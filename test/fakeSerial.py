from pathlib import Path
from unittest import TestCase
from time import sleep
from src.aicam.gps import GPS
# Fake serial device for mocks

class Serial:
    """Mock class for serial"""
    def __init__(self,port,baudrate):
        self.data = None
        mypath = Path('mockdata/gpsdata.txt')
        if not mypath.exists:
            raise OSError(f"Can't find file {mypath.absolute()}")
        with open(mypath.absolute(),'r') as myfile:
            self.data = myfile.read()
    def is_open(self):
        return True

    def readline(self):
        for line in self.data:
            sleep(1)
            return line



class test_GPS(TestCase):
    def __init__(self):
        self.mockserial = Serial()

