import serial
import serial.tools.list_ports
import time

"""Provides an interface to open a serial port with minimum fuss"""

PORT_TIMEOUT = 1

def getPort():
	#get list of ports
	ports = serial.tools.list_ports.comports()


	comport = None
	#get the one we want
	if len(ports) == 0:
		raise IOError("No COM port found")
	elif len(ports) == 1:
		comport = ports[0]	
	#query user for input
	elif len(ports) > 1:
		#list out
		for i, port in enumerate(ports):
			print("{}: {}, {}, {}".format(i, port.device, port.name, port.description))
		
		#get response
		while True:
			try:
				desiredPort = int(input('Pick which port you want> '))
				comport = ports[i]
				break
			except (ValueError, IndexError):
				print("That is not a valid port")

	assert(comport is not None)

	return comport

#TODO: make it time out if no data received after some time
def openSerialConnection(portURL, baudrate=115200, timeout=PORT_TIMEOUT):
	"""Returns a serial.Serial object, waits for data
	
	Returns a fileLike Serial object
	Sleeps at intervals until data is available on the connection
	portURL and timeout are passed directly to serial.Serial
	i.e. timeout=None is wait forever, 0 is nonblocking, 
	n is timeout after n seconds

	"""

	portURL = getPort().device
	print("Opening connection to port " + portURL)
	serialConn = serial.Serial(portURL, baudrate=baudrate, timeout=PORT_TIMEOUT)

	print("Waiting for data...")
	while not serialConn.in_waiting:
		#print(serialConn.in_waiting)
		time.sleep(0.1)
	print("Connected")
	print("{} bytes waiting".format(serialConn.in_waiting))

	return serialConn
