from threading import Lock

import json
import serial

import boatd
assert boatd.VERSION == 1.1


class Arduino(object):
    '''The arduino and basic communications with devices attached to it'''
    def __init__(self, port=None):
        try:
            self.port = serial.Serial(port)
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

    def set_rudder(self, amount):
        '''Set the rudder to an amount between 1000 and 2000'''
        return self.send_command('r{}'.format(amount)).get('rudder')

    def set_sail(self, amount):
        '''Set the sail to an amount between 1000 and 2000'''
        return self.send_command('s{}'.format(amount)).get('sail')


driver = boatd.Driver()

arduino = Arduino('/dev/arduino')

@driver.heading
def kitty_heading():
    return arduino.get_compass()
