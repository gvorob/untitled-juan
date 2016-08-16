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
				name="Deframer thread", 
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
		"enqueues any full frames in the input buffer"

		if(not len(self._inBuffer)):
			return

		#If framing error
		if(self._inBuffer[0] != 0):
			#find next frame
			indexOfZero = self._inBuffer.find(b'\x00')
			if(indexOfZero == -1):
				return

			#if found, move up to it
			self._inBuffer = self._inBuffer[indexOfZero:]

		#Extract frames
		while True:
			match = re.match(b'\x00([^\x00]*)\x00', self._inBuffer)
			if not match:
				break

			frameData = match.group(1)
			self.frames.put(self.cobsDecode(frameData))

			#move up to ending zero
			self._inBuffer = self._inBuffer[match.end(1):]

		#cleanup?
		pass

	@classmethod
	def cobsDecode(cls, data):
		"Decodes a COBS-encoded bytes object. Returns result or raises valueerror"
		originaldata = data #hold onto original in case of error

		if(len(data) == 0):
			return b''
		if(b'\x00' in data):
			raise ValueError("Found 0 in COBS data")


		result = b''

		while len(data) > 0:
			#pop off the segment length
			segmentLength = data[0]
			data = data[1:] 

			#works in general case and in special case
			dataBytesToRead = segmentLength - 1

			if dataBytesToRead > len(data):
				remakeData = bytes((segmentLength,)) + data
				raise ValueError("Invalid COBS string: " + originaldata.hex())

			#read in data
			result += data[:dataBytesToRead]
			data = data[dataBytesToRead:]

			#add zero
			if segmentLength != 0xFF:
				result += b'\x00'

		return result[:-1] #testing
	
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
		
