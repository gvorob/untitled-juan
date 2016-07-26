import sys
import time
import re
import serial
import serial.tools.list_ports
import threading
import queue

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

def openSerialConnection(portURL):
	"Returns a serial.Serial object, which is file-like"

	portURL = getPort().device
	print("Opening connection to port " + portURL)
	serialConn = serial.Serial(portURL, timeout=PORT_TIMEOUT)

	print("Waiting for data...")
	while not serialConn.in_waiting:
		#print(serialConn.in_waiting)
		time.sleep(0.1)
	print("Connected")
	print("{} bytes waiting".format(serialConn.in_waiting))

	return serialConn



class Packetizer():
	"""Asynchronously polls a file-like object and packetizes it by regex into a Queue"""


	#If we don't find a matching pattern in this many characters, try recovering or error out
	LONGEST_PATTERN = 50  

	#If we lose alignment, try discarding up to this many characters
	MAX_OFFSET_RETRIES = 20 
	
	#How many bytes to read each time through
	AMOUNT_TO_READ = 10 

	def __init__(self, _conn):
		self._inBuffer = b''
		self.packets = queue.Queue()
		self.inputRegex = re.compile(b'\xFF(.)\xAA(.)\xAA\x00')

		self._conn = _conn

		self.thread = threading.Thread(
				target=self.threadRun, 
				name="Packetizer thread", 
				daemon=True)

	def start(self):
		self.thread.start()

	#Pure
	def _tryMatching(reg, buff):
		"""Tries to match reg to the start of buff
		
		Returns (match, restOfBuff)
		If failed to match then returns (None, buff)"""

		m = reg.match(buff)
		if m:
			return m.groups(), buff[m.end():]
		else:
			return None, buff

	def readData(self):
		"Reads a small amount of data from the stream, packetizes if possible, should be called repeatedly"

		#read data
		bytesRead = self._conn.read(Packetizer.AMOUNT_TO_READ)

		#If it timed out and got nothing, assume the worst
		if len(bytesRead) == 0:
			raise IOError("Serial connection lost")

		self._inBuffer += bytesRead


		#match as much text as we can, 
		#put the matching capture groups into the packets queue
		while True:
			groups, self._inBuffer = Packetizer._tryMatching(self.inputRegex, self._inBuffer)

			if groups:
				self.packets.put(groups)
				continue
			#if we didnt match any data
			else:
				#maybe we just need to buffer some more data
				if len(self._inBuffer) < Packetizer.LONGEST_PATTERN:
					break #wait to read more data
				
				#we definitely have enough data, but maybe we're offset wrong
				else:
					oldInBuffer = self._inBuffer #hold onto this for error output

					#chomp off 1 char at a time and hope it works
					for i in range(Packetizer.MAX_OFFSET_RETRIES):
						self._inBuffer = self._inBuffer[1:]
						groups, self._inBuffer = Packetizer._tryMatching(self.inputRegex, self._inBuffer)
						if groups:
							break #break to main parsing loop
					if not groups: #we found nothing
						raise IOError("Invalid data received. Hex: {}".format(repr(oldInBuffer)))

					self.packets.put(groups)
	
	def threadRun(self):
		while True:
			self.readData()
			time.sleep(0.01)
