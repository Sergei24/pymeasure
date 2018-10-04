#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2017 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
from pymeasure.instruments import Instrument, RangeException
from pymeasure.instruments.validators import truncated_range, strict_discrete_set

from .buffer import KeithleyBuffer

import numpy as np
import time

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class Keithley2182(Instrument, KeithleyBuffer):
    """ Represents the Keithely 2182 Nanovoltmeter and provides a
    high-level interface for interacting with the instrument.
    .. code-block:: python
        keithley = Keithley2182("GPIB::1")
    """

    def __init__(self, adapter, **kwargs):
        super(Keithley2182, self).__init__(
            adapter, "Keithley 2182 Nanovoltmeter", **kwargs
        )

        self.channel = 1

    def set_channel(self, channel_number):
        if channel_number == 1:
            self.channel = 1
            self.write(":SENSE:CHANNEL 1")
        elif channel_number == 2:
            self.channel = 2
            self.write(":SENSE:CHANNEL 2")
        elif channel_number == 0:
            self.channel = 0
            self.write(":SENSE:CHANNEL 0")
        else:
            print('incorrect channel number')

    def set_range(self, mes_range):
        self.write("SENSE:VOLTAGE:CHANNEL {0}:RANGE:UPPER {1}".format(self.channel, self.mes_range)) 

    voltage_nplc = Instrument.control(
        ":SENSE:VOLTAGE:NPLCycles?", ":SENSE:VOLTAGE:NPLCycles %g",
        """ A floating point property that controls the number of power line cycles
        (NPLC) for the DC voltage measurements, which sets the integration period 
        and measurement speed. Takes values from 0.01 to 10, where 0.1, 1, and 10 are
        Fast, Medium, and Slow respectively. """
    )

    def set_analog_filtering(self, Status):
             self.write(":SENSE:VOLTAGE:CHANNEL {0}:LPASS {1}".format(self.channel, Status))

    def measure_voltage(self, iterations=1):
        self.write("INITIATE:CONT OFF")
        result = 0
        for i in range(iterations):
            tmp = (self.query("READ?").split('E'))
            result += float(tmp[0]) * 10**int(tmp[1])
        return(result / iterations)

    def get_last_error(self):
        return self.query("SYST:ERR?")

    def reset(self):
        self.write("*RST")
        self.write("*CLS")

    def setup(self):
        commands = ['SENSe:VOLTage','SENSe:CHANnel 2', 'SENSe:VOLTage:NPLCycles 5', 'SYSTem:FAZero OFF']
        commands.extend(['SYSTem:AZERo OFF', 'SYSTem:LSYNc ON'])
        commands.extend(['SENSe:VOLTage:CHANnel2:RANGe:AUTO ON'])
        # commands.extend(['SENSe:VOLTage:CHANnel1:RANGe:UPPer 0.001'])
        commands.extend(['SENSe:VOLTage:CHANnel2:LPASs OFF','INITiate','INITiate:CONTinuous OFF'])
        for command in commands:
            self.write(command)
