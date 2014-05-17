from threading import Lock

import serial
import time

class Arduino(object):
    '''The arduino and basic communications with devices attached to it'''
    def __init__(self, port=None):
        try:
            self.port = serial.Serial(port)
            self.port.open()
        except Exception:
            raise Exception('Cannot connect to arduino on %s' % port)
        self._lock = Lock()
        time.sleep(1)

    def _sendCommand(self, c):
        '''
        Send a short command, and return a single line response. Prevents
        other threads interweaving requests by locking on self._lock
        '''
        with self._lock:
            self.port.flushInput()
            self.port.write(c + '\n')
            return self.port.readline()

    def get_compass(self):
        '''Get the heading from the compass'''
        return int(float(self._sendCommand('c')))

if __name__ == '__main__':
    import time
    a = Arduino() #create a test device on the arduino
    time.sleep(2)
    print a.set_rudder(0)

