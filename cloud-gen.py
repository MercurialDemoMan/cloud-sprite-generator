#!/usr/bin/python

import sys
import os
import random
import math

from PIL import Image

# constants and factors which generate the cloud
CLOUD_RADIUS     	 = 500
CLOUD_FLUFFYNESS_MAG = 100
CLOUD_FLUFFYNESS_MIN = 40
CLOUD_SPREAD         = 100
CLOUD_DENSITY    	 = 16

# create noise buffer
noise = [[0 for x in range(CLOUD_RADIUS)] for y in range(CLOUD_RADIUS)]


# smooth noise values in "noise" buffer based on its neighbours
# source: https://lodev.org/cgtutor/randomnoise.html
def smooth_noise(x, y):

	fract_x = x - int(x)
	fract_y = y - int(y)

	x1 = (int(x) + CLOUD_RADIUS) % CLOUD_RADIUS
	y1 = (int(y) + CLOUD_RADIUS) % CLOUD_RADIUS

	x2 = (x1 + CLOUD_RADIUS - 1) % CLOUD_RADIUS
	y2 = (y1 + CLOUD_RADIUS - 1) % CLOUD_RADIUS

	value = 0
	value += (fract_x *       fract_y *       noise[y1][x1])
	value += ((1 - fract_x) * fract_y *       noise[y1][x2])

	value += (fract_x *       (1 - fract_y) * noise[y2][x1])
	value += ((1 - fract_x) * (1 - fract_y) * noise[y2][x2])

	return value


# combine multiple scales of smooth noises
# source: https://lodev.org/cgtutor/randomnoise.html
def turbulence(x, y, size):

	value     = 0.0
	size      = float(size)
	init_size = size

	while(size >= 1):
		value += smooth_noise(x / size, y / size) * size
		size  /= 2.0

	return 128.0 * value / init_size


# clamp function, duh..
def clamp(x, min, max):
	if(x < min): x = min
	if(x > max): x = max
	return x


# generate cloud based on constants defined in header
def gen_cloud(out_path):

	# generate noise
	for y in range(0, CLOUD_RADIUS):
		for x in range(0, CLOUD_RADIUS):
			noise[y][x] = random.random()

	# create random circles buffer
	# which will act as boundary 
	# to our smooth noise
	circles = [[0.0 for j in range(3)] for i in range(CLOUD_DENSITY)]

	# generate random circles
	for i in range(CLOUD_DENSITY):
		circles[i][0] = CLOUD_RADIUS / 2.0 + (random.random() * 2.0 - 1.0) * CLOUD_SPREAD	# x
		circles[i][1] = CLOUD_RADIUS / 2.0 + (random.random() * 2.0 - 1.0) * CLOUD_SPREAD	# y
		circles[i][2] = CLOUD_FLUFFYNESS_MIN + random.random() * CLOUD_FLUFFYNESS_MAG		# radius

	# create output image
	out = Image.new("RGBA", (CLOUD_RADIUS, CLOUD_RADIUS))

	# write data to image
	for y in range(0, CLOUD_RADIUS):
		for x in range(0, CLOUD_RADIUS):
			
			val = 0

			# choose which circle will bound the current pixel
			# cloud with highest density in current position wins
			for i in range(CLOUD_DENSITY):
				dx   = x - circles[i][0]
				dy   = y - circles[i][1]
				val  = max(val, circles[i][2] - math.sqrt(dx * dx + dy * dy))

			# smooth out noise data, bound it with circles and write it to image
			val = (val / 255) * (turbulence(x, y, 64) / 255)
			out.putpixel((x, y), (255, 255, 255, int(clamp(val * 255, 0.0, 255.0))))

	# write image on disk
	out.save(out_path)

	print("gen_cloud() log: generated [" + out_path + "] cloud")


####################
# main program
####################

# check arguments
if(len(sys.argv) != 2):
	print("usage: cloud-gen.py [number of clounds to generate]")
	sys.exit(1)

# create folder to store all clouds
try:
	os.mkdir("clouds")
except OSError:
	pass

out_names = ["clouds/cloud" + str(x) + ".png" for x in range(0, int(sys.argv[1]))]

for i in range(int(sys.argv[1])):
	gen_cloud("clouds/cloud" + str(i) + ".png")


