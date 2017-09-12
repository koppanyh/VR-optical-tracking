#!/usr/bin/env python
import pygame, socket
from pygame.locals import *
from math import *
from time import sleep
pygame.display.init()
screen = pygame.display.set_mode((640,480))
pygame.mouse.set_visible(False)

try:
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
	print 'Failed to create socket'
	exit()

host = "localhost"
	
s.sendto( "setup c1 0 240\n", (host, 32123) )
s.sendto( "setup c2 320 480\n", (host, 32123) )

while 1:
	for event in pygame.event.get():
		if event.type == QUIT: exit()
	screen.fill((0,0,0))
	
	mx,my = pygame.mouse.get_pos()
	
	pygame.draw.circle(screen,(255,255,255),(0,240),3) #cam1
	pygame.draw.line(screen,(255,255,255),(0,240),(640,-80))
	pygame.draw.line(screen,(255,255,255),(0,240),(640,560))
	a = atan2(my-240,mx)
	pygame.draw.line(screen,(100,100,100),(0,240),(800*cos(a),800*sin(a)+240))
	### internal program data ###
	c1ao = 0 #angular offset
	c1po = (0,240) #position offset
	c1 = a #relative angle
	if c1 < -pi/6: c1 = -pi/6
	elif c1 > pi/6: c1 = pi/6
	c1a = c1ao + c1 #absolute angle
	### transmitted program data ###
	c1ta = cos(c1a) #a in x = ta + b
	c1b = c1po[0] #b in x = ta + b
	c1tc = sin(c1a) #c in y = tc + d
	c1d = c1po[1] #d in y = tc + d
	
	s.sendto( "c1 %f %f\n" % (c1ta,c1tc), (host, 32123) )
	
	pygame.draw.circle(screen,(255,255,255),(320,480),3) #cam2
	pygame.draw.line(screen,(255,255,255),(320,480),(80,0))
	pygame.draw.line(screen,(255,255,255),(320,480),(560,0))
	a = atan2(my-480,mx-320)
	pygame.draw.line(screen,(100,100,100),(320,480),(800*cos(a)+320, 800*sin(a)+480))
	### internal program data ###
	c2ao = 3*pi/2 #angular offset
	c2po = (320,480) #position offset
	c2 = a + pi/2 #relative angle
	if c2 < -pi/6: c2 = -pi/6
	elif c2 > pi/6: c2 = pi/6
	c2a = c2ao + c2 #absolute angle
	### transmitted program data ###
	c2ta = cos(c2a) #a in x = ta + b
	c2b = c2po[0] #b in x = ta + b
	c2tc = sin(c2a) #c in y = tc + d
	c2d = c2po[1] #d in y = tc + d
	
	s.sendto( "c2 %f %f\n" % (c2ta,c2tc), (host, 32123) )
	
	pygame.draw.circle(screen,(255,0,0),(mx,my),3) #person
	
	c1bc2b = c1b - c2b
	c1dc2d = c1d - c2d
	t = ((c1dc2d / c2tc) - (c1bc2b / c2ta)) / ((c1ta / c2ta) - (c1tc / c2tc))
	gx = c1ta * t + c1b
	gy = c1tc * t + c1d
	pygame.draw.circle(screen,(255,255,0),(int(gx),int(gy)),1) #calculated position
	
	pygame.display.flip()
	pygame.time.wait(30)

"""
http://members.tripod.com/vector_applications/xtion_of_two_lines/

 x   y     x   y
c1b c1d : c1ta c1tc
c2b c2d : c2ta c2tc

c1ta * t + c1b = c2ta * s + c2b
c1tc * t + c1d = c2tc * s + c2d

(c1ta / c2ta) * t + ((c1b - c2b) / c2ta) = s
(c1tc / c2tc) * t + ((c1d - c2d) / c2tc) = s

(((c1d - c2d) / c2tc) - ((c1b - c2b) / c2ta)) / ((c1ta / c2ta) - (c1tc / c2tc)) = t
(c1ta / c2ta) * t + ((c1b - c2b) / c2ta) = s

x = c1ta * t + c1b
y = c1tc * t + c1d
"""
