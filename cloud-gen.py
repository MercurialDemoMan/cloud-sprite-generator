#!/usr/bin/python

import sys
import os
import random
import math
from multiprocessing import Process, Lock
from timeit import default_timer as timer

from PIL import Image

# constants and factors which generate the cloud
CLOUD_RADIUS     	 = 500
CLOUD_FLUFFYNESS_MAG = 100
CLOUD_FLUFFYNESS_MIN = 40
CLOUD_SPREAD         = 100
CLOUD_DENSITY    	 = 16



def smooth_noise(x, y, noise):
	"""smooth noise values in "noise" buffer based on its neighbours
	source: https://lodev.org/cgtutor/randomnoise.html
	"""


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



def turbulence(x, y, size, noise):
	"""combine multiple scales of smooth noises
	source: https://lodev.org/cgtutor/randomnoise.html
	"""

	value     = 0.0
	size      = float(size)
	init_size = size

	while(size >= 1):
		value += smooth_noise(x / size, y / size, noise) * size
		size  /= 2.0

	return 128.0 * value / init_size



def clamp(x, min, max):
	"""clamp function
	"""
	if(x < min): x = min
	if(x > max): x = max
	return x



def gen_cloud(out_path, lock):
	"""generate cloud
	based on global constants generate cloud image
	"""

	noise = [[random.random() for x in range(CLOUD_RADIUS)] for y in range(CLOUD_RADIUS)]

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
			val = (val / 255) * (turbulence(x, y, 64, noise) / 255)
			out.putpixel((x, y), (255, 255, 255, int(clamp(val * 255, 0.0, 255.0))))

		lock.acquire()
		print("gen_cloud() log: [" + out_path + "] " + str(y) + "/" + str(CLOUD_RADIUS))
		lock.release()

	# write image on disk
	out.save(out_path)

	# log successful generation
	lock.acquire()
	print("gen_cloud() log: generated [" + out_path + "] cloud")
	lock.release()



if __name__ == "__main__":
	"""main program
	"""
	# check arguments
	if(len(sys.argv) != 2):
		print("usage: cloud-gen.py [number of clounds to generate]")
		sys.exit(1)

	# create folder to store all clouds
	try:
		os.mkdir("clouds")
	except OSError:
		pass

	# generate paths
	out_names = ["clouds/cloud" + str(x) + ".png" for x in range(0, int(sys.argv[1]))]

	# manage multiprocessing
	cloud_processes = []

	# calculate elapsed time
	start = timer()

	# main loop
	for i in range(int(sys.argv[1])):
		# create lock for printing log
		print_lock = Lock()

		# log start of process
		print_lock.acquire()
		print("__main__ log: Start generating cloud [clouds/cloud" + str(i) + ".png]")
		print_lock.release()

		
		# start the generation
		p = Process(target = gen_cloud, args = ("clouds/cloud" + str(i) + ".png", print_lock))
		p.start()

		# keep track of all processes we created
		cloud_processes.append(p)

	# wait for every process
	for i in cloud_processes:
		i.join()

	# calculate and print elapsed time
	end = timer()
	print("__main__ log: elapsed time: " + str(end - start) + "s")


