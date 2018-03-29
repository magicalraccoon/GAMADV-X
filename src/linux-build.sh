rm -rf gamadv-x
rm -rf build
rm -rf dist
rm -rf gamadv-x-$1-linux-$(arch).tar.xz

export LD_LIBRARY_PATH=/usr/local/lib
pyinstaller --clean -F --distpath=gamadv-x linux-gam.spec
cp LICENSE gamadv-x
cp license.rtf gamadv-x
cp whatsnew.txt gamadv-x
cp Gam*.txt gamadv-x
cp cacerts.pem gamadv-x

tar cfJ gamadv-x-$1-linux-$(arch).tar.xz gamadv-x/ 
