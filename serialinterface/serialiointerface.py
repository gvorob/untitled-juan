"""High level interface to serial input

Manages creation/handling of a packetizer to read data, then exposes
methods to poll the state of a given button frame by frame.

"""

from . import packetizer
from . import serialtools
import queue
import time
import re

ANALOG_MAX = 1023


#TODO: generalize framework so buttons aren't hardcoded
#TODO: add handling for stale frames (i.e. no new input)
#TODO: make it so that fatal errors in packetizer are actually fatal

serialRegexFirstPass = re.compile(b"\xA1.(?P<numDigital>.)(?P<numAnalog>.)..*\xA2.*\xA3", re.DOTALL)

def MATCHER(buffIn):
	"""Matches a packet from buffIn, for Packetizer

	buffIn is a bytes object
	returns (packetData, restOfBuffIn) if match found
	returns (None, buffIn) otherwise
	
	Packet format is as follows:

	
	S1 __ ND NA __ [D,...] S2 [AH AL, ...] S3

	where S1-S3 are separators \xA1, \xA2, \xA3
	__ is any byte (currently unused)
	ND is the number of digital bits as inputs
	NA is the number of analog inputs
	[D, ...] is ceil(ND / 8) bytes containing digital inputs
	[AH AL,...] is NA pairs of bytes containing analog inputs
		in the range [0, 1023]
	"""

	
	#extract lengths
	match = serialRegexFirstPass.match(buffIn)
	if not match:
		return None, buffIn


	#calculate offsets
	numDigitalBits = int(match.group('numDigital')[0])
	numDigitalBytes = (numDigitalBits // 8) + 1
	numAnalogBytes =  int(match.group('numAnalog')[0]) * 2

	firstDigital = 5 #offset
	firstAnalog = firstDigital + numDigitalBytes + 1 #end of digital + separator
	totalLength = firstAnalog + numAnalogBytes + 1 #end of analog + terminator


	#simple validation
	inputInvalid = (
			(len(buffIn) < totalLength) or
			(buffIn[firstAnalog - 1] != 0xA2) or
			(buffIn[totalLength - 1] != 0xA3))
	if inputInvalid:
		return None, buffIn


	#extract binary data
	digitalBytes = buffIn[firstDigital:firstDigital + numDigitalBytes]
	analogBytes = buffIn[firstAnalog:firstAnalog + numAnalogBytes]

	digitalBits = []
	for inByte in digitalBytes:
		inBits = [bool((inByte >> i)  & 1) for i in range(8)]
		digitalBits.extend(inBits)
	digitalBits = digitalBits[:numDigitalBits] #discard excess

	#stitch together analog data
	assert(len(analogBytes) % 2 == 0)
	analogValues = []
	for i in range(len(analogBytes))[::2]:
		intValue = int(analogBytes[i]) * 256 + int(analogBytes[i + 1])
		floatValue = intValue / ANALOG_MAX
		analogValues.append(floatValue)
		
	
	result = (digitalBits, analogValues)
	return (result, buffIn[totalLength:])



class DigitalIn:
	".value: True or False"
	def __init__(self):
		self.value = False
	
	def __str__(self):
		return "Digital: " + ('1' if self.value else '0')

class AnalogIn:
	".value: float in [0, 1]"

	def __init__(self):
		self.value = 0

	def __str__(self):
		return "Analog: {:4.2f}".format(self.value)

class SerialIOInterface:
	"Opens a serial connection, exposes named buttons"

	def __init__(self):
		portURL = serialtools.getPort()
		conn = serialtools.openSerialConnection(portURL)

		self._packetizer = packetizer.Packetizer(conn, MATCHER)
		self._packetizer.start()

		self.digitals = [DigitalIn() for i in range(4)]
		self.analogs = [AnalogIn() for i in range(4)]


	def lockFrame(self):
		"""Makes state consistent for a frame

		Should be called at the start of every frame
		Reads buffered data from its packetizer

		Returns number of packets consumed
		"""

		numConsumed = 0
		#consume all packets until the queue is empty
		while True:
			try:
				p = self._packetizer.packets.get_nowait()
				numConsumed += 1
				self.consumePacket(p)
			except queue.Empty:
				if numConsumed == 0:
					print("Error: stale frame (in SerialIOInterface)")
				break
		return numConsumed

	def consumePacket(self, packet):
		"""Consume a packet and use it to update its state
		
		Packets are tuples of capture groups from packetizer regex"""
		#print("Consuming packet:", packet)

		digitals, analogs = packet

		#set my values to match the packet
		for i, d in enumerate(digitals):
			self.digitals[i].value = d

		for i, a in enumerate(analogs):
			self.analogs[i].value = a

		#print("Button state:", stateBits)

	def __str__(self):
		return str([list(map(str, self.digitals)), list(map(str, self.analogs))])



if __name__ == '__main__':
	import time

	print("Testing serialiointerface.py")

	#               HDR  ... #D  #A  ... D1-8 SEP A1H A1L A2H A2L CKSM
	print(MATCHER(b"\xA1\x00\x04\x02\x00\x15\xA2\x00\x00\x03\xFF\xA3"))
	print("The above should be (([T F T F], [0, 1023]), b'')")

	print("testing it for reals")
	s = SerialIOInterface()

	while True:
		s.lockFrame()
		print(str(s))
		time.sleep(0.2)
