from picamera import PiCamera
import numpy as np
from time import sleep
from logging import getLogger
from io import BytesIO
from PIL import Image
import torch
logger = getLogger(__name__)


class Camera(PiCamera):
    def __init__(self, invert: bool, camera_num: int):
        self.stream = BytesIO()
        self.camera = PiCamera.__init__(self, camera_num=camera_num)
        self.camera.resolution = (1024, 768)
        if invert:
            self.camera.rotation = 180
        self.camera.exposure_mode = 'antishake'
        self.camera.start_preview()

        sleep(2)

    def capture_still(self):
        self.camera.capture(self.stream, format='jpeg')
        self.stream.seek(0)
        image = Image.open(self.stream)
        # Image for looking at, image_tensor for showing.
        image_tensor = torch.from_numpy(np.asarray(image.thumbnail((512, 512))))
        return image, image_tensor
