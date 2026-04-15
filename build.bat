@echo off
echo Building WinAnchor with PyInstaller...

REM Run PyInstaller with the required flags
pyinstaller --clean --noconfirm --onefile --windowed --name "WinAnchor" ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import keyboard ^
    --hidden-import win32timezone ^
    run.py

echo Build complete! The standalone executable is located in the "dist" folder.