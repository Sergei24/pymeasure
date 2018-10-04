import logging
from time import sleep
import numpy as np
from pymeasure.instruments.keithley import Keithley2182, Keithley6220
from pymeasure.experiment import (
    Procedure, FloatParameter
)

log = logging.getLogger('')
log.addHandler(logging.NullHandler())


def CurrentValues(rangeA, stepA):
        CurrentValues = np.hstack((np.arange(0, rangeA, stepA), np.arange(
            rangeA, -rangeA, -stepA), np.arange(-rangeA, 0, stepA)))
        CurrentValues = np.append(CurrentValues, 0)
        return CurrentValues


class IV(Procedure):

    current_range = FloatParameter('Maximum Current', units='mkA', default=0.1)
    current_step = FloatParameter('Current Step', units='nA', default=10)
    delay = FloatParameter('Delay Time', units='ms', default=10)

    DATA_COLUMNS = ['Current (A)', 'Voltage (V)', 'Resistance (Ohm)']

    def startup(self):
        log.info("Setting up instruments")
        self.meter = Keithley2182("GPIB::25")
        self.meter.setup()

        self.source = Keithley6220("GPIB::1")
        self.source.enable_auto_range()
        self.source.source_current_range = self.current_range * 1e-6  # calculates in Amperes
        self.source.complinance_voltage = 100  # Volts
        self.source.reset()
        self.source.enable_source()
        sleep(2)

    def execute(self):
        currents = CurrentValues(current_range, current_step * 1e-3)  # dont forget to change step from nA to mkA
        currents *= 1e-6  # and finally change to A
        steps = len(currents)

        log.info("Starting to sweep through current")
        for i, current in enumerate(currents):
            log.debug("Measuring current: %g mA" % current)

            self.source.current = current
            sleep(self.delay * 1e-3)

            voltage = self.meter.measure_voltage()
            resistance = voltage / current
            data = {
                'Current (A)': current,
                'Voltage (V)': voltage,
                'Resistance (Ohm)': resistance
            }
            self.emit('results', data)
            self.emit('progress', 100. * i / steps)
            if self.should_stop():
                log.warning("Catch stop command in procedure")
                break

    def shutdown(self):
        self.source.shutdown()
        log.info("Finished")
