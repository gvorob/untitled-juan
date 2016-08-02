from . import serialtools
from . import packetizer
import queue
import time

BUFFER_AMOUNT = 8

def match(inBuff):
	if(len(inBuff) < BUFFER_AMOUNT):
		return None, inBuff

	beginning, rest = inBuff[:BUFFER_AMOUNT], inBuff[BUFFER_AMOUNT:]

	return beginning.hex(), rest


conn = serialtools.openSerialConnection(serialtools.getPort())
pack = packetizer.Packetizer(conn, match)

pack.start()

while True:
	try:
		print(pack.packets.get_nowait())
	except queue.Empty:
		time.sleep(0.01)
