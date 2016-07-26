import serialinterface
import queue
import time


sip = serialinterface.packetizer

conn = sip.openSerialConnection(sip.getPort())

p = sip.Packetizer(conn)
p.start()

while True:
	print('sleeping')
	time.sleep(0.1)

	while True:
		try:
			x = p.packets.get_nowait()
			print(x)
		except queue.Empty:
			break;
	
