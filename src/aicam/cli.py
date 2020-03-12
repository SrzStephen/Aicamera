import click
from src.aicam.settings import CAMERA_NUMBER, INVERT_CAMERA, GPS_BAUD_RATE, GPS_SERIAL_PORT,MODEL_PATH, BASE_URL
from src.aicam.gps import GPS
from src.aicam.camera import Camera
from attentive import quitevent
from logging import getLogger
from requests_toolbelt import sessions
import torch
from torch.autograd import Variable
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from logging import basicConfig
import logging
logger = getLogger(__name__)

def image_generator(camera:Camera,gps:GPS,model_path:str,sleep_time=5):
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Couldn't load model file {model_path}")
    model = torch.load(model_path,map_location=torch.device('cpu'))
    model.eval()
    # While we don't have a kill signal
    while not quitevent.is_set():
        if not gps.gps_is_ready:
            logger.info(f"GPS not ready waiting {sleep_time}")
            gps.read_until_gps(10)
        else:
            image, tensor = camera.capture_still()

            t2_var = Variable(tensor,requires_grad=False).float()
            lat, lon = gps.read_until_gps()
            prediction  = model(t2_var)
            data = prediction.data[0]
            output = dict(
                lat=lat,
                lon=lon,
                image=image,
                is_good=float(data[0]),
                is_bad=float(data[1])
            )
            yield output

class ConfigObject:
    def __init__(self):
        pass

config_class = click.make_pass_decorator(ConfigObject,ensure=True)

@click.group()
@click.option('--camera_number',default = CAMERA_NUMBER(),help=CAMERA_NUMBER.help(),type=int)
@click.option('--camera_invert',default=INVERT_CAMERA(),help=INVERT_CAMERA.help(),type=bool)
@click.option('--baud_rate',default=GPS_BAUD_RATE(),help=GPS_BAUD_RATE.help(),type=int)
@click.option('--serial_port',default=GPS_SERIAL_PORT(),help=GPS_SERIAL_PORT.help(),type=str)
@click.option('--model_path',default=MODEL_PATH(),help=MODEL_PATH.help(),type=str)
@config_class
def cli(config,camera_number,camera_invert,baud_rate,serial_port,model_path):



    config.camera = Camera(invert = camera_invert,camera_num=camera_number)
    config.GPS = GPS(port=serial_port,baudrate=baud_rate)
    config.GPS.read_until_gps(timeout=100)
    config.model_path = model_path
    config.generator = image_generator(config.camera,config.GPS,config.model_path)


@cli.command("to_file")
@click.option("--file_path",default="/tmp/data",help="Directory to save predictions to",type=str)
@config_class
def to_file(config,file_path):
    print(config)
    for item in config.generator:
        a =1


    raise NotImplementedError()

@cli.command("to_http")
@click.option("--base_url",default=BASE_URL,help=BASE_URL.help(),type=str)
@config_class
def to_http(config,base_url):
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
    basicConfig(level=logging.DEBUG)
    cli()