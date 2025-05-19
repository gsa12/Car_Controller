import cv2
import threading

from ultralytics import YOLO
from client_class import CarClient


def smart_car(p):
    client = None
    try:
        client = CarClient(port=p)
        threading.Thread(target=client.send_command)
        client.frame_updater()
        while True:
            if client.current_frame is not None:
                cv2.imshow("Frame", client.current_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except Exception as e:
        print(f"There has been an error: {e}")


if __name__=="__main__":
    p = 50000
    smart_car(p)