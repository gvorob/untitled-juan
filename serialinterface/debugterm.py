from . import serialtools
from . import packetizer
import queue
import time

BUFFER_AMOUNT = 12

def match(inBuff):
	if(len(inBuff) < BUFFER_AMOUNT):
		return None, inBuff

	beginning, rest = inBuff[:BUFFER_AMOUNT], inBuff[BUFFER_AMOUNT:]

	formattedPacket = ' '.join([bytes((b,)).hex() for b in beginning])
	return (formattedPacket, rest)


conn = serialtools.openSerialConnection(serialtools.getPort())
pack = packetizer.Packetizer(conn, match)

pack.start()

while True:
	try:
		in_packets = (pack.packets.get_nowait())
		print(in_packets)
	except queue.Empty:
		time.sleep(0.01)
