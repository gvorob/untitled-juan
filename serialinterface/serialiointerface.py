"""High level interface to serial input

Manages creation/handling of a packetizer to read data, then exposes
methods to poll the state of a given button frame by frame.

"""

from . import packetizer
from . import serialtools
import queue
import time

class Button:
	def __init__(self):
		self.state = False



#TODO: generalize framework so buttons aren't hardcoded
#TODO: add handling for stale frames (i.e. no new input)
class SerialIOInterface:
	"Opens a serial connection, exposes named buttons"

	def __init__(self):
		portURL = serialtools.getPort()
		conn = serialtools.openSerialConnection(portURL)

		self._packetizer = packetizer.Packetizer(conn, packetizer.OLD_MATCHER)
		self._packetizer.start()

		self.buttons = [Button() for i in range(4)]


	def lockFrame(self):
		"""Makes state consistent for a frame

		Should be called at the start of every frame
		Reads buffered data from its packetizer
		"""

		anyConsumed = False
		#consume all packets until the queue is empty
		while True:
			try:
				p = self._packetizer.packets.get_nowait()
				anyConsumed = True
				self.consumePacket(p)
			except queue.Empty:
				if not anyConsumed:
					print("Error: stale frame (in SerialIOInterface)")
				break

	def consumePacket(self, p):
		"""Consume a packet and use it to update its state
		
		Packets are tuples of capture groups from packetizer regex"""
		#print("Consuming packet:", p)
		stateByte = p[0][0] #first byte of first bytestring
		stateBits = [bool((stateByte >> i)  & 1) for i in range(8)]

		for button, newState in zip(self.buttons, stateBits):
			button.state = newState

		#print("Button state:", stateBits)


