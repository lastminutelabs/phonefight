CERT=`sh ./build/define_certificate.sh`

./build/ensymble.py py2sis --icon images/icon.svg --caps=LocalServices --lang EN --extrasdir="root" --uid=0x20021BCD --version=1.0.0 --verbose $CERT --textfile="build/installtext.txt" --shortcaption "Phonefight" --vendor="lastminute.com labs" --drive=C --caption="Phonefight" --appname="Phonefight" python build/output/phonefight/phonefight.sis
./build/ensymble.py mergesis --verbose  $CERT build/output/phonefight/phonefight.sis build/PythonForS60_1_4_5_3rdEd.sis build/aXYZ_3rd_N95_1_0_2_selfsigned.sisx build/N95AccelerometerPlugin.sis build/lightblue-0.3.3-s60-3rdEd.sisx build/output/phonefight_bundle/phonefight_bundle.sisx
