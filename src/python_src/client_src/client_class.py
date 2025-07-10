import socket
import sys
import time
import threading
import cv2
import keyboard as k
from numpy.f2py.crackfortran import previous_context


class CarClient:
    """
    A client_src class that enables some basic controls over the car.
    The constructor automatically connects to the raspberry pi.
    """

    def __init__(self, ip_host="10.42.0.1", port=50000, seconds = 892):
        """
            A client_src class that enables some basic controls over the car.
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

        if self.__connect() < 0:
            raise Exception("It was not possible to establish a connection.")


    def disconnect(self):
        if self.client_socket is None:
            print("There was no connection to close.")
            return -1
        if self.__video_thread is not None:
            self.__stop_video_thread.set()
            self.__video_thread.join()
        self.client_socket.close()
        print("The connection has been closed.")
        return 1

    # noinspection PyInconsistentReturns
    def send_command(self, command, block_manual=True, expected_response=True):
        """
            Method to send a single command to the server, printing the response.
            It also starts the camera feed.
            Args: command -> The command to be sent to the car.
        """
        client_socket = self.client_socket
        previously_running = False

        if client_socket is None:
            print("There isn't a client_src to send the command to.")
            return
        else:
            try:
                client_socket.send(command.encode())
                if expected_response:
                    number_of_responses = int(client_socket.recv(1024).decode())
                    if number_of_responses == 1:
                        response = client_socket.recv(1024).decode()
                        print(f"Server response: {response}")
                    else:
                        for n in range(number_of_responses):
                            response = client_socket.recv(1024).decode()
                            print(f"Server response: {response}")
                    if not self.already_running and command != "STOP" and command != "END":
                        if command in ["CAM", "AUTO"]:
                            print("To close the video feed, press 'q'.")
                            self.__video_thread = threading.Thread(target=self.__aux_vid)
                            self.__video_thread.start()
                            self.already_running = True
                        if command == "MANUAL":
                            if block_manual:
                                self.__wasd_sender()
                                return 1
                            else:
                                pass
                    elif self.already_running and command == "STOP":
                        self.__stop_video_thread.set()
                        time.sleep(0.2)
                        self.already_running = False
                        cv2.destroyAllWindows()
                        print("The video feed has been closed")
                    elif not self.already_running and command == "STOP":
                        print("There was not anything to stop.")
                        return -1
                    elif self.already_running and command == "END":
                        self.disconnect()
                        time.sleep(0.2)
                        cv2.destroyAllWindows()
                    elif self.already_running:
                        print("Command unavailable. Since a camera feed is already running, you can only insert the commands STOP or END")
            except Exception as e:
                print(f"It wasn't possible to send the command, {e}")


    def frame_updater(self, vid_port="5000", close=False, cap_provided = None):
        """
            Updates self.current_frame with the most recent frame from the video stream. If there was
            an error, the variable will be set to None. If you wish to close the video stream, set close to True.
            Call this method each time you want to update the frame.
        """

        if self.client_socket is None:
            print("There hasn't been established any connection yet.")
            return None

        if cap_provided is None:
            stream_url = f"http://{self.ip_host}:{vid_port}/raw_stream"
            video_cap = cv2.VideoCapture(stream_url)
        else:
            video_cap = cap_provided

        if video_cap.isOpened():
            ret, frame = video_cap.read()
            if ret:
                self.current_frame = frame
            else:
                print("There has been an error retrieving the frame.")
                self.current_frame = None
        if close:
            video_cap.release()
            return None
        return None

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
                    time.sleep(0.5)
                    print("Manual mode has been closed.")
                    break
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
                time.sleep(0.015)  # To avoid unnecessary CPU usage
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
        """
            Initializes the video feed, displaying it on the screen
            Args:
                vid_port (str): The port to use for the video feed
            Returns:
                0 when the video feed has been closed
        """

        video_cap = None

        try:
            self.__stop_video_thread.clear()
            stream_url = "http://" + self.ip_host + ":" + vid_port + "/raw_stream"
            print(stream_url + '\n')
            video_cap = cv2.VideoCapture(stream_url)

            video_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            start_time = time.time()
            while video_cap.isOpened() and (start_time+self.seconds)>time.time() and not self.__stop_video_thread.is_set():
                flag, frame = video_cap.read()
                if not flag:
                    print("There has been an error reading the current frame")
                    time.sleep(0.2)
                else:
                    cv2.imshow("Car video feed", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nThe video feed has been closed by the user.")
                        self.send_command("STOP", expected_response=False)
                        # Clear the buffer from the response from the server for the STOP command
                        try:
                            number_of_responses = int(self.client_socket.recv(1024).decode())
                            for _ in range(number_of_responses):
                                self.client_socket.recv(1024).decode()  # Read and discard
                        except (ValueError, ConnectionAbortedError):
                            # Ignore errors if the connection is already closing
                            pass
                        break
        finally:
            video_cap.release()
            cv2.destroyAllWindows()

        return 1
