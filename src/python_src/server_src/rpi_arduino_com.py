import serial
import serial.tools.list_ports as port_list
import time
import serial
import serial.tools.list_ports as port_list
import time
import sys
from socket import socket

# The arduino port is created with its name and baudrate. From now on i can use it as
# any other object

arduinoUSB = None


def serial_RPiArduino(stringReceived="Hi", close=0, first=False, socket_received=None, continuos=False):
	global arduinoUSB

	if first:
		arduinoUSB = serial.Serial("/dev/ttyACM0", 9600)
		time.sleep(1)

	if continuos and socket_received is not None:
		if arduinoUSB is None:
			arduinoUSB = serial.Serial("/dev/ttyACM0", 9600)
			time.sleep(0.01)
		arduinoUSB.write(f"{2}\n".encode("utf-8"))
		time.sleep(1)
		print("Entering manual mode.")
		while True:
			msg = socket_received.recv(1024).decode().strip()
			arduinoUSB.write(
				f"{msg}\n".encode("utf-8"))  # Encoding necessary for serial communication to be successfully achieved
			print(msg)
			if msg == "c" or msg == "END":
				print("The program has been closed by client's order.")
				arduinoUSB.write(f"STOP\n".encode("utf-8"))
				time.sleep(0.1)
				arduinoUSB.write(f"0\n".encode("utf-8"))
				break
	else:
		if arduinoUSB is None:
			pass
		else:
			arduinoUSB.write(f"{stringReceived}\n".encode("utf-8"))

	if close == 1:
		if arduinoUSB is not None:
			arduinoUSB.close()
			arduinoUSB = None
		else:
			pass


if __name__ == "__main__":
	serial_RPiArduino("hello", 1, first=True)
