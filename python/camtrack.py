#!/usr/bin/env python
#Works by tracking using colors but keeping a small bounding box around last known position to filter out background stuff
#throw motion detection to find moving target vs background

import pygame, os, socket
import pygame.camera
from pygame.locals import *
from math import *
pygame.display.init()
pygame.camera.init()
pygame.font.init()
font = pygame.font.Font(None,20)
clock = pygame.time.Clock()

#initialize camera
camlist = pygame.camera.list_cameras()
if camlist:
	cam = pygame.camera.Camera(camlist[0],(640,480),"RGB")
else:
	print "No cameras found"
	exit()
cam.start()
csize = cam.get_image().get_size()

screen = pygame.display.set_mode(csize)

#initialize parameters
camdat = {
	"name": "1",
	#"color": (255.0,253.0,255.0)
	"fov": 60.0,
	"position": (0.0,100.0),
	"angle": 0.0,
	"thresh": (10.0,10.0,10.0),
	"host": "localhost",
	"port": 32123
}
if os.path.exists("camdat.txt"):
	f = open("camdat.txt","r")
	x = f.read()
	f.close()
	x = x.replace("\r","").split("\n")
	for y in x:
		y = [z.strip() for z in y.split(":") if z != ""]
		if len(y) < 2: continue
		if ',' in y[1]: y[1] = tuple([float(z) for z in y[1].split(',')])
		try: y[1] = float(y[1])
		except: pass
		camdat[y[0]] = y[1]
camdat["port"] = int(camdat["port"])
camdat["angle"] = radians(camdat["angle"])
camdat["fov"] = radians(camdat["fov"])

app = camdat["fov"] / csize[0]

#initialize udp client socket
try: s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
	print 'Failed to create socket'
	exit()
s.sendto( "setup %s %d %d\n" % (camdat["name"], camdat["position"][0], camdat["position"][1]), (camdat["host"], camdat["port"]) )

#define simple event handler
def events():
	for event in pygame.event.get():
		if event.type == QUIT: exit()
		if event.type == KEYDOWN:
			if event.key == K_SPACE or event.key == K_ESCAPE: exit()

#get target color if not defined in settings
if "color" in camdat: targetcol = camdat["color"]
else:
	for x in range(75): #get target color
		events() #handle events
		img = pygame.transform.flip(cam.get_image(),True,False) #get image and mirror it
		screen.blit(img,(0,0)) #blit to screen
		pygame.draw.rect(screen,(255,0,0),(csize[0]/2-12,csize[1]/2-12,24,24),2) #draw red target box
		pygame.display.flip()
		pygame.time.wait(30)
	targetcol = pygame.transform.average_color(img,(csize[0]/2-12,csize[1]/2-12,24,24)) #find target color
	print "Target color: ",targetcol

coord = (csize[0]/2,csize[1]/2) #coord of last known target position
oldcoord = (csize[0]/2,csize[1]/2) #previous target coordinate
thsh = camdat["thresh"]
thresh = pygame.Surface(csize) #image threshold surface
crop = pygame.Surface(csize) #cropped surface for easier detection
g = 50 #size of scanning area

while 1: #track the target
	events() #handle events
	img = cam.get_image()
	#img = pygame.transform.flip(img,True,False) #get image and mirror it
	
	pygame.transform.threshold(thresh,img,targetcol,thsh,(0,0,0),1) #run threshold for certain color
	screen.blit(thresh,(0,0)) #blit thresholded image to screen
	
	crop.fill((0,0,0)) #turn cropped surface black
	crop.blit(img,(coord[0]-g,coord[1]-g),(coord[0]-g,coord[1]-g,g*2,g*2)) #show only target area
	
	mask = pygame.mask.from_threshold(crop,targetcol,thsh) #make thresholded image mask
	
	connected = mask.connected_component() #get mask blobs
	if connected.count() > 100: #if blob big enough
		coord = connected.centroid() #find center of blob
		if coord != (0,0): oldcoord = coord #set backup coords
		else: coord = oldcoord #set to old coordinates if not correct
		rct = pygame.draw.rect(screen,(255,0,0),(coord[0]-g,coord[1]-g,g*2,g*2),2) #draw red box
	else:
		rct = pygame.draw.rect(screen,(255,255,0),(coord[0]-g,coord[1]-g,g*2,g*2),2) #draw red box
	#if rct.colliderect(pygame.draw.rect(screen,(255,0,0),(630,0,10,10))): exit() #exit if touch red square
	
	screen.set_at(coord,(255,0,0))
	c1 = (coord[0] - (csize[0] / 2)) * app + camdat["angle"]
	s.sendto( "%s %f %f\n" % (camdat["name"], cos(c1), sin(c1)), (camdat["host"], camdat["port"]) )
	
	maxx = 0 #calculate size of scanning area
	minx = csize[0]
	maxy = 0
	miny = csize[1]
	for x in connected.outline():
		if x[0] > maxx: maxx = x[0]
		if x[0] < minx: minx = x[0]
		if x[1] > maxy: maxy = x[1]
		if x[1] < miny: miny = x[1]
	m = int(max(maxx-minx,maxy-miny) / 1)
	m = max(m,10)
	if g > m: g -= 5
	if m > g: g += 10
	g = max(g,50)
	
	screen.blit(pygame.transform.scale(img,(100,csize[1]*100/csize[0])),(0,csize[1]-csize[1]*100/csize[0])) #display tiny image at bottom left
	screen.blit(font.render(str(clock.get_fps()),1,(0,255,0)),(0,0)) #show fps
	pygame.display.flip()
	clock.tick(0)

"""
app = fov / width

c1 = (xcoord - (width / 2)) * app + camdat["angle"]

	### transmitted program data ###
	c1ta = cos(c1a) #a in x = ta + b
	c1tc = sin(c1a) #c in y = tc + d
"""
