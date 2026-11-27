@echo off
title WinDebloatX Standalone Compiler
echo Building standalone executable with PyInstaller...

pip install pyinstaller customtkinter rich pillow

pyinstaller --noconfirm --onedir --windowed --uac-admin ^
    --name "WinDebloatX" ^
    --collect-all customtkinter ^
    --hidden-import "rich" ^
    --hidden-import "PIL" ^
    main.py

echo.
echo Build finished! Portable binary located in dist\WinDebloatX\WinDebloatX.exe
pause
