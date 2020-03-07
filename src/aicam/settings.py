from knobs import Knob
from socket import gethostname

CAMERA_NUMBER = Knob(env_name="CAMERA_NUMBER", default=0,
                     description="Raspberry Pi camera number according to "
                                 "https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera")

INVERT_CAMERA = Knob(env_name="CAMERA_INVERT", default=False, description="Vertical invert camera")

GPS_SERIAL_PORT = Knob(env_name="GPS_SERIAL_PORT", default="/dev/ttyAMA0", description="Serial port for GPS")
GPS_BAUD_RATE = Knob(env_name="GPS_BAUD_RATE", default=9600, description="Baud rate on GPS")
MODEL_PATH = Knob(env_name="MODEL_PATH", default='/opt/model', description="Pytorch Model Location")
BASE_URL = Knob(env_name="BASE_URL", default='127.0.0.1', description="Base URL to send HTTP post to")
DEVICE_NAME = Knob(env_name="DEVICE_NAME", default=gethostname(), description="Device Name")