# -*- coding: utf-8 -*-

# převzato z Davidova kódu
# Proggrammer's Guide: https://www.picotech.com/download/manuals/picoscope-2000-series-a-api-programmers-guide.pdf

import ctypes
import numpy as np
from picosdk.ps2000a import ps2000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
from picosdk.constants import PICO_STATUS_LOOKUP
from time import time as time_time
from time import sleep as time_sleep


def set_up_oscilloscope():
    ENABLED = 1
    DISABLED = 0
    ANALOGUE_OFFSET = 0.0

    # Create c_handle and status ready for use
    global c_handle
    c_handle = ctypes.c_int16()
    global status
    status = {}

    # Channel ranges
    global CH_A_RANGE
    CH_A_RANGE = ps.PS2000A_RANGE['PS2000A_5V']
    global CH_B_RANGE
    CH_B_RANGE = ps.PS2000A_RANGE['PS2000A_5V']

    # Select timebase (see Programmer's Guide)
    global TIMEBASE   
    TIMEBASE = 8

    # Set number of pre and post trigger samples to be collected 
    global PRE_TRIGGER_SAMPLES
    PRE_TRIGGER_SAMPLES = 50
    global POST_TRIGGER_SAMPLES
    POST_TRIGGER_SAMPLES = 2500
    global TOTAL_SAMPLES
    TOTAL_SAMPLES = PRE_TRIGGER_SAMPLES + POST_TRIGGER_SAMPLES


    

    # Open 2000 series PicoScope
    # Returns handle to c_handle for use in future API functions
    status['open_unit'] = ps.ps2000aOpenUnit(ctypes.byref(c_handle), None)
    assert_pico_ok(status['open_unit'])

    # Set up channel A
    status['set_ch_a'] = ps.ps2000aSetChannel(
        c_handle,                                   # handle = c_handle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],    # channel = PS2000A_CHANNEL_A = 0
        ENABLED,                                    # enabled = 1
        ps.PS2000A_COUPLING['PS2000A_DC'],          # coupling type = PS2000A_DC = 1
        CH_A_RANGE,                                 # range = PS2000A_5V = 8
        ANALOGUE_OFFSET)                            # analogue offset = 0.0 V
    assert_pico_ok(status['set_ch_a'])

    # Set up channel B
    status['set_ch_b'] = ps.ps2000aSetChannel(
        c_handle,                                   # handle = c_handle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],    # channel = PS2000A_CHANNEL_B = 1
        ENABLED,                                    # enabled = 1
        ps.PS2000A_COUPLING['PS2000A_DC'],          # coupling type = PS2000A_DC = 1
        CH_B_RANGE,                                 # range = PS2000A_5V = 8
        ANALOGUE_OFFSET)                            # analogue offset = 0.0 V
    assert_pico_ok(status['set_ch_b'])

    # Set up single trigger
    max_adc = ctypes.c_int16()
    status['maximum_value'] = ps.ps2000aMaximumValue(c_handle, ctypes.byref(max_adc))

    v_range = 5
    v_trigger = 1
    adc_trigger_treshold = int((v_trigger / v_range) * max_adc.value) # 6502 in adc counts
    #print(max_adc.value, adc_trigger_treshold) # 32512 6502
    status['trigger'] = ps.ps2000aSetSimpleTrigger(
        c_handle,                                   # handle = c_handle
        ENABLED,                                    # enabled = 1
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],    # source = PS2000A_CHANNEL_A = 0 
        adc_trigger_treshold,                       # threshold = 1V # excact adc counts unknown
        2, #ps.PS2000A_THRESHOLD_DIRECTION['RISING'],   # direction = PS2000A_RISING = 2
        0,                                          # delay = 0 s # delay, the time between the trigger occurring and the first sample being taken.
        0)                                          # auto Trigger = 0 # wait indefinitely for a trigger
    assert_pico_ok(status['trigger'])


    # Get TIMEBASE information
    '''
    Note: p. 44
    time_interval_ns -> a pointer to the time interval between readings at the selected TIMEBASE
    segment index == the index of the memory segment to use
    '''
    global time_interval_ns
    time_interval_ns = ctypes.c_float()
    returned_max_samples = ctypes.c_int32()
    global oversample
    oversample = ctypes.c_int16(0)
    status['get_TIMEBASE_2'] =ps.ps2000aGetTimebase2(
        c_handle,                           # handle = c_handle
        TIMEBASE,                           # TIMEBASE = 8 = TIMEBASE
        TOTAL_SAMPLES,                      # noSamples = TOTAL_SAMPLES
        ctypes.byref(time_interval_ns),     # pointer to timeIntervalNanoseconds = ctypes.byref(time_interval_ns)
        oversample,                         # Programmer's Guide says: "oversample, not used"
        ctypes.byref(returned_max_samples), # pointer to TOTAL_SAMPLES = ctypes.byref(returnedMaxSamples)
        0                                   # segment index = 0
    )
    assert_pico_ok(status['get_TIMEBASE_2'])

    return status, c_handle, TIMEBASE, time_interval_ns, oversample 

def capture_waveform():
    global status, c_handle, TOTAL_SAMPLES, TIMEBASE, time_interval_ns, oversample

    # Run block capture
    status['run_block'] = ps.ps2000aRunBlock(
        c_handle,               # handle = c_handle
        PRE_TRIGGER_SAMPLES,    # number of pre-trigger samples = PRE_TRIGGER_SAMPLES
        POST_TRIGGER_SAMPLES,   # number of post-trigger samples = POST_TRIGGER_SAMPLES
        TIMEBASE,               # TIMEBASE = 8 = 80 ns = TIMEBASE (see Programmer's guide for mre information on TIMEBASEs)
        oversample,             # not used
        None,                   # time indisposed ms = None
        0,                      # segment index = 0
        None,                   # lpReady = None (using ps2000aIsReady rather than ps2000aBlockReady)
        None)                   # pParameter = None
    assert_pico_ok(status['run_block'])

    # Check for data collection to finish using ps2000aIsReady
    ready = ctypes.c_int16(0)
    check = ctypes.c_int16(0)
    while ready.value == check.value:
        status['is_ready'] = ps.ps2000aIsReady(c_handle, ctypes.byref(ready))
    
    # Create buffers ready for assigning pointers for data collection
    buffer_a_max = (ctypes.c_int16 * TOTAL_SAMPLES)()
    buffer_a_min = (ctypes.c_int16 * TOTAL_SAMPLES)() # used for downsampling
    buffer_b_max = (ctypes.c_int16 * TOTAL_SAMPLES)()
    buffer_b_min = (ctypes.c_int16 * TOTAL_SAMPLES)() # used for downsampling
    
    # Set data buffer location for data collection from channel A
    status['set_data_buffers_a'] = ps.ps2000aSetDataBuffers(
        c_handle,                                           # handle = c_handle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],            # source = PS2000A_CHANNEL_A = 0
        ctypes.byref(buffer_a_max),                         # pointer to buffer max = ctypes.byref(bufferDPort0Max???)
        ctypes.byref(buffer_a_min),                         # pointer to buffer min = ctypes.byref(bufferDPort0Min???)
        TOTAL_SAMPLES,                                      # buffer length = TOTAL_SAMPLES
        0,                                                  # segment index = 0
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'])   # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    assert_pico_ok(status['set_data_buffers_a'])

    
    # Set data buffer location for data collection from channel B
    status['set_data_buffers_b'] = ps.ps2000aSetDataBuffers(
        c_handle,                                           # handle = c_handle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],            # source = PS2000A_CHANNEL_B = 1
        ctypes.byref(buffer_b_max),                         # pointer to buffer max = ctypes.byref(bufferBMax)
        ctypes.byref(buffer_b_min),                         # pointer to buffer min = ctypes.byref(bufferBMin)
        TOTAL_SAMPLES,                                      # segment index = 0
        0,                                                  # buffer length = totalSamples
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE']    # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    )
    assert_pico_ok(status['set_data_buffers_b'])

    # Create overflow location
    overflow = ctypes.c_int16()
    # create converted type totalSamples
    c_TOTAL_SAMPLES = ctypes.c_int32(TOTAL_SAMPLES)

    # Retried data from scope to buffers assigned above
    status['get_values'] = ps.ps2000aGetValues(
        c_handle,                                           # handle = c_handle
        0,                                                  # start index = 0
        ctypes.byref(c_TOTAL_SAMPLES),                      # pointer to number of samples = ctypes.byref(c_TOTAL_SAMPLES)
        0,                                                  # downsample ratio = 0
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],   # downsample ratio mode = PS2000A_RATIO_MODE_NONE
        0,                                                  # segment index = 0
        ctypes.byref(overflow))                             # pointer to overflow = ctypes.byref(overflow))
    assert_pico_ok(status['get_values'])

    # find maximum ADC count value
    max_adc = ctypes.c_int16()
    status["maximum_value"] = ps.ps2000aMaximumValue(
        c_handle,               # handle = c_handle
        ctypes.byref(max_adc))  # pointer to value = ctypes.byref(max_adc)
    assert_pico_ok(status["maximum_value"])
    
    # convert ADC counts data to mV
    adc_2_mV_ch_a =  adc2mV(buffer_a_max, CH_A_RANGE, max_adc)
    adc_2_mV_ch_b =  adc2mV(buffer_b_max, CH_B_RANGE, max_adc)

    # Create time data
    time = np.linspace(
        start = 0,
        stop = c_TOTAL_SAMPLES.value * time_interval_ns.value,
        num = c_TOTAL_SAMPLES.value)

    # display status returns
    #print(status)
    #for key in status:
    #    print(key, PICO_STATUS_LOOKUP[status[key]])
    
    time = np.array(time)
    voltage_a = np.array(adc_2_mV_ch_a)
    voltage_b = np.array(adc_2_mV_ch_b)

    return time, voltage_a, voltage_b

def close_oscilloscope():
    global c_handle, status
    # Stop the scope
    status['stop'] = ps.ps2000aStop(c_handle) # handle = c_handle
    assert_pico_ok(status['stop'])

    # Close unit & Disconnect the scope
    status['close'] = ps.ps2000aCloseUnit(c_handle) # handle = c_handle
    assert_pico_ok(status['close'])



if(__name__ == '__main__'):
    from sys import exit
    import serial

    OFFSET = 10 # in counts; offset from first pulse for finding the second one
    ONE_VOLT = 1000 # in mV
    counter = 0

    # open serial port
    ser = serial.Serial(port = '/dev/ttyUSB0', baudrate = 115200, timeout = 5.0)
    print('Serial line to ESP32 is open {}'.format(ser.is_open))

    set_up_oscilloscope()
    print('Oscilloscope set up!')

    try:
        while True:
            time, voltage_a, voltage_b = capture_waveform()
            #print(counter)
            
            voltage_len = len(voltage_a) # should equal TOTAL_SAMPLES

            # find first pulse
            for i in range(voltage_len):
                if(voltage_a[i] > ONE_VOLT):
                    first_pulse_time = round(time[i])
                    
                    
                    # find second pulse after the first one + OFFSET
                    for j in range(i + OFFSET, voltage_len):
                        if(voltage_a[j] > ONE_VOLT):
                            second_pulse_time = round(time[j])
                            decay_time = round((second_pulse_time - first_pulse_time) / 1000) # in μs
                            #print('First pulse found at time {} ns.'.format(first_pulse_time))
                            #print('Second pulse found at time {} ns.'.format(second_pulse_time))
                            #print('Decay time is {} μs.'.format(decay_time))

                            # find ESP32 response after the second pulse
                            for k in range(j, voltage_len):
                                if voltage_b[k] > ONE_VOLT:
                                    esp32_response_time = round(time[k])
                                    #print('ESP32 has responded at time {} ns.'.format(esp32_response_time))
                                    
                                    epoch_time = int(time_time())
                                    
                                    time_sleep(3) # <---------------------------------------------------------------------------------------------------------------wait for esp32
                                    ser_size = ser.inWaiting() 
                                    if ser.inWaiting() > 0:
                                        esp32_decay_time = ser.read(ser_size)
                                        try:
                                            esp32_decay_time = esp32_decay_time.decode('utf-8')
                                            #esp32_decay_time = esp32_decay_time.strp('\r\n' )
                                            esp32_decay_time = round(int(esp32_decay_time) / 240) # convert to μs
                                        except Exception:
                                            print('Unable to convert to int: {}'.format(esp32_decay_time))
                                            esp32_decay_time = 0
                                    else:
                                        esp32_decay_time = 'none'

                                    if abs(esp32_decay_time - decay_time) < 5:
                                        test_path = 'pass'
                                    else:
                                        test_path = 'fail'
                                    
                                    print('Pass; Response from ESP32 is: {} μs, mesured decay time is: {} μs, so delta is {} % of measured decay time.'.format(esp32_decay_time, decay_time, round((abs(esp32_decay_time - decay_time))/(decay_time) * 100)))

                                    # plot & save graph
                                    plt.plot(time, voltage_a)
                                    plt.plot(time, voltage_b)
                                    plt.xlabel('Time (μs)')
                                    plt.ylabel('Voltage (mV)')

                                    xmin, xmax, ymin, ymax = plt.axis()
                                    plt.text(round(0.4 * xmax, 0), round(0.90 * ymax, 0), 'Epoch time: ' + str(epoch_time), fontsize=10)
                                    plt.text(round(0.4 * xmax, 0), round(0.80 * ymax, 0), 'ESP32 decay time: ' + str(esp32_decay_time) + 'us', fontsize=10)
                                    plt.text(round(0.4 * xmax, 0), round(0.70 * ymax, 0), 'Decay time: ' + str(decay_time) + 'us', fontsize=10)

                                    plt.savefig('pulses/pulses_with_response/' + test_path + '/waveform' + str(epoch_time) + '.svg', format = 'svg')
                                    plt.close()
                                    plt.figure().clear()
                                    
                                    counter += 1
                                    break
                            
                            else:
                                esp32_response_time = round(time[k])
                                if(4 < decay_time < 100): # ESP32 cannot hadndle events this fast or slow
                                    print('ESP32 has NOT responded, measured decay time is: {} μs.'.format(decay_time))
                                    epoch_time = int(time_time())
                                    # plot & save graph
                                    plt.plot(time, voltage_a)
                                    plt.plot(time, voltage_b)

                                    xmin, xmax, ymin, ymax = plt.axis()
                                    plt.text(round(0.4 * xmax, 0), round(0.80 * ymax, 0), 'Epoch time: ' + str(epoch_time), fontsize=10)
                                    plt.text(round(0.4 * xmax, 0), round(0.70 * ymax, 0), 'Decay time: ' + str(decay_time) + 'us', fontsize=10)

                                    plt.xlabel('Time (μs)')
                                    plt.ylabel('Voltage (mV)')
                                    plt.savefig('pulses/pulses_without_response/waveform' + str(epoch_time) + '.svg', format = 'svg')
                                    plt.close()
                                    plt.figure().clear()
                                    counter += 1

                        else:
                            continue
                        break
                    
                    break # no need for finding the first pulse multiple times

    except Exception as exception:
        print(exception)
        print('\nClosing oscilloscope!')
        close_oscilloscope()        
        exit(0)