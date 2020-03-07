
from serial import Serial
from time import sleep, time
from pynmea2 import parse, GGA
from logging import getLogger
logger = getLogger(__name__)

class GPS:
    def __init__(self,port,baudrate):
        self.serial = Serial(port=port,baudrate=baudrate)
        sleep(1)
        if not self.serial.is_open():
            raise ConnectionError(f"Couldn't open serial port {port}")
        self.gps_is_ready = False
        logger.info(f"Successfuly loaded GPS on serial port {port}")

    def check_if_gps_ready(self,timeout:int):
        start_time = time()
        # Read NMEA strings until we get valid lat/longs or timeout
        while time() < start_time+timeout:
            message = self.serial.readline()
            message = parse(message)
            # We'll start getting valid lat/longs when gps quality > 0
            # https://www.gpsinformation.org/dale/nmea.htm#GGA
            if message.sentence_type is "GGA":
                if int(message.gps_qual) > 0:
                    logger.info("GPS is ready")
                    self.gps_is_ready = True
                    return True
        logger.debug("GPS not ready")
        return False


    def read_until_gps(self,timeout:int):
        start_time = time()
        while time() < start_time+timeout:
            message = self.serial.readline()
            logger.debug(message)
            message = parse(message)
            if message.sentence_type is "GGA":
                if int(message.gps_qual) > 0:
                    lat,lon = self.extract_latlong_gps(message)
                    if lat is not None and lon is not None:
                        return lat,lon
                else:
                    logger.info("GPS was ready, now isn't.")
                    self.gps_is_ready = False

    def extract_latlong_gps(self,message:GGA):
        if message.is_valid():
            if message.gps_qual > 0:
                return message.latitude,message.longitude
