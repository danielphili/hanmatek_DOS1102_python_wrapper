# -*- coding: utf-8 -*-
"""
Use the pyUSB library (mamba install pyUSB) for controlling a Hanmatek DOS1102
Oscilloscope for automated measurements.

Created on Sat Dec  9 11:31:51 2023

@author: Daniel Alexander Philipps (github.com/danielphili)

License: GNU GPL v3
Please refer to the license copy distributed within this repository.
"""

### read data from a Hanmatek DOS1102 Oscilloscope 
### similar to OWON SDS1102

import usb.core
import usb.util

import json
import time

import numpy as np


class Oscilloscope():
    ## Hanmatek DOS1102 vendor and product id:
    idVendor_HANMATEK_DOS1102=0x5345
    idProduct_HANMATEK_DOS1102=0x1234
    ## addresses for the in-/output of the Hanmatek DOS1102:
    # Bulk OUT
    addr_OUT_HANMATEK_DOS1102 = 0x3
    # Bulk IN
    addr_IN_HANMATEK_DOS1102 = 0x81

    def __init__(self, idVendor : str = None, idProduct : str = None,
                 addr_OUT : int = None, addr_IN : int = None, verbose = False):
        self.verbose = verbose
        if idVendor is None:
            self.idVendor = self.idVendor_HANMATEK_DOS1102
        else:
            self.idProduct = idProduct
        if idProduct is None:
            self.idProduct = self.idProduct_HANMATEK_DOS1102
        else:
            self.idProduct = idProduct
            
        if addr_IN is None:
            self.addr_IN = self.addr_IN_HANMATEK_DOS1102
        else:
            self.addr_IN = addr_IN    
        if addr_OUT is None:
            self.addr_OUT = self.addr_OUT_HANMATEK_DOS1102
        else:
            self.addr_OUT = addr_OUT
        
        # attempt to find the oscilloscope
        self.dev = usb.core.find(idVendor=self.idVendor, 
                                 idProduct=self.idProduct)
        if self.dev is None:
            raise ValueError('Oscilloscope not found')
        else:
            if self.verbose:
                print('Success, device found.')
                print('Instrument ID: ', self.query_string_result('*IDN?'))
            self.meta_data = self.get_meta_data()

    def write(self, msg : str | list) -> None:
        '''
        send command to oscilloscope without reading information back

        Parameters
        ----------
        msg : str | list
            command.

        Returns
        -------
        None.

        '''
        self.query(msg)

    def query(self, msg : str | list) -> list:
        '''
        heart of the communication: perform query
        
        Parameters
        ----------
        msg : str | list
            message(s) to be transmitted to the oscilloscope.

        Returns
        -------
        list
            result as bytes.

        '''
        if type(msg) == type(list()):
            result = list()
            for msgk in msg:
                self.dev.write(self.addr_OUT,msgk)
                result.append(self.dev.read(self.addr_IN,100000,1000))
        else: 
            self.dev.write(self.addr_OUT,msg)            
            result = (self.dev.read(self.addr_IN,100000,1000))
        return result
    
    def query_and_show_response(self, msg:str) -> None:
        '''
        send a query to the oscilloscope and display the answer directly.
        Mostly for debugging purposes
    
        Parameters
        ----------
        msg : str
            query content.
    
        Returns
        -------
        None.
    
        '''
        result = self.query(msg)
        try:
            string = result.tobytes().decode('utf-8')
        except:
            res = [str(rk) for rk in result]
            string = ' '.join(res)
        print(string)
    
    def query_string_result(self, msg : str | list) -> str | list:
        '''
        perform a query where the output can be expected to be a string
    
        Parameters
        ----------
        msg : str | list (of str)
            DESCRIPTION.
    
        Returns
        -------
        result : str | list (of str)
            contains the response(s) decoded in strings.
    
        '''
        result = self.query(msg)
        if type(result) == type(list()):
            result = [resk.tobytes().decode('utf-8') for resk in result]
        else:
            result = result.tobytes().decode('utf-8')
        return result  
    
    def get_channel_waveform_data(self, ch:int) -> np.array:
        '''
        Queries the data recorded on channel ch and returns it in an np.array.
        The data is scaled to the voltage at the probe input.

        Parameters
        ----------
        ch : int
            channel number (1 or 2).

        Returns
        -------
        np.array
            data.

        '''
        self.get_meta_data()
        raw_data = self.query(f':DATA:WAVE:SCREEN:CH{ch}?')
        data = []
        # discard first 4 bytes (meta data)
        for idx in range(4,len(raw_data),2):
            # two bytes at a time 
            # -> one signed integer (little-endian byte order)
            adc_val = int().from_bytes([raw_data[idx], raw_data[idx+1]],
                                       'little', signed=True)
            # adc_val /= 4096
            data.append(adc_val)
        
        # offset and scaling
        offset = int(self.meta_data['CHANNEL'][ch-1]['OFFSET'])
        
        scale = self.get_scale(ch)
        
        # It seems that per division, there are 410 points
        # and 8.25 offset points per ADC value... highly confusing
        data = [scale * (dk - offset*8.25)/410 for dk in data]
            
        return np.array(data,dtype=np.float64)
    
    def get_channel_measurement_data(self, ch:int) -> dict:
        '''
        Queries all available measurements.
        All measurement types are actually activated but only displayed upon
        according configuration in the menu accessible through the "Measure"
        button.
        
        Parameters
        ----------
        ch : int
            Channel number. Possible values: 1, 2.
        
        Returns
        -------
        dict
            all measurements in dict format.
        
        '''
        meas_string = self.query_string_result(f':MEAS:CH{ch}?')
        meas_string = meas_string.replace('0\x02\x00\x00', '')
        return json.loads(meas_string)

    def get_meta_data(self) -> None:
        '''
        obtain info about, for example, time base, sample settings etc and
        save it to object property
    
        Returns
        -------
        meta_data : dict
            contains the meta data of the recording.
    
        '''
        meta_data = self.query(':DATA:WAVE:SCREen:HEAD?')
        meta_data = meta_data[4:].tobytes().decode('utf-8')
        
        self.meta_data = json.loads(meta_data)
        return self.meta_data
    
    def get_sample_rate(self) -> float:
        '''
        extract sample rate info from meta data. The sample rate is global
        across channels.
    
        Parameters
        ----------
    
        Returns
        -------
        float
            sample rate.
    
        '''
        sample_rate = self.meta_data['SAMPLE']['SAMPLERATE']
        sample_rate = sample_rate.replace('(','')
        sample_rate = sample_rate.replace(')','')
        
        possible_units = ['kS/s','MS/s','GS/s']
        ten_exp = [3,6,9]
        
        for k, unit in enumerate(possible_units):
            if unit in sample_rate:
                break;
        
        sample_rate = float(sample_rate.replace(unit,'')) * 10**ten_exp[k]
        return sample_rate

    def get_scale(self, ch) -> float:
        '''
        extract sample rate info from meta data
    
        Parameters
        ----------
    
        Returns
        -------
        float
            sample rate.
    
        '''
        scale = self.meta_data['CHANNEL'][ch-1]['SCALE']
        
        possible_units = ['mV','V', 'kV',
                          'mA', 'A', 'kA']
        ten_exp = [-3,0,3,
                   -3,0,3]
        
        for k, unit in enumerate(possible_units):
            if unit in scale:
                break;
        
        scale = float(scale.replace(unit,'')) * 10**ten_exp[k]
        probe_attenuation = \
            int(self.meta_data['CHANNEL'][ch-1]['PROBE'].replace('X',''))
        return scale*probe_attenuation

    def get_time_base(self) -> np.array:
        '''
        synthesize the time array of the current recording

        Returns
        -------
        time_array : TYPE
            DESCRIPTION.

        '''
        self.get_meta_data()
        nbr_points = self.meta_data['SAMPLE']['DATALEN']
        
        sample_rate = self.get_sample_rate()
        sample_time = 5/sample_rate
        
        offset = self.meta_data['TIMEBASE']['HOFFSET']
        time_offset = -1 * offset * 2 * sample_time
        
        time_array = [(k-nbr_points/2)*sample_time - time_offset
                      for k in range(nbr_points)]
        time_array = np.array(time_array)
        return time_array

    
if __name__ == '__main__':
    osci = Oscilloscope()
    osci.write(':RUNNING RUN')
    time.sleep(0.01)
    osci.write(':RUNNING STOP')    
    osci.get_meta_data()
    time = osci.get_time_base()
    data_ch1 = osci.get_channel_waveform_data(ch=1)

    # filter for nicer waveform (bandwidth loss assumed acceptable)
    from scipy.ndimage import gaussian_filter1d
    data_ch1 = gaussian_filter1d(data_ch1, sigma=1)    

    # plot
    import matplotlib.pyplot as plt
    time = time/1E-6
    plt.plot(time, data_ch1, marker='o', markersize=2.5, label='CH1')
    plt.grid(True)
    plt.legend()
    plt.xlim((min(time),max(time)))
    plt.xlabel('Time (µs)')
    plt.ylabel('Voltage (V)')
    plt.show()

    # save to disk
    import pandas as pd
    data_ch2 = gaussian_filter1d(osci.get_channel_waveform_data(ch=2), sigma=1) 
    time *= 1E-6
    data = np.array([time, data_ch1, data_ch2], dtype=np.float64).T
    df = pd.DataFrame(data)
    df.columns =  ['Time','CH1','CH2']
    df.to_csv('OsciData.csv', index=False)
    
    meta_data_string = json.dumps(osci.meta_data)
    measurement_data_ch1_string = \
        json.dumps(osci.get_channel_measurement_data(ch=1))
    measurement_data_ch2_string = \
        json.dumps(osci.get_channel_measurement_data(ch=2))
    
    meta_meas_data_string = (meta_data_string + measurement_data_ch1_string + \
        measurement_data_ch2_string).replace('}{', ',')
    
    with open("OsciData_MetaMeas.json",'w+') as file:
        file.write(meta_meas_data_string)
        file.close()
