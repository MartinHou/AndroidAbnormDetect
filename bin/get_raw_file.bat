adb shell COLUMNS=512 "top -d 1 -H -n %1|grep %2" >%3