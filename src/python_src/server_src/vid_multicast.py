from flask import Flask, Response
from vid_udp import cam_create
from picamera2 import Picamera2
from gpiozero import LED
import numpy as np
import cv2
import time
import threading
import os
import psutil
import sched

light = None


def create_vid_server():
    try:
        os.system("sudo pkill picamera2")
        os.system("sudo pkill pipewire")
        os.system("sudo pkill wireplumb")
    except:
        pass

    time.sleep(1)
    light = LED(26)
    frame = [None]
    app = Flask(__name__)
    frame_lock = threading.Lock()

    # Initialize the Picamera2
    camera = cam_create(res=(960, 640))
    # camera = cam_create()

    # Commands to avoid lag spikes -> Setting the process to the highest OS priority
    try:
        os.nice(-20)
        process = psutil.Process(os.getpid())
        if hasattr(psutil, 'REALTIME_PRIORITY_CLASS'):
            process.nice(psutil.REALTIME_PRIORITY_CLASS)
        else:
            os.nice(-20)
    except:
        print("It was not possible to establish this process with the highest priority")

    def frame_capturer():
        while True:
            start = time.time()
            raw_img = camera.capture_array()
            raw_img = cv2.flip(raw_img, 0)
            raw_img = cv2.cvtColor(raw_img, cv2.COLOR_RGB2BGR)
            success, buffer = cv2.imencode('.jpg', raw_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if success:
                with frame_lock:
                    frame[0] = buffer.tobytes()
            # print("Frame time:", time.time() - start)

            img_bw = np.dot(raw_img[..., :3], [0.299, 0.587, 0.114])
            if img_bw.mean() < 40:
                light.on()
            else:
                light.off()
            time.sleep(0.005)

    threading.Thread(target=frame_capturer, daemon=True).start()

    def generate_multipart():
        while True:
            with frame_lock:
                if frame[0] is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame[0] + b'\r\n')
            time.sleep(0.025)

    def generate_raw_mjpeg():
        while True:
            with frame_lock:
                if frame[0] is not None:
                    yield frame[0]
            time.sleep(0.025)

    # Generates an HTTP response that constantly updates itself with new images.
    # The mimetype is exactly for this. I t tells the browser that the images is going to be updating itself.
    # The boundary just tells the browser that each chunk of data is separated by an header that starts with "frame"
    # Each frame is in this format (taking a look at the generate multipart function:
    # --frame
    # Content-Type:image/jpeg
    # <the image itself>
    @app.route('/video_feed')
    def video_feed():
        return Response(generate_multipart(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/raw_stream')
    def raw_stream():
        return Response(generate_raw_mjpeg(), mimetype='video/x-motion-jpeg')

    @app.route('/')
    def index():
        return '''
        <html>
        <head><title>Live Video</title></head>
        <body>
        <h1>Car Live Feed</h1>
        <img src="/video_feed">
        <p>Use <code>/raw_stream</code> with OpenCV clients.</p>
        </body>
        </html>
        '''

    return app


def run_vid_server():
    try:
        app = create_vid_server()
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"There has been an error in the video server: {e}")
    finally:
        if light is not None:
            light.close()


if __name__ == '__main__':
    try:
        run_vid_server()
    except Exception as e:
        (f"Print there has been an error in the video server: {e}")
        if light:
            light.close()