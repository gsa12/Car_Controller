import socket
import time
import multiprocessing
import threading as thread
import numpy as np

from picamera2 import Picamera2, Preview
from time import sleep

from rpi_arduino_com import serial_RPiArduino
from vid_udp import vid_udp, cam_create
from vid_multicast import run_vid_server

video_server_process = None


def start_server():
    host_com = '0.0.0.0'  # Listen on all interfaces
    port_com = 50002
    global video_server_process
    # cam = cam_create()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket_com:

        try:
            server_socket_com.bind((host_com, port_com))
            server_socket_com.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            print("The port number has been increased by two")
            try:
                server_socket_com.bind((host_com, port_com))
                port_com = port_com + 2
                server_socket_com.bind((host_com, port_com))
            except Exception as e:
                print("The port number has been increased by four")
                try:
                    server_socket_com.bind((host_com, port_com))
                    port_com = port_com + 4
                    server_socket_com.bind((host_com, port_com))
                except Exception as e:
                    raise Exception("It wasn't possible to bind the socket to the desired port.")

        video_start()
        camera_started = False
        serial_RPiArduino(first=True)

        while True:

            server_socket_com.listen(1)
            print(f"Server listening on port {port_com} for commands.")

            client_socket_com, addr_com = server_socket_com.accept()
            print(f"Got connection from {addr_com} (commands)")

            while True:
                data = client_socket_com.recv(1024).decode()
                data = data.strip()
                print(f"Received message: '{data}'")

                if data == 'END':
                    client_socket_com.send("1".encode())
                    client_socket_com.send(f"Command '{data}' received!".encode())
                    time.sleep(0.1)
                    client_socket_com.send(f"Closing socket (commands)".encode())
                    client_socket_com.close()
                    serial_RPiArduino(stringReceived="0", close=1)
                    print("The client has disconnected from the server")
                    break
                elif data == 'CAM':
                    client_socket_com.send("1".encode())
                    client_socket_com.send(f"Command '{data}' received!".encode())
                    if not camera_started:
                        t2 = thread.Thread(target=serial_RPiArduino, args=("0", 0))
                        t2.start()
                        camera_started = True
                elif data == 'STOP':
                    client_socket_com.send("1".encode())
                    client_socket_com.send(f"Command '{data}' received!".encode())
                    if camera_started:
                        serial_RPiArduino(stringReceived="STOP")
                        time.sleep(0.01)
                        t2 = thread.Thread(target=serial_RPiArduino, args=("0", 0))
                        t2.start()
                        camera_started = False
                    else:
                        print("There was not a camera instance to stop")
                    serial_RPiArduino(stringReceived="STOP")
                elif data == 'MANUAL':
                    client_socket_com.send("1".encode())
                    client_socket_com.send(f"Command '{data}' received!".encode())
                    serial_RPiArduino(stringReceived="STOP")
                    time.sleep(0.01)  # To be sure the arduino has time to be reset
                    if not camera_started:
                        camera_started = True
                        serial_RPiArduino(stringReceived="", first=False, close=0, continuos=True,
                                          socket_received=client_socket_com)
                elif data == 'AUTO':
                    client_socket_com.send("1".encode())
                    client_socket_com.send(f"Command '{data}' received!".encode())
                    if not camera_started:
                        t2 = thread.Thread(target=serial_RPiArduino, kwargs={'stringReceived': "1"})
                        t2.start()
                        camera_started = True
                else:
                    client_socket_com.send("1".encode())
                    client_socket_com.send(
                        f"Command '{data}' unknown. Please insert one of the following: end, cam, manual, auto, stop.".encode())


def video_start():
    global video_server_process
    try:
        video_server_process = multiprocessing.Process(target=run_vid_server, daemon=True)
        video_server_process.start()
    except Exception as e:
        print(f"There was an error starting the video feed: {e}")


if __name__ == '__main__':
    start_server()


