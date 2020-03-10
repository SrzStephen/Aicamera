import click
from .settings import CAMERA_NUMBER, INVERT_CAMERA, GPS_BAUD_RATE, GPS_SERIAL_PORT,MODEL_PATH, BASE_URL
from .gps import GPS
from .camera import Camera
from attentive import quitevent
from logging import getLogger
from time import sleep
from requests_toolbelt import sessions
import torch
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = getLogger(__name__)

def image_generator(camera:Camera,gps:GPS,model_path:str,sleep_time=5):
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Couldn't load model file {model_path}")
    model = torch.load(model_path)
    model.eval()
    # While we don't have a kill signal
    while not quitevent.is_set():
        if not gps.gps_is_ready():
            logger.info(f"GPS not ready waiting {sleep_time}")
            sleep(sleep_time)
        else:
            image, tensor = camera.capture_still()
            lat,lon = gps.read_until_gps()
            prediction  = model.input(tensor)
            # Todo: Figure out
            yield NotImplementedError()

class ConfigObject:
    def __init__(self):
        pass

Config = click.make_pass_decorator(ConfigObject)

@click.group()
@click.option('--camera_number',default = CAMERA_NUMBER(),help=CAMERA_NUMBER.help(),type=int)
@click.option('--camera_invert',default=INVERT_CAMERA(),help=INVERT_CAMERA.help(),type=bool)
@click.option('--baud_rate',default=GPS_BAUD_RATE(),help=GPS_BAUD_RATE.help(),type=int)
@click.option('--serial_port',default=GPS_SERIAL_PORT(),help=GPS_SERIAL_PORT.help(),type=str)
@click.option('-m --model_path',default=MODEL_PATH(),help=MODEL_PATH.help(),type=str)
@Config
def cli(Config,camera_num,camera_invert,baud_rate,serial_port,model_path):
    Config.camera = Camera(invert = camera_invert,camera_num=camera_num)
    Config.GPS = GPS(port=serial_port,baudrate=baud_rate)
    Config.model_path = model_path
    Config.generator = image_generator(Config.camera,Config.GPS,Config.model_path)


@cli.command("to_file")
@click.option("-f --file_path",default="/tmp/data",help="Directory to save predictions to",type=str)
def to_file():
    raise NotImplementedError()

@cli.command("to_http")
@click.option("--base_url",default=BASE_URL,help=BASE_URL.help(),type=str)
@Config
def to_http(Config,base_url):
    retry_strategy = Retry(
        total=5,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["POST"],
        backoff_factor=3
    )
    http = sessions.BaseUrlSession(base_url=BASE_URL())
    adaptor = HTTPAdapter(max_retries=retry_strategy)
    http.adapters = {"https://": adaptor, "http://": adaptor}
    raise NotImplementedError()
    for item in Config.generator():
        payload = {} #ToDo depends on what item returns
        http.post("/data",data=payload)

if __name__ == "__main__":
    cli()