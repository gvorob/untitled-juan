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




def drawRectCentered(x, y, r, color=(255, 0, 0, 255)):
	sdl.SDL_SetRenderDrawColor(renderer, *color)
	sdl.SDL_RenderFillRect(renderer, sdl.SDL_Rect(int(x - r), int(y - r), int(2 * r), int(2 * r)))

class State:
	"dummy class for holding properties"
	pass


consts = State()
consts.windowSize = (640, 480)


def resetShip():
	state.ship.pos.x = consts.windowSize[0] / 2
	state.ship.pos.y = consts.windowSize[1] / 2

class Vec2:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __add__(self, other):
		return Vec2(self.x + other.x, self.y + other.y)

	def __mul__(self, other):
		return Vec2(self.x * other, self.y * other)
	def __rmul__(self, other):
		return Vec2(self.x * other, self.y * other)

	def __iter__(self):
		return (self.x, self.y).__iter__()

	def __repr__(self):
		return "Vec2({}, {})".format(self.x, self.y)
	def __str__(self):
		return repr(self)
	
	@classmethod
	def random(cls, mu=0, sigma=1):
		return Vec2(random.normalvariate(mu, sigma), random.normalvariate(mu, sigma))
	

class ExhaustParticleSystem:
	class Particle:
		def __init__(self, pos, vel, radius, ttl):
			self.pos = pos
			self.vel = vel
			self.radius = radius
			self.ttl = ttl

		def update(self, time):
			self.pos += self.vel * time
			self.ttl -= time

		def render(self):
			drawRectCentered(*self.pos, self.radius)

		def isDead(self):
			return self.ttl < 0

	def __init__(self):
		self.particles = []
		self.partialParticles = 0

	def update(self, time):
		for p in self.particles:
			p.update(time)

		self.particles = [p for p in self.particles if not p.isDead()]
		
	def render(self):
		for p in self.particles:
			p.render()

	def makeParticles(self, time, thrust, pos, shipvel, thrustdir):
		rate = thrust * 1

		numToMake = self.partialParticles + time * rate

		radius = 1
		ttl = random.lognormvariate(1, 0.5)
		thrustvel = (thrustdir + Vec2.random(0, 0.1)) * 100
		particleVel = thrustvel + shipvel

		while numToMake > 1:
			self.particles.append(self.Particle(pos, particleVel, radius, ttl))
			numToMake -= 1

		self.partialParticles = numToMake


class Ship:
	width = 50
	height = 60
	speed = 1
	mass = 1
	
	radius = 10
	thrusterDistance = 20
	thrusterRadius = 2

	maxThrust = 300
	gravity = 100

	frictionDynamic = 40
	frictionStatic = 100

	maxangle = math.pi / 4

	def __init__(self, pos):
		self.pos = pos
		self.vel = Vec2(0,0)
		self.angle = 0
		self.exhaust = ExhaustParticleSystem()

	def setThrustDirection(self, setting):
		"setting in [0, 1]"
		self.angle = lerp(-Ship.maxangle, Ship.maxangle, setting)

	def setThrust(self, setting):
		"setting in [0, 1]"
		self.thrust = lerp(0, Ship.maxThrust, setting)

	def getThrustVector(self):
		"returns a Vec2"
		tx = -math.sin(self.angle)
		ty = -math.cos(self.angle)
		return Vec2(tx, ty)


	def isBelowGround(self):
		return self.pos.y > consts.windowSize[1] - 50

	def update(self, time):
		self.vel.y += self.gravity * time

		accel = self.thrust / self.mass
		
		thrustDir = self.getThrustVector()
		self.vel += thrustDir * accel * time

		#print(accel)
		#print(thrustDir)
		#print(self.vel)

		self.pos += self.vel * time

		if self.isBelowGround() and self.vel.y > 0:
			self.pos.y = consts.windowSize[1] - 50
			self.vel.y = 0
			self.vel.x *= 0.8

		self.exhaust.makeParticles(time, self.thrust, self.pos, self.vel, thrustDir * -1)
		self.exhaust.update(time)

	def render(self):
		drawRectCentered(self.pos.x, self.pos.y, Ship.radius)

		#thruster pos 
		thrustVec = self.getThrustVector() 
		thrusterPos = self.pos + (Ship.thrusterDistance * thrustVec * -1)
		
		drawRectCentered(*thrusterPos, Ship.thrusterRadius)

		self.exhaust.render()

	
		
state = State()
state.ship = Ship(Vec2(0,0))
resetShip()



def updateInputAnalog(time):
	state.ship.setThrustDirection(sioInput.analogs[0].value)
	state.ship.setThrust(sioInput.analogs[1].value)
	pass

def updateFrame(time):
	global numIOFramesPastSecond 
	numIOFramesPastSecond += sioInput.lockFrame()

	#updateInputDigital(time)
	updateInputAnalog(time)

	
	ws = consts.windowSize
	ship = state.ship
	ship.update(time)

	#b.x += b.xvel * time
	#b.y += b.yvel * time



	##check wall bounce
	#if b.y + b.radius > ws[1]:
	#	b.y = ws[1] - b.radius
	#	b.yvel *= -1
	#if b.y - b.radius < 0:
	#	b.y = b.radius
	#	b.yvel *= -1


def renderFrame(time):
	#clear screen
	sdl.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
	sdl.SDL_RenderClear(renderer)

	#set color to white
	sdl.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)

	ws = consts.windowSize
 
	state.ship.render()
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
