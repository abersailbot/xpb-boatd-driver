from threading import Lock

import json
import serial

import gps as gpsd

from rowind import Rowind

import boatd
assert boatd.VERSION == 1.1

class Arduino(object):
    '''The arduino and basic communications with devices attached to it'''
    def __init__(self, port=None, baud=115200):
        try:
            self.port = serial.Serial(port, baudrate=baud)
        except Exception as e:
            raise IOError('Cannot connect to arduino on {} - {}'.format(port, e))
        self._lock = Lock()
        self.port.readline()

    def read_json_line(self):
        '''Return a decoded line'''
        with self._lock:
            return json.loads(self.port.readline())

    def send_command(self, c):
        '''
        Send a short command, and return a single line response. Prevents
        other threads interweaving requests by locking on self._lock
        '''
        with self._lock:
            self.port.flushInput()
            self.port.write(c + '\n')
            return json.loads(self.port.readline())

    def get_compass(self):
        '''Return the heading from the compass in degrees'''
        return self.send_command('c').get('compass')

    def get_wind(self)
        return self.send_command('w').get('wind')

    def set_rudder(self, amount):
        '''Set the rudder to an amount between 1000 and 2000'''
        return self.send_command('r{}'.format(amount)).get('rudder')

    def set_sail(self, amount):
        '''Set the sail to an amount between 1000 and 2000'''
        return self.send_command('s{}'.format(amount)).get('sail')


driver = boatd.Driver()
arduino = Arduino('/dev/arduino')
gps = gpsd.gps(mode=gpsd.WATCH_ENABLE)


@driver.heading
def kitty_heading():
    return arduino.get_compass()

@driver.wind_direction
def kitty_wind():
    return arduino.get_wind()

@driver.position
def kitty_position():
    if gps.waiting(timeout=2):
        fix = gps.next()
        i = 0
        while fix['class'] != 'TPV':
            if gps.waiting(timeout=2) and i < 15:
                fix = gps.next()
                i += 1
            else:
                return (None, None)

        return (fix.lat, fix.lon)

    else:
        return (None, None)

@driver.rudder
def kitty_rudder(angle):
    ratio = (1711/22.5) / 8 # ratio of angle:microseconds
    amount = 1500 + (angle * ratio)
    arduino.set_rudder(amount - 65)

@driver.sail
def kitty_sail(angle):
    arduino.set_sail(angle)

if __name__ == '__main__':
    import time
    a = Arduino('/dev/arduino')
    print a.get_compass()
    print a.get_wind()
    print a.set_rudder(0)
    print a.set_sail(0)
