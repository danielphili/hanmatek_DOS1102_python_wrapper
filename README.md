# A Python 3 interface for data extraction from a cheap oscilloscope
I got myself a cheap, entry level oscilloscope (Hanmatek DOS1102 110 MHz, 1GSa/s max) for my hobby endeavors, and because it is a breeze to evaluate data with python, I decided to create this little project.
Feel free to share and contribute.

# Requirements
You will need to install a libusb (tested with libusb0 (v1.2.7.3)) distribution for Windows. 
I recommend Zadig, it works with Windows 11 and comes with the said driver.
You do NOT need a VISA or similar software. This interface just uses pyUSB to directly communicate with the oscilloscope

Ito python, check out the environment.yaml file. Using ```conda env create -f environment.yaml``` should get you an environment that works with the code. I do recommend using spyder in addition for ease of use.

# Additional resouces
A list of SCPI commands that can be used with the very similar OWON SDS1102 oscilloscope can be found here:
<http://files.owon.com.cn/software/Application/SDS_Series_Oscilloscopes_SCPI_Protocol.pdf>
For trying them out, you can use the function ```query_and_show_response``` and you will immmediately get a feedback whether there was any data sent back from your oscilloscope.
