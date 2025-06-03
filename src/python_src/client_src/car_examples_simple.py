import cv2
from client_class import CarClient


def ex1(p):
    command = ""
    try:
        client = CarClient(port=p)
        while command != "END":
            command = input("Please insert the desired command: CAM, SMART, AUTO, MANUAL, END: ").upper()
            client.send_command(command)
    except Exception as e:
        print(f"There has been an error: {e}")

def ex2(p):
    client = None
    try:
        client = CarClient(port=p)
        client.frame_updater()
        while True:
            if client.current_frame is not None:
                cv2.imshow("Frame", client.current_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except Exception as e:
        print(f"There has been an error: {e}")
    finally:
        client.send_command("END")
        client.frame_updater(close=True)
        client.disconnect()
        cv2.destroyAllWindows()

def __ex3():
    #cam = cv2.VideoCapture("http://192.168.1.97:5000/raw_stream")
    #cam = cv2.VideoCapture("http://10.42.0.1:5000/raw_stream")
    cam = cv2.VideoCapture("udp://10.42.0.1:5000")
    while True:
        flag, cap = cam.read()
        if not flag:
            pass
        cv2.imshow("Example n3", cap)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__== "__main__":
    p = 50000
    #ex1(p)
    #ex2(p)
    __ex3()
