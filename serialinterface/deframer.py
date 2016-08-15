import sys
import time
import re
import threading
import queue
import time


#TODO: expose any exceptions encountered to other threads using this

class Deframer():
	"""Polls a file like object asynchronously, extracts and de-COBSses frames into a queue

	create this on a stream, then call start

	decodes frames between 0-bytes as COBS encoded

	this will put bytes into the self.frames queue
	"""


	#If we don't find a matching pattern in this many characters, try recovering or error out
	LONGEST_PATTERN = 50  
	
	#How many bytes to read each time through
	AMOUNT_TO_READ = 10 

	#How long to sleep between reads
	THREADED_SLEEP_TIME = 0.001 
	

	def __init__(self, conn):
		"""Initializes deframer

		Reads data from input stream conn.
		Matches frames off it

		Note: you must call .start() on this deframer to start it
		listening
		"""

		self._inBuffer = b''
		self.frames = queue.Queue()

		self._conn = conn

		self.thread = threading.Thread(
				target=self.threadRun, 
				name="Packetizer thread", 
				daemon=True)


	def start(self):
		self.thread.start()



	def readData(self):
		"Reads a small amount of data from the stream, should be called repeatedly"

		#read data
		bytesRead = self._conn.read(Deframer.AMOUNT_TO_READ)

		#If it timed out and got nothing, assume the worst
		if len(bytesRead) == 0:
			raise IOError("Serial connection lost")

		self._inBuffer += bytesRead


	def matchData(self):
		"packetizes as much data as possible from the input buffer"

		#match as much text as we can, 
		#put the matching capture groups into the frames queue
		while True:
			#print(self._inBuffer)
			#we are in sync
			if(self._inBuffer[0] == 0):
				match = re.match(b'\x00([^\x00]*)\x00', self._inBuffer)

				if match:
					self.frames.put(match.group(1))
					#move up to ending zero
					self._inBuffer = self._inBuffer[match.end(1):]
				else:
					break
			#if out of sync discard until we see a zero
			else:
				#discard data up to zero
				indexOfZero = self._inBuffer.find(b'\x00')
				self._inBuffer = self._inBuffer[indexOfZero:]

				#raise IOError("Invalid data received. Hex: {}".format(repr(inbuffer)))

	
	def threadRun(self):
		"Calls readdata repeatedly, to be run from Thread"
		while True:
			self.readData()
			self.matchData()
			time.sleep(Deframer.THREADED_SLEEP_TIME)

#debugging code
if __name__ == '__main__':
	print("Testing Deframer")

	import serialtools
	
	port = serialtools.getPort()
	conn = serialtools.openSerialConnection(port)


	f = Deframer(conn)
	f.start()

	while True:
		try:
			frame = f.frames.get_nowait()
			print(' '.join([bytes([b]).hex() for b in frame]))
		except queue.Empty:
			time.sleep(0.01)
			pass
		
