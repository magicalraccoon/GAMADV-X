rm -rf gam
rm -rf build
rm -rf dist
rm -f gamadv-x-$1-macos.tar

pyinstaller2.7 --clean -F --distpath=gam macos-gam.spec
cp LICENSE gam
cp license.rtf gam
cp whatsnew.txt gam
cp Gam*.txt gam

tar -cf gamadv-x-$1-macos.tar gam/ 
