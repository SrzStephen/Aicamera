import click
from src.aicam.settings import CAMERA_NUMBER, INVERT_CAMERA, GPS_BAUD_RATE, GPS_SERIAL_PORT, MODEL_PATH, BASE_URL
from src.aicam.settings import ACCESS_KEY, SECRET_KEY, SQS_QUEUE, DEVICE_NAME, MIN_PREDICT_SCORE, gethostname
from src.aicam.gps import GPS
from src.aicam.camera import Camera, image_to_base64
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
import boto3
from time import time, sleep

logger = getLogger(__name__)


# TODO only yield if predicted bad is above a certain value.
def image_generator(camera: Camera, gps: GPS, model_path: str, device_name: str, min_predict_score: float,
                    sleep_time=5):
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
            lat, lon = gps.read_until_gps()
            t2_var = Variable(tensor, requires_grad=False).float()
            prediction = model(t2_var)
            data = prediction.data[0]
            output = dict(
                lat=lat,
                lon=lon,
                image=image,
                is_good=float(data[0]),
                is_bad=float(data[1]),
                device_name=device_name
            )
            if output['is_bad'] > min_predict_score:
                yield output


class ConfigObject:
    def __init__(self):
        pass


config_class = click.make_pass_decorator(ConfigObject, ensure=True)


# TODO wait time
@click.group()
@click.option('--camera_number', default=CAMERA_NUMBER(), help=CAMERA_NUMBER.help(), type=int)
@click.option('--camera_invert', default=INVERT_CAMERA(), help=INVERT_CAMERA.help(), type=bool)
@click.option('--baud_rate', default=GPS_BAUD_RATE(), help=GPS_BAUD_RATE.help(), type=int)
@click.option('--serial_port', default=GPS_SERIAL_PORT(), help=GPS_SERIAL_PORT.help(), type=str)
@click.option('--model_path', default=MODEL_PATH(), help=MODEL_PATH.help(), type=str)
@click.option('--device_name', default=DEVICE_NAME(), help=DEVICE_NAME.help(), type=str)
@click.option('--min_predict_score', default=MIN_PREDICT_SCORE(), help=MIN_PREDICT_SCORE.help(), type=float)
@config_class
def cli(config, camera_number, camera_invert, baud_rate, serial_port, model_path, device_name, min_predict_score):
    logging.getLogger("PIL").setLevel(logging.WARNING)
    config.camera = Camera(invert=camera_invert, camera_num=camera_number)
    config.GPS = GPS(port=serial_port, baudrate=baud_rate)
    config.GPS.read_until_gps(timeout=100)
    config.model_path = model_path
    config.generator = image_generator(config.camera, config.GPS,
                                       config.model_path, config.device_name, min_predict_score)
    config.device_name = device_name
    config.min_predict_score = min_predict_score


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
    start = time()
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
            item['image'] = image_to_base64(item['image'])
            header = dict(sent_from=gethostname(), uptime=time() - start, device_name=config.device_name)
            http.post(f"{base_url}/data", data=item, headers=header)


@cli.command("to_stdout")
@config_class
def to_stdout(config):
    for item in config.generator:
        item.pop('image')
        print(item)


@cli.command("to_sqs")
@click.option("--queue", default=SQS_QUEUE(), help=SQS_QUEUE.help())
@click.option("--access_key", default=ACCESS_KEY(), help=ACCESS_KEY.help())
@click.option("--secret_key", default=SECRET_KEY(), help=SECRET_KEY.help())
@config_class
def to_sqls(config, access_key, secret_key, queue):
    start = time()
    if not access_key:
        raise ValueError("No AWS access key set. Please either use --access_key or"
                         " set environment variable AWS_ACCESS_KEY_ID")
    if not secret_key:
        raise ValueError("No AWS secret key set. Please either use --secret_key or"
                         " set environment variable AWS_SECRET_ACCESS_KEY")
    if not queue:
        raise ValueError("No AWS SQS queue defined. please either use --queue or"
                         "set environment variable SQS_QUEUE")

    session = boto3.Session(aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)
    sqs = session.resource('sqs')
    try:
        queue = sqs.get_queue_by_name(QueueName=queue)
    except Exception as e:
        logger.debug(f"SQS failed to get queue. Got {e}")
        raise ValueError(f"SQS queue {queue} not found or you don't have access to it!")

    for item in config.generator:
        # convert image to base64 to send
        item['image'] = image_to_base64(item['image'])
        header = dict(sent_from=gethostname(), uptime=time() - start, device_name=config.device_name)
        resp = queue.send_message(MessageAttributes=header, MessageBody=item)
        logger.debug(f"Sent message {item}, got response {resp}")


if __name__ == "__main__":
    basicConfig(level=logging.INFO)
    cli()
