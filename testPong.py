
import serialinterface.serialiointerface as sio
import time
import sdltest.sdlaccess as sdl
import math
import random

FPS_TARGET = 60

sioInput = sio.SerialIOInterface()

def lerp(a, b, n):
	return a * (1-n) + b * n
def clamp(n, a, b):
	return min(max(n, a), b)
#eases n from 0 to 1
def ease(n):
	n = clamp(n, 0, 1)
	return -0.5 * math.cos(n * math.pi) + 0.5

def randSign():
	return random.randint(0, 1) * 2 - 1





class State:
	"dummy class for holding properties"
	pass


consts = State()
consts.windowSize = (640, 480)
consts.ballRadius = 20


def resetBall():
	state.ball.x = consts.windowSize[0] / 2
	state.ball.y = consts.windowSize[1] / 2
	state.ball.xvel = 400 * randSign()
	state.ball.yvel = random.random() * 200 - 100
	state.ball.radius = consts.ballRadius



class Paddle:
	width = 50
	height = 60
	speed = 1

	def __init__(self, side):
		self.trackPos = 0

		if side == 'L':
			self.x = 0
			self.normal = 1
		elif side == 'R':
			self.x = consts.windowSize[0] - Paddle.width
			self.normal = -1
		else:
			raise ValueError('Paddle can only be on L or R side')

	def getTop(self):
		return lerp(0, consts.windowSize[1] - Paddle.height, self.trackPos)
	def getCenter(self):
		return self.getTop() + Paddle.height / 2
	def getBottom(self):
		return self.getTop() + Paddle.height

	def getSDLRect(self):
		ws = consts.windowSize
		yCoord = int(self.getTop())
		return sdl.SDL_Rect(self.x, yCoord, Paddle.width, Paddle.height)

	def move(self, direction, time):
		self.trackPos += direction * time * Paddle.speed
		self.trackPos = clamp(self.trackPos, 0, 1)
	
	def moveTo(self, position):
		self.trackPos = position

	def testIntersect(self, ball):
		"return true if ball should bounce here"

		balldir = 1 if ball.xvel > 0 else -1
		paddleSurfX = self.x if self.normal < 0 else Paddle.width

		#if going in the wrong direction to bounce, return
		if balldir * self.normal > 0:
			return False

		#If it hasn't reached the paddle yet, return
		if self.normal < 0: #right paddle
			if(ball.x + ball.radius) < paddleSurfX:
				return False
		else: #left paddles
			if(ball.x - ball.radius) > paddleSurfX:
				return False

		#check if it hit us
		return (ball.y + ball.radius > self.getTop() and 
				ball.y - ball.radius < self.getBottom())

	
	def getSpin(self, ball):
		"""Returns how much the ball should spin (-1 to 1)

		will be called when an intersect occurs to determine new yvel"""

		#
		maxRange = Paddle.height / 2 + ball.radius
		return (ball.y - self.getCenter()) / maxRange
		
state = State()
state.leftPaddle = Paddle('L')
state.rightPaddle = Paddle('R')
state.ball = State()
resetBall()

def bounce(spin):
	"""adds spin to ball, reverse xvel of ball
	
	spin in -1 to 1"""

	state.ball.yvel += spin * abs(spin) * 200
	state.ball.xvel *= -1

def ballOut(side):
	print('ball out: ', str(side))
	resetBall()

def updateInputDigital(time):
	if(sioInput.digitals[0].value):
		state.leftPaddle.move(1, time)
	if(sioInput.digitals[1].value):
		state.leftPaddle.move(-1, time)
	if(sioInput.digitals[3].value):
		state.rightPaddle.move(1, time)
	if(sioInput.digitals[2].value):
		state.rightPaddle.move(-1, time)

def updateInputAnalog(time):
	state.leftPaddle.moveTo(1 - sioInput.analogs[0].value)
	state.rightPaddle.moveTo(1 - sioInput.analogs[1].value)

def updateFrame(time):
	global numIOFramesPastSecond 
	numIOFramesPastSecond += sioInput.lockFrame()

	#updateInputDigital(time)
	updateInputAnalog(time)

	
	#update ball
	ws = consts.windowSize
	b = state.ball
	br = consts.ballRadius

	#move ball
	b.x += b.xvel * time
	b.y += b.yvel * time

	#check scored
	if b.x - br > ws[0]:
		ballOut(1)
	if b.x + br < 0:
		ballOut(0)

	#check paddle bounce
	if(state.leftPaddle.testIntersect(b)):
		bounce(state.leftPaddle.getSpin(b))
	if(state.rightPaddle.testIntersect(b)):
		bounce(state.rightPaddle.getSpin(b))

	#check wall bounce
	if b.y + b.radius > ws[1]:
		b.y = ws[1] - b.radius
		b.yvel *= -1
	if b.y - b.radius < 0:
		b.y = b.radius
		b.yvel *= -1


def renderFrame(time):
	#clear screen
	sdl.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
	sdl.SDL_RenderClear(renderer)

	#set color to white
	sdl.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)

	#render paddles
	ws = consts.windowSize
	sdl.SDL_RenderFillRect(renderer, state.leftPaddle.getSDLRect())
	sdl.SDL_RenderFillRect(renderer, state.rightPaddle.getSDLRect())
 
	#render ball
	bx = int(state.ball.x) - consts.ballRadius
	by = int(state.ball.y) - consts.ballRadius
	sdl.SDL_RenderFillRect(renderer, sdl.SDL_Rect(bx, by, 2 * consts.ballRadius, 2 * consts.ballRadius))
	


	sdl.SDL_RenderPresent(renderer)



running = True

def tickFrame(time):
	"""Handle events, update, and render

	time: elapsed time in seconds since last tick"""

	global running

	#print("Getting events...", end='')

	events = sdl.sdl2.ext.get_events()
	for e in events:
		if e.type == sdl.SDL_QUIT:
			print("Quitting")
			running = False
			return
		if e.type in (sdl.SDL_MOUSEMOTION, sdl.SDL_MOUSEBUTTONDOWN, sdl.SDL_MOUSEBUTTONUP):
			#ignore mouseevents
			break
		else:
			print("Unhandled event type " + sdl.eventName[e.type])
	


	#print("Updating...", end='')
	updateFrame(time)

	#print(" Rendering...", end='')
	renderFrame(time)

	#print(" Done.")





#create window
window, renderer = sdl.init(b"Test window please ignore", *consts.windowSize)

#framerate 
frameTimeTarget = 1 / FPS_TARGET
sdl.SDL_Delay(int(frameTimeTarget * 1000))

#fps counting
lastFPSSecond = sdl.sdlGetTime()
numFramesPastSecond = 0
numIOFramesPastSecond = 0
frameRate = 0
ioRate = 0

#absolute frameNumber
frameNumber = 0

while running:
	frameNumber += 1
	numFramesPastSecond += 1

	frameStartTime = sdl.sdlGetTime()

	#Do all the work
	tickFrame(frameTimeTarget)	
	if not running:
		break

	#Calculate how much longer to wait
	frameEndTime = sdl.sdlGetTime()
	frameTime = frameEndTime - frameStartTime
	remainingTime = frameTimeTarget - frameTime


	#calculate FPS
	if frameEndTime > lastFPSSecond + 1:
		frameRate = numFramesPastSecond
		ioRate = numIOFramesPastSecond
		numFramesPastSecond = 0
		numIOFramesPastSecond = 0
		lastFPSSecond += 1

	sdl.SDL_SetWindowTitle(window, str("FPS: {:3d} - IOPS: {:3d}".format(frameRate, ioRate)).encode('ascii'))

	if(remainingTime > 0):
		#print("Delaying..." + str(int(remainingTime * 1000)), end='')
		sdl.SDL_Delay(int(remainingTime * 1000))
		#print("Done.")
	
print("Exiting")

sdl.SDL_Quit()
