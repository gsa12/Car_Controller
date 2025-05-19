import socket
import time
import threading
import cv2
import keyboard as k
import sys


class CarClient:
    """
    A client class that enables some basic controls over the car.
    The constructor automatically connects to the raspberry pi.
    """

    def __init__(self, ip_host="10.42.0.1", port=50000, seconds = 892):
        """
            A client class that enables some basic controls over the car.
            The constructor automatically connects to the raspberry pi.
            Args:
                ip_host (str): The ip address of the server
                port (int): The port to use for communications
        """
        self.ip_host = ip_host
        self.port = port
        self.seconds = seconds
        self.already_running = False

        self.client_socket = None
        self.current_frame = None

        self.__video_thread = None
        self.__stop_video_thread = threading.Event()
        self.__frame_returner_thread = None
        self.__stop_frame_returner = threading.Event()

        if self.__connect() < 0:
            raise Exception("It was not possible to establish a connection.")


    def disconnect(self):
        if self.client_socket is None:
            print("There was no connection to close.")
            return -1
        if self.__video_thread is not None:
            self.__stop_video_thread.set()
            self.__video_thread.join()
        if self.__frame_returner_thread is not None:
            self.__stop_frame_returner.set()
        self.client_socket.close()
        print("The connection has been closed.")
        return 1


    def send_command(self, command):
        """
            Method to send a single command to the server, printing the response.
            It also starts the camera feed.
            Args: command -> The command to be sent to the car.
        """
        command = command.upper()
        client_socket = self.client_socket
        already_running = self.already_running

        if client_socket is None:
            print("There isn't a client to send the command to.")
            return
        else:
            try:
                client_socket.send(command.encode())
                number_of_responses = int(client_socket.recv(1024).decode())
                if number_of_responses == 1:
                    response = client_socket.recv(1024).decode()
                    print(f"Server response: {response}")
                else:
                    for n in range(number_of_responses):
                        a = 1+1
                        response = client_socket.recv(1024).decode()
                        print(f"Server response: {response}")
                if not already_running and command != "STOP" and command != "END":
                    if command in ["CAM", "AUTO"]:
                        self.__video_thread = threading.Thread(target=self.__aux_vid)
                        self.__video_thread.start()
                    if command == "MANUAL":
                        self.__video_thread = threading.Thread(target=self.__aux_vid)
                        self.__video_thread.start()
                        self.__wasd_sender()
                    if command == "SMART":
                        self.__video_thread = threading.Thread(target=self.__aux_vid)
                        self.__video_thread.start()
                        print("Oops still in development. Only the video feed will be shown.")
                elif already_running and command == "STOP":
                    self.__stop_video_thread.set()
                    time.sleep(0.2)
                    self.already_running = False
                    print("The video feed has been closed")
                elif already_running and command == "END":
                    self.disconnect()
                    time.sleep(0.2)
                    cv2.destroyAllWindows()
                elif already_running:
                    print("Command unavailable. Since a camera feed is already running, you can only insert the commands STOP or END")
            except Exception as e:
                print(f"It wasn't possible to send the command, {e}")


    def frame_updater(self) :
        """
            Used when the user desires to treat the image received.
            Puts a numpy array with the current video frame on the current_frame variable, or none, if there was an error.
        """
        if self.client_socket is None:
            print("There hasn't been established any connection yet.")
            return None

        self.__frame_returner_thread = threading.Thread(target=self.__frame_updater_aux)
        self.__frame_returner_thread.start()


    def frame_updater_close(self):
        if self.__frame_returner_thread is None:
            print("The frame updater method isn't being run.")
        else:
            self.__stop_frame_returner.set()
            self.__frame_returner_thread.join()


    def __wasd_sender(self):
        """
            Handles the key presses and sends them to the server socket
            Returns:
                1 when the "c" key has been pressed
        """
        try:
            print("Please, touch the keyboard keys WASD to control the car.")
            while True:
                if k.is_pressed("c"):
                    message = "c"
                    self.client_socket.send(message.encode())
                    sys.stdin.flush()
                    #To delete the WASD sender buffer
                    time.sleep(0.5)
                    print("Manual mode closed.")
                    return 1
                if k.is_pressed("w"):
                    message = "f"
                    self.client_socket.send(message.encode())
                if k.is_pressed("a"):
                    message = "l"
                    self.client_socket.send(message.encode())
                if k.is_pressed("s"):
                    message = "b"
                    self.client_socket.send(message.encode())
                if k.is_pressed("d"):
                    message = "r"
                    self.client_socket.send(message.encode())
                time.sleep(0.05)
        except Exception as e:
            print(f"Error while sending direction commands, {e}")
            return -1


    def __connect(self):
        """
            A method to establish the connection between the platform and the pc.
            Returns:
                -1 if there was an error, else returns 1.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip_host, self.port))
            self.client_socket.settimeout(5.0)
            print("Connection established successfully")
            return 1
        except Exception as e:
            print(f"Could not establish connection, {e}")
            return -1


    def __aux_vid(self, vid_port="5000"):
        """Initializes the video feed, displaying it on the screen"""
        self.already_running = True
        stream_url = "http://"+self.ip_host+":"+vid_port+"/raw_stream"
        print(stream_url+'\n')
        video_cap = cv2.VideoCapture(stream_url)

        video_cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
        start_time = time.time()

        while video_cap.isOpened() and (start_time+self.seconds)>time.time() and not self.__stop_video_thread.is_set():
            flag, frame = video_cap.read()
            if not flag:
                print("There has been an error reading the current frame")
                time.sleep(0.2)
            else:
                cv2.imshow("Car video feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        video_cap.release()
        cv2.destroyAllWindows()

        return 0


    def __frame_updater_aux(self, vid_port="5000"):
        video_cap = None
        try:
            self.client_socket.send("CAM".encode())
            stream_url = "http://" + self.ip_host + ":" + vid_port + "/raw_stream"
            video_cap = cv2.VideoCapture(stream_url)

            while not self.__stop_frame_returner.is_set():
                if video_cap.isOpened():
                    ret, frame = video_cap.read()
                    if ret:
                        self.current_frame = frame
                    else:
                        print("There has been an error retrieving the frame.")
                        self.current_frame = None
        finally:
            video_cap.release()