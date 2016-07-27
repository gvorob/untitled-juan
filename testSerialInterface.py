import serialinterface.serialiointerface as sio
import time

sioInput = sio.SerialIOInterface()

class State:
	pass

state = State()
state.a = 0.
state.vela = 0.
state.b = 0.
state.velb = 0.

consts = State()
consts.jumpvel = 1
consts.grav = -0.1


def updateFrame():
	sioInput.lockFrame()

	if(sioInput.buttons[0].state):
		state.vela = consts.jumpvel
	if(sioInput.buttons[1].state):
		state.velb = consts.jumpvel

	state.a += state.vela
	state.b += state.velb

	state.vela += consts.grav
	state.velb += consts.grav

	if(state.b < 0):
		state.b = 0.
	if(state.a < 0):
		state.a = 0.

def renderFrame():
	framestr = ""
	framestr += ', '.join([str(int(b.state)) for b in sioInput.buttons])

	abstr = list(' ' * ((int(max(state.a, state.b))) + 1))
	abstr[int(state.a)] = 'a'
	abstr[int(state.b)] = 'b'

	framestr += '|' + ''.join(abstr)

	#print("frame")
	print(framestr)
	#print('-' * height)

while True:
	updateFrame()
	renderFrame()
	time.sleep(1. / 30)
