from threading import Lock

import json
import serial
import time
import threading

import gps as gpsd

import boatd

max_sail_angle = 70
winch_value_full_in = 1800
winch_value_full_out = 1365
winch_input_range = winch_value_full_in - winch_value_full_out

class Arduino(object):
    '''The arduino and basic communications with devices attached to it'''

    def __init__(self, port=None, baud=115200):

        try:
            self.port = serial.Serial(port, baudrate=baud)
        except Exception as e:
            raise IOError(
                'Cannot connect to arduino on {} - {}'.format(port, e))
        self._lock = Lock()

    def read_json_line(self):
        '''Return a decoded line'''
        with self._lock:
            return json.loads(self.port.readline())

    def send_command(self, c):
        '''
        Send a short command, and return a single line response. Prevents
        other threads interweaving requests by locking on self._lock
        '''

        # the input buffer on the arduino is limited in size, so try not to
        # overflow it
        if len(c) > 9:
            raise 'arduino input line too long'

        with self._lock:
            self.port.flushInput()
            self.port.write(c + '\n')
            return json.loads(self.port.readline())


    def get_compass(self):
         '''Return the heading from the compass in degrees'''
         return self.send_command('c').get('compass')

    def get_pitch(self):
        '''Return the heading from the compass in degrees'''
        return self.send_command('p').get('pitch')

    def get_roll(self):
        '''Return the heading from the compass in degrees'''
        return self.send_command('&').get('roll')


    def get_wind(self):
        return 0

    def set_rudder(self, amount):
        '''Set the rudder to an amount between 1000 and 2000'''
        # note: at the time of writing, the arduino only accepts six bytes so
        # this must be converted to an int
        return self.send_command('r{}'.format(int(amount))).get('rudder')

    def set_sail(self, amount):
        '''
        Set the sail to an amount between 1100 (fully out) and 2100 (fully in).
        '''
        # note: at the time of writing, the arduino only accepts six bytes so
        # this must be converted to an int
        return self.send_command('s{}'.format(int(amount))).get('sail')


class XPBDriver(boatd.BaseBoatdDriver):
    def __init__(self):
        self.reconnect()
        self.previous_lat = 0
        self.previous_long = 0

    def reconnect(self):
        # sleep for a little to hope that devices are reset
        time.sleep(1)
        #CHANGEME comment out the next line if you have no arduino
        self.arduino = Arduino('/dev/arduino')
        self.gps = gpsd.gps(mode=gpsd.WATCH_ENABLE)

    def heading(self):
        #CHANGE ME TO READ CMPS12
        return self.arduino.get_compass()

    def roll(self):
        '''get roll in degrees between +/- 180'''
        #CHANGE ME TO READ CMPS12
        return self.arduino.get_roll()

    def pitch(self):
        '''get pitch in degrees between +/- 180'''
        #CHANGE ME TO READ CMPS12
        return self.arduino.get_pitch()

    def depth(self):
        '''get depth in metres'''
        return self.depth_metres

    def absolute_wind_direction(self):
        '''get the absolute wind in degrees'''
        #hard coded value, change to the current wind direction
        return 180
    
    def apparent_wind_direction(self):
        '''get the wind relative to the boat in degrees'''
        #calculate apparent wind by subtracing compass heading from the absolute wind direction
        apparent_wind_dir = (self.absolute_wind_direction() - self.heading()) % 360
        if apparent_wind_dir < 0:
            apparent_wind_dir += 360
        return apparent_wind_dir

    def wind_speed(self):
        # xpb's can't get the wind speed
        return 0

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
        #CHANGEME to use a rudder servo connected to the raspberry pi
        self.arduino.set_rudder(amount - 65)

    def sail(self, angle):
        # no sail winch on an XPB
        
        #new_angle = 70 - abs(angle)
        # winch_input_range is difference between the two extremes of winch inputs, 70 is
        # the maximum angle the sail will move to when the winch is fully
        # extended. 1800 is the winch value when the sail is full in.

        # FIXME: angle of 0 cannot be reached, generally around 5 degrees, account for this
        # FIXME: this is kind of non-linear, so adjust for this at some point
        #amount1 = -new_angle*(winch_input_range/max_sail_angle) 
        #amount = amount1 + winch_value_full_in

        #if amount < winch_value_full_out:
        #    amount = winch_value_full_out
        #if amount > winch_value_full_in:
        #    amount = winch_value_full_in

        #self.arduino.set_sail(amount)
        pass


driver = XPBDriver()


if __name__ == '__main__':
    a = Arduino('/dev/arduino')
    print(a.get_compass())
    print(a.get_wind())
    print(a.set_rudder(0))
    print(a.set_sail(0))
