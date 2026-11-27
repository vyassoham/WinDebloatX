@echo off
title WinDebloatX Standalone Compiler
echo Building standalone executable with PyInstaller...

pip install pyinstaller customtkinter rich pillow darkdetect psutil pytest

pyinstaller --noconfirm --onedir --windowed --uac-admin ^
    --name "WinDebloatX" ^
    --icon "assets\icon.ico" ^
    --add-data "locales;locales" ^
    --add-data "assets;assets" ^
    --collect-all customtkinter ^
    --hidden-import "rich" ^
    --hidden-import "PIL" ^
    --hidden-import "psutil" ^
    main.py

echo.
echo Build finished! Portable binary located in dist\WinDebloatX\WinDebloatX.exe
pause
