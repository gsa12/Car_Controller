import socket
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Encoder, MJPEGEncoder, JpegEncoder
from picamera2.outputs import FileOutput, FfmpegOutput, PyavOutput
from libcamera import Transform

def vid_udp(BR=1000000, seconds=900, camera_object=None, close=False, ip="10.42.0.248", port=10000):
    if camera_object is None:
        print("ERROR: camera_object cannot be null")
        return
    
    cam = camera_object

    if close:
        cam.stop_recording()
        return 
    
    encoder = H264Encoder(bitrate=BR, iperiod=5)
    #encoder=MJPEGEncoder(bitrate=BR)
    #encoder=JpegEncoder()
	
    output = FfmpegOutput("-fflags nobuffer -flags low_delay -tune zerolatency -f mpegts udp://"+ip+":"+str(port))
    #output = FfmpegOutput("-f mpegts udp://"+ip+":"+str(port))
    #output = PyavOutput("udp://"+ip+":"+str(port), format="h264")
    cam.start_recording(encoder,output)
    time.sleep(seconds)
    cam.stop_recording()

def cam_create(res=(1280, 720), FR=60.0):
    cam = Picamera2()
    video_config = cam.create_video_configuration(lores={"size": res}, buffer_count = 4, queue = True)
    #video_config["controls"]["FrameRate"] = FR
    cam.configure(video_config)
    cam.start()
    return cam

if __name__ == "__main__":
    cam = cam_create()
    vid_udp(camera_object=cam)
    cam.close()
