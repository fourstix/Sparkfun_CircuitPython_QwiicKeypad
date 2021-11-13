# SPDX-FileCopyrightText: Copyright (c) 2021 Gaston Williams
#
# SPDX-License-Identifier: MIT

# The MIT License (MIT)
#
# Copyright (c) 2019 Gaston Williams
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
"""
`sparkfun_qwiickeypad`
================================================================================

CircuitPython library for the Sparkfun Qwiic Keypad


* Author(s): Gaston Williams

Implementation Notes
--------------------

**Hardware:**

*  This is library is for the SparkFun Qwiic 12-Button Keypad.
*  SparkFun sells these at its website: www.sparkfun.com
*  Do you like this library? Help support SparkFun. Buy a board!
   https://www.sparkfun.com/products/15290

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports__version__ = "0.0.0-auto.0"
__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/fourstix/Sparkfun_CircuitPython_QwiicKeypad.git"

# imports

from time import sleep
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

# public constants
QWIIC_KEYPAD_ADDR = const(0x4B) # default I2C Address

# register constants
_KEYPAD_ID = const(0x00)
_KEYPAD_VERSION1 = const(0x01)
_KEYPAD_VERSION2 = const(0x02)
_KEYPAD_BUTTON = const(0x03)
_KEYPAD_TIME_MSB = const(0x04)
_KEYPAD_TIME_LSB = const(0x05)
_KEYPAD_UPDATE_FIFO = const(0x06)
_KEYPAD_CHANGE_ADDRESS = const(0x07)

# This sets the bit0 on the updateFIFO register
_UPDATE_FIFO_COMMAND = const(0x01)

# class
class Sparkfun_QwiicKeypad:
    """CircuitPython class for the Sparkfun Qwiic 12-Button Keypad"""

    def __init__(self, i2c, address=QWIIC_KEYPAD_ADDR, debug=False):
        """Initialize Qwiic Keypad for i2c communication."""
        self._device = I2CDevice(i2c, address)
        #save handle to i2c bus in case address is changed
        self._i2c = i2c
        self._debug = debug

# public properites (read-only)

    @property
    def connected(self):
        """Check the id of Keypad.  Returns True if successful."""
        if self._read_register(_KEYPAD_ID) != QWIIC_KEYPAD_ADDR:
            return False
        return True

    @property
    def version(self):
        """Return the version string for the Keypad firmware."""
        major = self._read_register(_KEYPAD_VERSION1)
        minor = self._read_register(_KEYPAD_VERSION2)
        return 'v' + str(major) + '.' + str(minor)

    @property
    def button(self):
        """Return the button at the top of the stack (aka the oldest button).
           Return -1 for Error/Busy Try Again or 0 for No Button Pressed. """
        return self._read_register(_KEYPAD_BUTTON)

    @property
    def time_since_pressed(self):
        """Return the number of milliseconds since the current button in FIFO was pressed."""
        msb = self._read_register(_KEYPAD_TIME_MSB)
        lsb = self._read_register(_KEYPAD_TIME_LSB)
        return (msb << 8) | lsb

# public functions

    def set_i2c_address(self, new_address):
        """Change the i2c address of Keypad snd return True if successful."""
        # check range of new address
        if (new_address < 8 or new_address > 119):
            print('ERROR: Address outside 8-119 range')
            return False

        # write new address
        self._write_register(_KEYPAD_CHANGE_ADDRESS, new_address)

	# wait a second for joystick to settle after change
        sleep(1)

        # try to re-create new i2c device at new address
        try:
            self._device = I2CDevice(self._i2c, new_address)
        except ValueError as err:
            print('Address Change Failure')
            print(err)
            return False

        #if we made it here, everything went fine
        return True

    def update_fifo(self):
        """Commands keypad to plug in the next button into the register map."""
        self._write_register(_KEYPAD_UPDATE_FIFO, _UPDATE_FIFO_COMMAND)

# No i2c begin function is needed since I2Cdevice class takes care of that

# private methods

    def _read_register(self, addr):
        # Read and return a byte from the specified 8-bit register address.
        # ignore spurious Remote IO errors thrown when keypad is busy
        try:
            with self._device as device:
                result = bytearray(1)
                device.write_then_readinto(bytes([addr & 0xFF]), result)
                if self._debug:
                    print("$%02X => %s" % (addr, [hex(i) for i in result]))
                return result[0]
        except OSError as err:
            if self._debug:
                print(err)
            # return error value for read
            return -1

    def _write_register(self, addr, value):
        # Write a byte to the specified 8-bit register address
        # ignore spurious Remote IO errors thrown when keypad is busy
        try:
            with self._device as device:
                # Wait a bit for bus to settle
                sleep(0.050)
                device.write(bytes([addr & 0xFF, value & 0xFF]))
                if self._debug:
                    print("$%02X <= 0x%02X" % (addr, value))
        except OSError as err:
            if self._debug:
                print(err)
