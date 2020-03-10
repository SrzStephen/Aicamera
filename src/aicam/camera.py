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

        PiCamera.__init__(self, camera_num=camera_num,resolution=(1024, 1024))
        if invert:
            self.rotation = 180
        self.start_preview()

        sleep(2)

    def capture_still(self):
        self.capture(self.stream, format='jpeg')
        self.stream.seek(0)
        image = Image.open(self.stream)
        # Image for looking at, image_tensor for showing.
        thumb_size = 512,512
        image.thumbnail(thumb_size, Image.ANTIALIAS)
        image_tensor = torch.from_numpy(np.array(image))
        return image, image_tensor
