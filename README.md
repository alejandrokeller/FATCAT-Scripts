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
3. Open config.ini and check **[configuration file](#configuration-file)**. You can set here the destination directories for the output files.
4. Create required data and logs directories:
```bash
$ sudo mkdir  ~/fatcat-files/ ~/fatcat-files/data ~/fatcat-files/data/events ~/fatcat-files/data/events/graph ~/fatcat-files/logs ~/fatcat-files/data/baseline
```
5. Install python requirements:
```bash
$ pip install -r extras/requirements.txt
```
6. Install PySide (for python3 use the `python3-pyside` meta package):
```bash
$ sudo apt-get install python-pyside
```
