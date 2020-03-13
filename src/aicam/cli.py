import click
from src.aicam.settings import CAMERA_NUMBER, INVERT_CAMERA, GPS_BAUD_RATE, GPS_SERIAL_PORT, MODEL_PATH, BASE_URL
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
import csv
from io import BytesIO
import base64

logger = getLogger(__name__)


def image_generator(camera: Camera, gps: GPS, model_path: str, sleep_time=5):
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Couldn't load model file {model_path}")
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    # While we don't have a kill signal
    while not quitevent.is_set():
        if not gps.gps_is_ready:
            logger.info(f"GPS not ready waiting {sleep_time}")
            gps.read_until_gps(10)
        else:
            image, tensor = camera.capture_still()

            t2_var = Variable(tensor, requires_grad=False).float()
            lat, lon = gps.read_until_gps()
            prediction = model(t2_var)
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


config_class = click.make_pass_decorator(ConfigObject, ensure=True)


@click.group()
@click.option('--camera_number', default=CAMERA_NUMBER(), help=CAMERA_NUMBER.help(), type=int)
@click.option('--camera_invert', default=INVERT_CAMERA(), help=INVERT_CAMERA.help(), type=bool)
@click.option('--baud_rate', default=GPS_BAUD_RATE(), help=GPS_BAUD_RATE.help(), type=int)
@click.option('--serial_port', default=GPS_SERIAL_PORT(), help=GPS_SERIAL_PORT.help(), type=str)
@click.option('--model_path', default=MODEL_PATH(), help=MODEL_PATH.help(), type=str)
@config_class
def cli(config, camera_number, camera_invert, baud_rate, serial_port, model_path):
    logging.getLogger("PIL").setLevel(logging.WARNING)
    config.camera = Camera(invert=camera_invert, camera_num=camera_number)
    config.GPS = GPS(port=serial_port, baudrate=baud_rate)
    config.GPS.read_until_gps(timeout=100)
    config.model_path = model_path
    config.generator = image_generator(config.camera, config.GPS, config.model_path)


@cli.command("to_file")
@click.option("--file_path", default="/tmp/data", help="Directory to save predictions to", type=str)
@config_class
def to_file(config, file_path):
    with Path(file_path) as path:
        if not path.exists():
            path.mkdir(file_path)
        if not path.is_dir():
            raise OSError(f"Path {file_path} is actually a file")
        count = 0
    for item in config.generator:
        path.mkdir(count)
        item['image'].save(Path(f"{file_path}/{count}/image.jpg", 'jpeg').absolute())
        with open(Path(f"{file_path}/{count}/data.csv").absolute(), 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(["latitude", "longitude", "bad_estimate", "good_estimate"])
            item['image'].pop()
            w = csv.DictWriter(fp, item.keys())
            w.writeheader()
            w.writerow(item)
            logger.info(item)


@cli.command("to_http")
@click.option("--base_url", default=BASE_URL, help=BASE_URL.help(), type=str)
@config_class
def to_http(config, base_url):
    retry_strategy = Retry(
        total=5,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["POST"],
        backoff_factor=3
    )
    http = sessions.BaseUrlSession(base_url=BASE_URL())
    adaptor = HTTPAdapter(max_retries=retry_strategy)
    http.adapters = {"https://": adaptor, "http://": adaptor}
    while not quitevent.is_set():
        for item in config.generator:
            # convert PIL to bytes
            byte_io = BytesIO()
            byte_io.seek(0)

            item['image'].save(byte_io, 'jpeg')
            image_str = base64.b64encode(byte_io.getvalue())
            item['image'] = image_str
            msg = http.post(f"{base_url}/data", data=item)
            a=1


@cli.command("to_stdout")
@config_class
def to_stdout(config):
    for item in config.generator:
        item.pop('image')
        print(item)





if __name__ == "__main__":
    basicConfig(level=logging.INFO)
    cli()
