@echo off
echo Menginstal PyInstaller...
pip install pyinstaller
echo Membangun file .exe...
pyinstaller -y --noconsole --name Milipah --icon "assets\setup_icon.ico" --add-data "assets;assets" main.py
echo Selesai! File exe Anda berada di dalam folder "dist\Milipah".
pause
