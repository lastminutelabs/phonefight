./ensymble.py py2sis --icon ../images/icon.svg --lang EN --verbose --shortcaption "Phonefight" --caption "Phonefight" --appname Phonefight ../python/fight.py $phonefight_script_only.sis
./ensymble.py mergesis --verbose $phonefight_script_only.sis PythonForS60_1_4_5_3rdEd.sis aXYZ_3rd_N95_1_0_2_selfsigned.sisx N95AccelerometerPlugin.sis phonefight.sis
