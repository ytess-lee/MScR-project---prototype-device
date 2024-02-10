import time, libcamera
from picamera2 import Picamera2, Preview

picam = Picamera2()

config = picam.create_preview_configuration(main={"size": (1600, 1200)})
config["transform"] = libcamera.Transform(hflip=1, vflip=1)
picam.configure(config)

picam.start_preview(Preview.QTGL)

picam.start()
time.sleep(1)
picam.capture_file("neu-10.jpg")

picam.close()