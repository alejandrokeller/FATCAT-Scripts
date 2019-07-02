# FATCAT Control, Monitor & Visualization System (local)
## Collection of scripts for controlling FATCAT from a RASPI (python and unix shell)
*Application developed in **Python** to work (optional) in conjunction with an **HTTP Database** and a **serial** controlled device.*

### **Installation**
1. Clone repository:
```bash
$ git clone https://github.com/alejandrokeller/FATCAT-scripts
```
2. Travel to cloned folder:
```bash
$ cd FATCAT-scripts
```
3. Open config.ini and check **[configuration file](#configuration-file)**.
4. Create required data and logs directories:
```bash
$ sudo mkdir data data/events data/events/graph logs data/baseline
```
5. Install python requirements:
```bash
$ pip install -r extras/requirements.txt
```
6. Install PySide (for python3 use the `python3-pyside` meta package):
```bash
$ sudo apt-get install python-pyside
```

## Enabling USB/Serial Port Permissions on Linux (not needed for the Raspberry Pi)

Note: Linux distributions other than Ubuntu may run into issues with the following instructions: 

1. Add yourself to the "dialout" group:
```
sudo usermod -a -G dialout $USER
```
2. Create a rule file to automatically enable permissions when Palette™/P+™ is connected:
```
sudo nano /etc/udev/rules.d/50-local.rules
```
3. Paste this line in the file you just created:
```
ACTION=="add", ATTRS{idProduct}=="0042", ATTRS{idVendor}=="2341", DRIVERS=="usb", RUN+="chmod a+rw /dev/ttyACM0"
```
4. Press `Control-O` and then `Control-X` to save the file and exit.

Note: you may need to log out and log back in (or reboot your computer) for the changes to take effect.
