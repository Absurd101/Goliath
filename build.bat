@echo off
echo ==============================
echo  GOLIATH - Building exe...
echo ==============================

cd /d "C:\Users\cssko\Documents\TerrorZone Tracker"

echo Cleaning old build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del Goliath.spec 2>nul

echo Building new exe...
pyinstaller --onefile --windowed --icon=goliath.ico --name=Goliath goliath_gui.py

echo Copying new exe...
copy /y "dist\Goliath.exe" "Goliath.exe"

echo Updating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Goliath.lnk')); $s.TargetPath = 'C:\Users\cssko\Documents\TerrorZone Tracker\Goliath.exe'; $s.IconLocation = 'C:\Users\cssko\Documents\TerrorZone Tracker\goliath.ico'; $s.Save()"

echo ==============================
echo  Done! Goliath.exe is ready.
echo  Desktop shortcut updated.
echo ==============================
pause
