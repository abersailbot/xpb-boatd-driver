from threading import Lock

import json
import serial

import gps as gpsd

import boatd


class Arduino(object):
    '''The arduino and basic communications with devices attached to it'''

    def __init__(self, port=None, baud=115200):
        try:
            self.port = serial.Serial(port, baudrate=baud)
        except Exception as e:
            raise IOError(
                'Cannot connect to arduino on {} - {}'.format(port, e))
        self._lock = Lock()
        #self.port.readline()

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

    def get_wind(self):
        return self.send_command('w').get('wind')

    def set_rudder(self, amount):
        '''Set the rudder to an amount between 1000 and 2000'''
        return self.send_command('r{}'.format(amount)).get('rudder')

    def set_sail(self, amount):
        '''
        Set the sail to an amount between 1100 (fully out) and 2100 (fully in).
        '''

        return self.send_command('s{}'.format(amount)).get('sail')


class DewiDriver(boatd.BaseBoatdDriver):
    def __init__(self):
        self.arduino = Arduino('/dev/arduino')
        self.gps = gpsd.gps(mode=gpsd.WATCH_ENABLE)
        self.previous_lat = 0
        self.previous_long = 0

    def heading(self):
        return self.arduino.get_compass()

    def wind_direction(self):
        return self.arduino.get_wind()

    def wind_speed(self):
        # dewi can't get the wind speed
        pass

    def position(self):
        if self.gps.waiting(timeout=2):
            fix = self.gps.next()
            i = 0
            while fix['class'] != 'TPV':
                if self.gps.waiting(timeout=2) and i < 15:
                    fix = self.gps.next()
                    i += 1
                else:
                    return (self.previous_lat, self.previous_long)

            self.previous_lat = fix.lat
            self.previous_long = fix.lon
            return (fix.lat, fix.lon)

        else:
            return (self.previous_lat, self.previous_long)

    def rudder(self, angle):
        ratio = (1711/22.5) / 8  # ratio of angle:microseconds
        amount = 1500 + (angle * ratio)
        self.arduino.set_rudder(amount - 65)

    def sail(self, angle):
        angle = abs(angle)
        # 1000 is difference between the two extremes of winch inputs, 70 is
        # the maximum angle the sail will move to when the winch is fully
        # extended. 2100 is the winch value when the sail is full in.

        # FIXME: this is kind of non-linear, so adjust for this at some point
        amount = -angle*(1000/70) + 2100
        self.arduino.set_sail(amount)


driver = DewiDriver()


if __name__ == '__main__':
    a = Arduino('/dev/arduino')
    print a.get_compass()
    print a.get_wind()
    print a.set_rudder(0)
    print a.set_sail(0)
