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

class Keithley6220(Instrument, KeithleyBuffer):
    """ Represents the Keithely 6220 DC Currunt Source and provides a
    high-level interface for interacting with the instrument.
    .. code-block:: python
        keithley = Keithley6220("GPIB::1")

        keithley.apply_current()                # Sets up to source current
        keithley.source_current_range = 10e-3   # Sets the source current range to 10 mA
        keithley.compliance_voltage = 10        # Sets the compliance voltage to 10 V
        keithley.source_current = 0             # Sets the source current to 0 mA
        keithley.enable_source()                # Enables the source output
        keithley.measure_voltage()              # Sets up to measure voltage
        keithley.ramp_to_current(5e-3)          # Ramps the current to 5 mA
        print(keithley.voltage)                 # Prints the voltage in Volts
        keithley.shutdown()                     # Ramps the current to 0 mA and disables output
    """

    # TODO: Add measurement mode property

    ###############
    # Current (A) #
    ###############

    ONOFF = ["ON", "OFF"]

    current_range = Instrument.control(
        "CURRent:RANGe?", "CURRent:RANGe:AUTO 0;CURRent:RANGe %g",
        """ A floating point property that controls the measurement current
        range in Amps, which can take values between -105 and +105 mA.
        Auto-range is disabled when this property is set. """,
        validator=truncated_range,
        values=[-105e-3, 105e-3]
    )
    current = Instrument.setting(
        "CURRent?", "CURRent %g",
        """ A floating point property that controls the source current
        in Amps. """
    )
    current_filter = Instrument.control(
        "CURRent:FILTer?", "CURRent:FILTer %s",
        """ A boolean property that enables or disables
        the output analog filter.""",
        validator=strict_discrete_set,
        values=ONOFF
    )

    ###############
    # Voltage (V) #
    ###############

    compliance_voltage = Instrument.control(
        "CURRent:COMPliance?", "CURRent:COMPliance %g",
        """ A floating point property that controls the compliance voltage
        in Volts. """,
        validator=truncated_range,
        values=[0.1, 105]
    )

    ###########
    # Trigger #
    ###########

    trigger_count = Instrument.control(
        ":TRIG:COUN?", ":TRIG:COUN %d",
        """ An integer property that controls the trigger count,
        which can take values from 1 to 9,999. """,
        validator=truncated_range,
        values=[1, 2500],
        cast=int
    )
    trigger_delay = Instrument.control(
        ":TRIG:SEQ:DEL?", ":TRIG:SEQ:DEL %g",
        """ A floating point property that controls the trigger delay
        in seconds, which can take values from 0 to 999.9999 s. """,
        validator=truncated_range,
        values=[0, 999.9999]
    )

    def __init__(self, adapter, **kwargs):
        super(Keithley6220, self).__init__(
            adapter, "Keithley 6220 DC Currunt Source", **kwargs
        )

    def shutdown(self):
        """Sets output to zero, then turns the output off"""
        log.info("Shutting down %s." % self.name)
        self.write("SourceMeter")

    def enable_source(self):
        """ Enables the source of current or voltage depending on the
        configuration of the instrument. """
        self.write("OUTPUT ON")

    def disable_source(self):
        """ Disables the source of current or voltage depending on the
        configuration of the instrument. """
        self.write("OUTPUT OFF")

    def enable_auto_range(self):
        """ Configures the source to use an automatic range.
        """
        self.write("CURRent:RANGe:AUTO 1")

    def disable_auto_range(self):
        """ Configures the source to use an automatic range.
        """
        self.write("CURRent:RANGe:AUTO 0")

    @property
    def error(self):
        """ Returns a tuple of an error code and message from a
        single error. """
        err = self.values(":system:error?")
        if len(err) < 2:
            err = self.read()  # Try reading again
        code = err[0]
        message = err[1].replace('"', '')
        return (code, message)

    def check_errors(self):
        """ Logs any system errors reported by the instrument.
        """
        code, message = self.error
        while code != 0:
            t = time.time()
            log.info("Keithley 2400 reported error: %d, %s" % (code, message))
            code, message = self.error
            if (time.time() - t) > 10:
                log.warning("Timed out for Keithley 2400 error retrieval.")

    def reset(self):
        """ Resets the instrument."""
        self.write("*RST")
        self.write("*CLS")

    def ramp_to_current(self, target_current, steps=30, pause=20e-3):
        """ Ramps to a target current from the set current value over
        a certain number of linear steps, each separated by a pause duration.
        :param target_current: A current in Amps
        :param steps: An integer number of steps
        :param pause: A pause duration in seconds to wait between steps
        """
        currents = np.linspace(
            self.source_current,
            target_current,
            steps
        )
        for current in currents:
            self.current = current
            time.sleep(pause)
