HOME_DIR=/home/pi
RAM_DISK_PATH=$HOME_DIR/RamDisk

python3 $HOME_DIR/Heizung/Heizung/batterymonitor.py --privateKey  $HOME_DIR/MobileAlerts/TempLogger/pushsafer_key.dat --statusFilePath=$RAM_DISK_PATH/
