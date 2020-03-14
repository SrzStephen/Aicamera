from picamera import PiCamera
import numpy as np
from time import sleep
from logging import getLogger
from PIL import Image
import torch
from io import BytesIO
import base64

logger = getLogger(__name__)
from copy import deepcopy


class Camera(PiCamera):
    def __init__(self, invert: bool, camera_num: int):
        self.stream = BytesIO()

        PiCamera.__init__(self, camera_num=camera_num, resolution=(1024, 1024))
        if invert:
            self.rotation = 180
        self.start_preview()

        sleep(2)

    def capture_still(self):
        self.stream.seek(0)
        self.capture(self.stream, format='jpeg')
        image = Image.open(self.stream)
        fullsize_image = deepcopy(image)
        # Image for looking at, image_tensor for showing.
        thumb_size = 512, 512
        image.thumbnail(thumb_size, Image.ANTIALIAS)
        image_array = np.array(image)
        # swap axis from l w c to c l w
        image_array = np.transpose(image_array, (2, 0, 1))
        # Image tensor is expected as batch size c l w
        image_array = np.expand_dims(image_array, axis=0)
        image_tensor = torch.from_numpy(image_array)
        return fullsize_image, image_tensor


def image_to_base64(image):
    byte_io = BytesIO()
    byte_io.seek(0)
    image.save(byte_io, 'jpeg')
    image_str = base64.b64encode(byte_io.getvalue()).decode('utf-8')
    return image_str
