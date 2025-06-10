import cv2
from client_class import CarClient


def __ex1(p):
    command = ""
    try:
        client = CarClient(port=p)
        while command != "END":
            command = input("Please insert the desired command: CAM, SMART, AUTO, MANUAL, END: ").upper()
            client.send_command(command)
    except Exception as e:
        print(f"There has been an error: {e}")

def __ex2(p):
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



if __name__== "__main__":
    p = 50002
    __ex1(p)
    #__ex2(p)