import sys
import time
import re
import threading
import queue
import time


#TODO: add packet format customization
#TODO: expose any exceptions encountered to other threads using this
class Packetizer():
	"""Asynchronously polls a file-like object and packetizes it by regex into a Queue"""


	#If we don't find a matching pattern in this many characters, try recovering or error out
	LONGEST_PATTERN = 50  

	#If we lose alignment, try discarding up to this many characters
	MAX_OFFSET_RETRIES = 20 
	
	#How many bytes to read each time through
	AMOUNT_TO_READ = 10 

	#How long to sleep between reads
	THREADED_SLEEP_TIME = 0.01

	def __init__(self, _conn):


		self._inBuffer = b''
		self.packets = queue.Queue()
		#regex newline transmitted as data
		self.inputRegex = re.compile(b'\xFF(.)\xAA(.)\xAA\x00', 
									 re.MULTILINE | re.DOTALL)

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
		"Reads a small amount of data from the stream, should be called repeatedly"

		#read data
		bytesRead = self._conn.read(Packetizer.AMOUNT_TO_READ)

		#If it timed out and got nothing, assume the worst
		if len(bytesRead) == 0:
			raise IOError("Serial connection lost")

		self._inBuffer += bytesRead


	def matchData(self):
		"packetizes as much data as possible from the input buffer"

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
				
				#we definitely have enough data, something went wrong
				else:
					self.recoverFromInvalidInput()
					#only returns on success
	
	def recoverFromInvalidInput(self):
		"""Try to recover by discarding some input

		We have enough data in the buffer that we should definitely
		have a full packet. Try discarding one character at a time
		up to MAX_OFFSET_RETRIES and hope that we match something
		
		Else raise IOError
		"""

		oldInBuffer = self._inBuffer #hold onto this for error output

		#chomp off 1 char at a time and hope it works
		print("Invalid serial input, trying to recover by discarding input")
		for i in range(Packetizer.MAX_OFFSET_RETRIES):
			print(self._inBuffer)
			self._inBuffer = self._inBuffer[1:]
			groups, self._inBuffer = Packetizer._tryMatching(self.inputRegex, self._inBuffer)
			print(self._inBuffer)
			print('---')
			if groups:
				print("Successfully recovered by discarding " + str(i + 1) + " chars")
				return #return to main parsing loop
		if not groups: #we found nothing
			raise IOError("Invalid data received. Hex: {}".format(repr(oldInBuffer)))

		self.packets.put(groups)
	
	def threadRun(self):
		"Calls readdata repeatedly, to be run from Thread"
		while True:
			self.readData()
			self.matchData()
			time.sleep(Packetizer.THREADED_SLEEP_TIME)
