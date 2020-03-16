from knobs import Knob
from socket import gethostname

CAMERA_NUMBER = Knob(env_name="CAMERA_NUMBER", default=0,
                     description="Raspberry Pi camera number according to "
                                 "https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera")

INVERT_CAMERA = Knob(env_name="CAMERA_INVERT", default=True, description="Vertical invert camera")

GPS_SERIAL_PORT = Knob(env_name="GPS_SERIAL_PORT", default="/dev/ttyUSB0", description="Serial port for GPS")

GPS_BAUD_RATE = Knob(env_name="GPS_BAUD_RATE", default=9600, description="Baud rate on GPS")

MODEL_PATH = Knob(env_name="MODEL_PATH", default='/home/pi/thirdstep.model', description="Pytorch Model Location")

BASE_URL = Knob(env_name="BASE_URL", default='https://foo.execute-api.us-east-1.amazonaws.com', description="Base URL to send HTTP post to")

DEVICE_NAME = Knob(env_name="DEVICE_NAME", default=gethostname(), description="Device Name")

SQS_QUEUE = Knob(env_name="SQS_QUEUE", default=False, description="SQS queue name")

ACCESS_KEY = Knob(env_name="AWS_ACCESS_KEY_ID", default=False, description="AWS Access Key")

SECRET_KEY = Knob(env_name="AWS_SECRET_ACCESS_KEY", default=False, description="AWS Secret Key")

MIN_PREDICT_SCORE = Knob(env_name="MIN_PREDICT_SCORE", default=5, description="Minimum score to send")
