import serialinterface.serialiointerface as sio
import time
import sdltest.sdlaccess as sdl
import math
import random

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

def updateFrame(time):
	sioInput.lockFrame()

	if(sioInput.buttons[0].state):
		state.leftPaddle.move(1, time)
	if(sioInput.buttons[1].state):
		state.leftPaddle.move(-1, time)
	if(sioInput.buttons[3].state):
		state.rightPaddle.move(1, time)
	if(sioInput.buttons[2].state):
		state.rightPaddle.move(-1, time)

	
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





window, renderer = sdl.init(b"Test window please ignore", *consts.windowSize)
numframes = 0

running = True
while running:
	numframes += 1

	events = sdl.sdl2.ext.get_events()
	for e in events:
		if e.type == sdl.SDL_QUIT:
			running = False
			continue
		if e.type in (sdl.SDL_MOUSEMOTION, sdl.SDL_MOUSEBUTTONDOWN, sdl.SDL_MOUSEBUTTONUP):
			#ignore mouseevents
			break
		else:
			print("Unhandled event type " + sdl.eventName[e.type])
	

	sdl.SDL_SetWindowTitle(window, str(numframes).encode('ascii'))

	time = 20
	updateFrame(time / 1000)
	renderFrame(time / 1000)
	sdl.SDL_Delay(time)
	
print("Exiting")

sdl.SDL_Quit()
