# A Python 3 interface for data extraction from a cheap oscilloscope
I got myself a cheap, entry level oscilloscope (Hanmatek DOS1102 110 MHz, 1GSa/s max) for my hobby endeavors, and because it is a breeze to evaluate data with python, I decided to create this little project.
Feel free to share and contribute.

# Requirements
You will need to install a libusb (tested with libusb0 (v1.2.7.3)) distribution for Windows. 
I recommend Zadig, it works with Windows 11 and comes with the said driver.

Ito python, check out the environment.yaml file. Using ```conda env create -f environment.yaml``` should get you an environment that works with the code. I do recommend using spyder in addition for ease of use.
