import unittest
import winreg
from core.privacy import PRIVACY_TWEAKS, get_tweak_status, get_windows_edition_info
from core.win11_tweaks import WIN11_TWEAKS
from core.appx_remover import BLOATWARE_CATALOG, SYSTEM_WHITELIST, reinstall_app_from_store
from core.services import BLOAT_SERVICES, get_service_status
from core.presets import PRESETS
from core.registry import parse_key_path
from core.backup_manager import list_backups
from core.restore_point import check_restore_prerequisites
from core.onedrive import check_onedrive_files_on_demand
from core.gaming import get_mmcss_status
from core.persistence import is_persistence_task_installed
from core.hardware import get_hardware_profile, is_laptop
from core.winget_installer import SOFTWARE_CATALOG, is_winget_available
from core.i18n import t, set_language, SUPPORTED_LANGUAGES

class TestWinDebloatXCore(unittest.TestCase):
    def test_registry_parse_key_path(self):
        root, sub = parse_key_path("HKLM\\SOFTWARE\\Policies\\Test")
        self.assertEqual(root, winreg.HKEY_LOCAL_MACHINE)
        self.assertEqual(sub, "SOFTWARE\\Policies\\Test")

        root_cu, sub_cu = parse_key_path("HKCU\\Software\\Microsoft")
        self.assertEqual(root_cu, winreg.HKEY_CURRENT_USER)
        self.assertEqual(sub_cu, "Software\\Microsoft")

    def test_presets_structure(self):
        required_presets = ["essential", "gaming", "privacy", "full"]
        for p in required_presets:
            self.assertIn(p, PRESETS)
            self.assertIn("name", PRESETS[p])
            self.assertIn("description", PRESETS[p])

    def test_appx_catalog_safety(self):
        for protected in SYSTEM_WHITELIST:
            self.assertNotIn(protected, BLOATWARE_CATALOG)

    def test_appx_store_ids(self):
        for pkg_id, info in BLOATWARE_CATALOG.items():
            self.assertIn("store_id", info)

    def test_privacy_tweaks_structure(self):
        self.assertGreater(len(PRIVACY_TWEAKS), 5)
        for key, tweak in PRIVACY_TWEAKS.items():
            self.assertIn("title", tweak)
            self.assertIn("entries", tweak)
            self.assertIsInstance(tweak["entries"], list)

    def test_win11_tweaks_structure(self):
        self.assertIn("classic_context_menu", WIN11_TWEAKS)
        self.assertIn("disable_copilot", WIN11_TWEAKS)
        self.assertIn("disable_recall", WIN11_TWEAKS)
        self.assertIn("disable_widgets", WIN11_TWEAKS)
        self.assertIn("disable_edge_bloat", WIN11_TWEAKS)

    def test_backup_manager(self):
        backups = list_backups()
        self.assertIsInstance(backups, list)

    def test_restore_prerequisites(self):
        ok, msg = check_restore_prerequisites()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

    def test_onedrive_scan(self):
        has_cloud_files, count, msg = check_onedrive_files_on_demand()
        self.assertIsInstance(has_cloud_files, bool)
        self.assertIsInstance(count, int)
        self.assertIsInstance(msg, str)

    def test_mmcss_status(self):
        status = get_mmcss_status()
        self.assertIn("network_throttling_index", status)
        self.assertIn("system_responsiveness", status)
        self.assertIn("is_optimized", status)

    def test_windows_edition_detection(self):
        info = get_windows_edition_info()
        self.assertIn("edition_id", info)
        self.assertIn("level_0_supported", info)
        self.assertIn("note", info)

    def test_persistence_task_check(self):
        installed = is_persistence_task_installed()
        self.assertIsInstance(installed, bool)

    def test_hardware_intelligence(self):
        hw = get_hardware_profile()
        self.assertIn("is_laptop", hw)
        self.assertIn("form_factor", hw)
        self.assertIn("total_ram_gb", hw)
        self.assertIn("storage_type", hw)
        self.assertIsInstance(hw["recommendations"], list)
        self.assertGreater(len(hw["recommendations"]), 0)

    def test_winget_software_catalog(self):
        self.assertGreater(len(SOFTWARE_CATALOG), 10)
        for pkg_id, info in SOFTWARE_CATALOG.items():
            self.assertIn("name", info)
            self.assertIn("category", info)
            self.assertIn("description", info)

    def test_i18n_localization(self):
        set_language("en")
        self.assertEqual(t("ready"), "Ready")
        set_language("es")
        self.assertEqual(t("ready"), "Listo")
        set_language("de")
        self.assertEqual(t("ready"), "Bereit")
        set_language("zh")
        self.assertEqual(t("ready"), "准备就绪")
        set_language("en")

if __name__ == "__main__":
    unittest.main()
