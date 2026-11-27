"""
WinDebloatX - Registry Backup and Rollback Manager
Provides listing, validation, and 1-click restoration of registry state backups.
"""

import os
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning
from core.registry import BACKUP_DIR, restart_explorer

def list_backups() -> List[Dict[str, any]]:
    """
    Returns a sorted list of available registry backups with metadata.
    """
    if not os.path.isdir(BACKUP_DIR):
        return []

    backups = []
    for fname in os.listdir(BACKUP_DIR):
        if fname.endswith(".reg"):
            fpath = os.path.join(BACKUP_DIR, fname)
            stat = os.stat(fpath)
            backups.append({
                "filename": fname,
                "filepath": fpath,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "mtime": stat.st_mtime
            })

    # Sort descending (newest first)
    backups.sort(key=lambda x: x["mtime"], reverse=True)
    return backups

def restore_backup(backup_path: str, auto_restart_explorer: bool = True) -> Tuple[bool, str]:
    """
    Restores a .reg backup file using reg.exe import.
    """
    if not os.path.isfile(backup_path):
        msg = f"Backup file not found: {backup_path}"
        log_error(msg)
        return False, msg

    log_info(f"Restoring registry backup from {backup_path}...")
    cmd = f'reg.exe import "{backup_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            if auto_restart_explorer:
                restart_explorer()
            msg = f"Successfully restored backup: {os.path.basename(backup_path)}"
            log_success(msg)
            return True, msg
        else:
            msg = f"Failed to restore backup: {res.stderr.strip() or res.stdout.strip()}"
            log_error(msg)
            return False, msg
    except Exception as e:
        msg = f"Exception during backup restoration: {e}"
        log_error(msg)
        return False, msg

def delete_backup(backup_path: str) -> bool:
    """Deletes a specific backup file."""
    try:
        if os.path.isfile(backup_path):
            os.remove(backup_path)
            log_info(f"Deleted backup file: {os.path.basename(backup_path)}")
            return True
        return False
    except Exception as e:
        log_error(f"Failed to delete backup file: {e}")
        return False

def clean_old_backups(keep_count: int = 20) -> int:
    """Retains the most recent N backups and cleans older files."""
    backups = list_backups()
    if len(backups) <= keep_count:
        return 0

    to_delete = backups[keep_count:]
    deleted = 0
    for b in to_delete:
        if delete_backup(b["filepath"]):
            deleted += 1
    return deleted
