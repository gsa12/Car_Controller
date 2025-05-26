import cv2
import threading

from ultralytics import YOLO
from client_class import CarClient


def smart_car(p):
    client = None
    try:
        client = CarClient(port=p)
        while True:
            client.frame_updater()
            cv2.imshow("Objects recognition", client.current_frame)
    except Exception as e:
        print(f"There has been an error: {e}")
    finally:
        client.frame_updater(close=True)
        client.disconnect()


if __name__=="__main__":
    p = 50000
    smart_car(p)