# -*- coding: utf-8 -*-

# převzato z Davidova kódu
# Proggrammer's Guide: https://www.picotech.com/download/manuals/picoscope-2000-series-a-api-programmers-guide.pdf

import ctypes
import numpy as np
from picosdk.ps2000a import ps2000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
from picosdk.constants import PICO_STATUS_LOOKUP

def capture_waveform():

    # Create chandle and status ready for use
    chandle = ctypes.c_int16()
    status = {}

    # Open 2000 series PicoScope
    # Returns handle to chandle for use in future API functions
    status['open_unit'] = ps.ps2000aOpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status['open_unit'])

    ENABLED = 1
    DISABLED = 0
    ANALOGUE_OFFSET = 0.0

    # Set up channel A
    ch_a_range = ps.PS2000A_RANGE['PS2000A_5V']
    status['set_ch_a'] = ps.ps2000aSetChannel(
        chandle,                                   # handle = chandle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],    # channel = PS2000A_CHANNEL_A = 0
        ENABLED,                                    # enabled = 1
        ps.PS2000A_COUPLING['PS2000A_DC'],          # coupling type = PS2000A_DC = 1
        ch_a_range,                                 # range = PS2000A_5V = 8
        ANALOGUE_OFFSET)                            # analogue offset = 0.0 V
    assert_pico_ok(status['set_ch_a'])

    # Set up channel B
    ch_b_range = 8
    status['set_ch_b'] = ps.ps2000aSetChannel(
        chandle,                                   # handle = chandle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],    # channel = PS2000A_CHANNEL_B = 1
        ENABLED,                                    # enabled = 1
        ps.PS2000A_COUPLING['PS2000A_DC'],          # coupling type = PS2000A_DC = 1
        ch_b_range,                                 # range = PS2000A_5V = 8
        ANALOGUE_OFFSET)                            # analogue offset = 0.0 V
    assert_pico_ok(status['set_ch_b'])

    # Set up single trigger
    max_adc = ctypes.c_int16()
    status['maximum_value'] = ps.ps2000aMaximumValue(chandle, ctypes.byref(max_adc))

    v_range = 5
    v_trigger = 1
    adc_trigger_treshold = int((v_trigger / v_range) * max_adc.value) # 6502 in adc counts
    #print(max_adc.value, adc_trigger_treshold) # 32512 6502
    status['trigger'] = ps.ps2000aSetSimpleTrigger(
        chandle,                                   # handle = chandle
        ENABLED,                                    # enabled = 1
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],    # source = PS2000A_CHANNEL_B = 1 
        adc_trigger_treshold,                       # threshold = 1V # excact adc counts unknown
        2, #ps.PS2000A_THRESHOLD_DIRECTION['RISING'],   # direction = PS2000A_RISING = 2
        0,                                          # delay = 0 s # delay, the time between the trigger occurring and the first sample being taken.
        0)                                          # auto Trigger = 0 # wait indefinitely for a trigger
    assert_pico_ok(status['trigger'])

    # Set number of pre and post trigger samples to be collected <-----------------------------------------------------------------------------------------------------------------------
    pre_trigger_samples = 2500
    post_trigger_samples = 50
    total_samples = pre_trigger_samples + post_trigger_samples

    # Get timebase information
    '''
    Note: p. 44
    time_interval_ns -> a pointer to the time interval between readings at the selected timebase
    segment index == the index of the memory segment to use
    '''   
    timebase = 8 # <--------------------------------------------https://www.picotech.com/download/manuals/picoscope-2000-series-a-api-programmers-guide.pdf
    time_interval_ns = ctypes.c_float()
    returned_max_samples = ctypes.c_int32()
    oversample = ctypes.c_int16(0)
    status['get_timebase_2'] =ps.ps2000aGetTimebase2(
        chandle,                           # handle = chandle
        timebase,                           # timebase = 8 = timebase
        total_samples,                      # noSamples = total_samples
        ctypes.byref(time_interval_ns),     # pointer to timeIntervalNanoseconds = ctypes.byref(time_interval_ns)
        oversample,                         # Programmer's Guide says: "oversample, not used"
        ctypes.byref(returned_max_samples), # pointer to total_samples = ctypes.byref(returnedMaxSamples)
        0                                   # segment index = 0
    )
    assert_pico_ok(status['get_timebase_2'])

    # Run block capture
    status['run_block'] = ps.ps2000aRunBlock(
        chandle,               # handle = chandle
        pre_trigger_samples,    # number of pre-trigger samples = pre_trigger_samples
        post_trigger_samples,   # number of post-trigger samples = post_trigger_samples
        timebase,               # timebase = 8 = 80 ns = timebase (see Programmer's guide for mre information on timebases)
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
        status['is_ready'] = ps.ps2000aIsReady(chandle, ctypes.byref(ready))
    
    # Create buffers ready for assigning pointers for data collection
    buffer_a_max = (ctypes.c_int16 * total_samples)()
    buffer_a_min = (ctypes.c_int16 * total_samples)() # used for downsampling
    buffer_b_max = (ctypes.c_int16 * total_samples)()
    buffer_b_min = (ctypes.c_int16 * total_samples)() # used for downsampling
    
    # Set data buffer location for data collection from channel A
    status['set_data_buffers_a'] = ps.ps2000aSetDataBuffers(
        chandle,                                           # handle = chandle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],            # source = PS2000A_CHANNEL_A = 0
        ctypes.byref(buffer_a_max),                         # pointer to buffer max = ctypes.byref(bufferDPort0Max???)
        ctypes.byref(buffer_a_min),                         # pointer to buffer min = ctypes.byref(bufferDPort0Min???)
        total_samples,                                      # buffer length = total_samples
        0,                                                  # segment index = 0
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'])   # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    assert_pico_ok(status['set_data_buffers_a'])

    
    # Set data buffer location for data collection from channel B
    status['set_data_buffers_b'] = ps.ps2000aSetDataBuffers(
        chandle,                                           # handle = chandle
        ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],            # source = PS2000A_CHANNEL_B = 1
        ctypes.byref(buffer_b_max),                         # pointer to buffer max = ctypes.byref(bufferBMax)
        ctypes.byref(buffer_b_min),                         # pointer to buffer min = ctypes.byref(bufferBMin)
        total_samples,                                      # segment index = 0
        0,                                                  # buffer length = totalSamples
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE']    # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    )
    assert_pico_ok(status['set_data_buffers_b'])

    # Create overflow location
    overflow = ctypes.c_int16()
    # create converted type totalSamples
    c_total_samples = ctypes.c_int32(total_samples)

    # Retried data from scope to buffers assigned above
    status['get_values'] = ps.ps2000aGetValues(
        chandle,                                           # handle = chandle
        0,                                                  # start index = 0
        ctypes.byref(c_total_samples),                      # pointer to number of samples = ctypes.byref(c_total_samples)
        0,                                                  # downsample ratio = 0
        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],   # downsample ratio mode = PS2000A_RATIO_MODE_NONE
        0,                                                  # segment index = 0
        ctypes.byref(overflow))                             # pointer to overflow = ctypes.byref(overflow))
    assert_pico_ok(status['get_values'])

    # find maximum ADC count value
    max_adc = ctypes.c_int16()
    status["maximum_value"] = ps.ps2000aMaximumValue(
        chandle,               # handle = chandle
        ctypes.byref(max_adc))  # pointer to value = ctypes.byref(max_adc)
    assert_pico_ok(status["maximum_value"])
    
    # convert ADC counts data to mV
    adc_2_mV_ch_a =  adc2mV(buffer_a_max, ch_a_range, max_adc)
    adc_2_mV_ch_b =  adc2mV(buffer_b_max, ch_b_range, max_adc)

    # Create time data
    time = np.linspace(
        start = 0,
        stop = c_total_samples.value * time_interval_ns.value,
        num = c_total_samples.value)

    # Stop the scope
    status['stop'] = ps.ps2000aStop(chandle) # handle = chandle
    assert_pico_ok(status['stop'])

    # Close unit & Disconnect the scope
    status['close'] = ps.ps2000aCloseUnit(chandle) # handle = chandle
    assert_pico_ok(status['close'])

    # display status returns
    #print(status)
    #for key in status:
    #    print(key, PICO_STATUS_LOOKUP[status[key]])
    
    time = np.array(time)
    voltage_a = np.array(adc_2_mV_ch_a)
    voltage_b = np.array(adc_2_mV_ch_b)

    return time, voltage_a, voltage_b

if(__name__ == '__main__'):
    import csv

    time, voltage_a, voltage_b = capture_waveform()

    output_file = open('waveform_t_esp32.csv', mode = 'w')
    csv_writer = csv.writer(output_file, delimiter = ',')
    csv_writer.writerow(time)
    csv_writer.writerow(voltage_a)
    csv_writer.writerow(voltage_b)
    output_file.close()

    # plot waveform
    plt.plot(time, voltage_a)
    plt.plot(time, voltage_b)
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (mV)')
    plt.savefig('waveform_t_esp32.svg', format = 'svg')
    plt.close()
    plt.figure().clear()
