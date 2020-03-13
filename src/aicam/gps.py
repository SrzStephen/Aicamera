from serial import Serial
from time import sleep, time
from pynmea2 import parse, GGA
from pynmea2.nmea import ChecksumError, ParseError
from logging import getLogger

logger = getLogger(__name__)


class GPS:
    def __init__(self, port, baudrate):
        self.serial = Serial(port=port, baudrate=baudrate)
        sleep(1)
        if not self.serial.is_open:
            raise ConnectionError(f"Couldn't open serial port {port}")
        self.gps_is_ready = False
        logger.info(f"Successfuly loaded GPS on serial port {port}")

    def check_if_gps_ready(self, timeout: int):
        start_time = time()
        # Read NMEA strings until we get valid lat/longs or timeout
        while time() < start_time + timeout:
            message = self.serial.readline()
            msg = self.process_line(message)
            if msg is not None:
                self.gps_is_ready = True
                return True
        logger.debug("GPS not ready")
        self.gps_is_ready = False
        return False

    def read_until_gps(self, timeout: int = 10):
        start_time = time()
        while time() < start_time + timeout:
            message = self.serial.readline()
            msg = self.process_line(message)
            if msg is not None:
                lat, lon = msg.latitude, msg.longitude
                self.gps_is_ready = True
                return lat, lon
                self.gps_is_ready = False

    @staticmethod
    def process_line(message):
        try:
            message = message.decode('utf-8')
            logger.debug(message)
            message = parse(message)
        except ChecksumError:
            logger.debug(f"Checksum error for {message}")
            return None
        except ParseError:
            logger.debug(f"Parse error for message {message}")
            return None
        except UnicodeDecodeError:
            logger.debug(f"couldn't decode {message}. Probably read in the middle of a string")

        if message.sentence_type == "GGA":
            if message.is_valid:
                if int(message.gps_qual) > 0:
                    return message
