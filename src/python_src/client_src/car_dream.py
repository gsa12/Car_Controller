import cv2
import threading

import keyboard
from ultralytics import YOLO
from client_class import CarClient


def smart_car(p):
    client = None
    try:
        client = CarClient(port=p)
        threading.Thread(target=client.send_command, args=("MANUAL",)).start()
        while True:
            client.frame_updater()
            if client.current_frame is not None:
                cv2.imshow("Frame", client.current_frame)
                '''
                if ...:
                    keyboard.press("w")
                if ...:
                    keyboard.press("a")
                if ...:
                    keyboard.press("s")
                if ...: 
                    keyboard.press("d")
                '''
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except Exception as e:
        print(f"There has been an error: {e}")
    finally:
        client.frame_updater(close=True)
        client.disconnect()



if __name__=="__main__":
    p = 50000
    smart_car(p)