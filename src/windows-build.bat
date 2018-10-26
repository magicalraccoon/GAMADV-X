rmdir /q /s gamadv-x
rmdir /q /s gamadv-x-64
rmdir /q /s build
rmdir /q /s dist
del /q /f gamadv-x-%1-windows.zip
del /q /f gamadv-x-%1-windows-x64.zip
del /q /f gamadv-x-%1-windows-x64.msi
del /q /f *.wixobj
del /q /f *.wixpdb

set WIXVERSION=3.11

c:\python27-32\scripts\pyinstaller --clean -F --distpath=gamadv-x windows-gam.spec
xcopy LICENSE gamadv-x\
xcopy license.rtf gamadv-x\
xcopy gam-setup.bat gamadv-x\
xcopy Gam*.txt gamadv-x\
xcopy cacerts.pem gamadv-x\
del gamadv-x\w9xpopen.exe
"%ProgramFiles%\7-Zip\7z.exe" a -tzip gamadv-x-%1-windows.zip gamadv-x\ -xr!.svn

c:\python27-64\scripts\pyinstaller --clean -F --distpath=gamadv-x-64 windows-gam.spec
xcopy LICENSE gamadv-x-64\
xcopy license.rtf gamadv-x-64\
xcopy gam-setup.bat gamadv-x-64\
xcopy Gam*.txt gamadv-x-64\
xcopy cacerts.pem gamadv-x-64\
"%ProgramFiles%\7-Zip\7z.exe" a -tzip gamadv-x-%1-windows-x64.zip gamadv-x-64\ -xr!.svn

set GAMVERSION=%1
"%ProgramFiles(x86)%\WiX Toolset v%WIXVERSION%\bin\candle.exe" -arch x64 gam.wxs
"%ProgramFiles(x86)%\WiX Toolset v%WIXVERSION%\bin\light.exe" -ext "%ProgramFiles(x86)%\WiX Toolset v%WIXVERSION%\bin\WixUIExtension.dll" gam.wixobj -o gamadv-x-%1-windows-x64.msi
del /q /f gamadv-x-%1-windows-x64.wixpdb
