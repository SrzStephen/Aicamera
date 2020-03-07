import click
class ConfigObject:
    def __init__(self):
        pass
from knobs import Knob
Config = click.make_pass_decorator(ConfigObject)


from src.aicam.settings import CAMERA_NUMBER, INVERT_CAMERA, GPS_BAUD_RATE, GPS_SERIAL_PORT,MODEL_PATH, BASE_URL
@click.group()
@click.option('--camera_number',default = CAMERA_NUMBER(),help=CAMERA_NUMBER.help(),type=int)
@click.option('--camera_invert',default=INVERT_CAMERA(),help=INVERT_CAMERA.help(),type=bool)
@click.option('--baud_rate',default=GPS_BAUD_RATE(),help=GPS_BAUD_RATE.help(),type=int)
@click.option('--serial_port',default=GPS_SERIAL_PORT(),help=GPS_SERIAL_PORT.help(),type=str)
@click.option('--model_path',default=MODEL_PATH(),help=MODEL_PATH.help(),type=str)
@click.option('--knobs',callback =Knob.print_knobs_env)
def cli(camera_number,camera_invert,baud_rate,serial_port,model_path):
    print(Knob.get_knob_defaults_as_table())
    pass
@cli.command("to_file")
@click.option("--file_path",default="/tmp/data",help="Directory to save predictions to",type=str)
def to_file(file_path):
    pass
@cli.command("to_http")
@click.option("--base_url",default=BASE_URL,help=BASE_URL.help(),type=str)
def to_http(base_url):

    pass

if __name__ == "__main__":
    cli()