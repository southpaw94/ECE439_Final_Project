#!/usr/bin/env python
import cv2
import math
import numpy as np
import scipy as sp
import matplotlib
import matplotlib.pyplot as plt
#matplotlib.use("TkAgg")
import pandas as pd
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep
import time
from sqlalchemy import create_engine

# ideas: resize image to something much smaller, with the same height/width ratio as either Pi camera
# or the paper (8.5" x 11")
# if we use a much smaller image, we will have less pixels and therefore less data, and the entire
# process will take a shorter amount of time


# global variables
image = 0
plot_image = 0
angle_array = []
pix_list = []
pen_down = False
image_processed = False
current_pix = []
angles_df = pd.DataFrame()
height = 0
width = 0

# universal setup for GPIO pin numbering
GPIO.setmode(GPIO.BCM)


def take_image():
	
	print
	print "get ready for the camera to take your picture!"
	print
	sleep(5)
	camera = PiCamera()
	camera.start_preview()
	# give user 10 seconds to get ready for picture
	sleep(10)
	camera.capture('image_captured.jpg')
	camera.stop_preview()
	image_captured = cv2.imread('image_captured.jpg')
	cv2.imshow('Captured Image', image_captured)
	image_captured = cv2.cvtColor(image_captured, cv2.COLOR_RGB2GRAY)
	height_captured, width_captured = image_captured.shape
	cv2.imwrite('image_captured.jpg', image_captured)
	find_pix('image_captured.jpg')

def find_pix(input_image):

	# check if first time through to process image once, otherwise skip this step
	global image
	global pix_list
	global pen_down
	global image_processed
	global current_pix
	global height, width
	global plot_image

	if image_processed == False:
		# image = saved image that we want processed/drawn
		# if you want to draw a test picture, simply replace following line with "image = 'name_of_test_image.jpg'"
		image = input_image
		image = cv2.imread(image)
		print 
		print "image has been read"
		print
		height_original, width_original, color_dimension = image.shape
		print "original height = ", height_original
		print "original width = ", width_original
		print
		# dimensions should match ratio of 8.5" x 11" paper
		# 352 x 272 
		image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
		image = cv2.resize(image, (352, 272))
		# image for plot_points() function; allows us to plot over original image
		plot_image = image
		cv2.imwrite('plot_image.jpg', plot_image)
		cv2.imshow('Saved Original', image)
		image = cv2.Canny(image, 150, 175)
		cv2.imshow('Saved Edges', image)
	        height, width = image.shape
		print "resized image height = ", height
       		print "resized image width = ", width
		print
		image_processed = True	

	print "beginning to look for first white pixel"
	print

	for i in range(1, height):
		for j in range(1, width):
			if image[i, j] != 0:
				pen_down = False
				current_pix = [i, j, pen_down]
				pix_list.append(current_pix)
				# delete already drawn pixels
				image[i, j] = 0
				# make sure we're in the boundaries of the image
				if ((i-1 > 0) and (j-1 > 0) and (i < height-1) and (j < width-1)):
					# check neighborhood (3x3)
					# if white pixel is in neighborhood, call follow_pix( ) with current location
					if (image[i-1,j-1]!=0 or image[i-1,j]!=0 or image[i-1,j+1]!=0 or \
					image[i,j-1]!=0 or image[i,j+1]!=0 or image[i+1,j-1]!=0 or \
					image[i+1,j]!=0 or image[i+1,j+1]!=0): 
						follow_pix(i, j)
					else:
						# if no white pixels in neighborhood, lift pen up until next pixel is found
						pen_down = False

	print "length of pix_list = ", len(pix_list)
	print "found all pixels"
	print
	print "beginning pixel-to-angle function (inverse kinematics)"
	print

	for p in range(0, len(pix_list)):
		px_input = pix_list[p][1]
		py_input = pix_list[p][0]
		pen_state = pix_list[p][2]
		pix_to_ik(px_input, py_input, pen_state)

	


def follow_pix(k, l):

	# (n, o) first time through is the current pixel location (first pixel in line)
	# index through rows and columns of neighborhood matrix (3x3)
	# current pixel here is image(n, o)
	global image
	global pix_list
	global pen_down
	global current_pix

	for n in range(k-1, k+2):
		for o in range(l-1, l+2):
			if ((n < height) and (o < width)):
				if image[n, o] != 0:
					pen_down = True
					current_pix = [n, o, pen_down]
					pix_list.append(current_pix)
					pen_down = False
		        		image[n, o] = 0
					follow_pix(current_pix[0], current_pix[1])

	pen_down = False
	current_pix = [n, o, pen_down]
	pix_list.append(current_pix)
	print
	print
	#print "current_pix = ", current_pix
	print
	print


#  function to convert a pixel coordinate into angles for the servos
#  on each joint
def pix_to_ik(px, py, pen_state):

	global angle_array
	global angles_df
	global pix_list_df

	# 1280 is width of image from pi cam, 232.72 is 2 inches (for offset) 
	#  after multiplying by scalar
	cx = ((px * 11.0) / width) + 4.50
	# 1024 is height of image from pi cam, -py is to flip axis to Cartesian	
        cy = ((-py * 8.5) / height) + 8.5
	cartesian = [cx, cy]
	# print "cartesian coords = ", cartesian
	
	a1 = 200.0  # measurement in mm for link 1
	a2 = 236.0  # measurement in mm for link 2
	a1 = a1 / 25.4  # convert to inches
	a2 = a2 / 25.4  # convert to inches
	alpha = (math.pow(cx, 2) + math.pow(cy, 2) - math.pow(a1, 2) - math.pow(a2, 2)) / (2 * a1 * a2)
	theta_two = math.atan2(math.sqrt(1 - math.pow(alpha, 2)), alpha)
	
	#  0 <= theta_two <= +180
	# -90 <= theta_one <= +90 
	if (theta_two < 0.0):
		theta_two += math.pi
	elif (theta_two > math.pi):
		theta_two -= math.pi

	k1 = a1 + a2 * math.cos(theta_two)
	k2 = a2 * math.sin(theta_two)
	gamma = math.atan2(k2, k1)
	theta_one = math.atan2(cy, cx) - gamma
	
	if (pen_state == True):
		theta_three = 60.0
	elif (pen_state == False):
		theta_three = 0.0

	theta_one = round(math.degrees(theta_one))  # convert from rad to deg
	theta_one += 60.0                           # add +90 so we can 
stick with uint's
	theta_two = round(math.degrees(theta_two))  # convert from rad to deg
	angles = [theta_one, theta_two, theta_three]
	angle_array.append(angles)	
	angles_df = pd.DataFrame(angle_array, columns = ['THETA1', 'THETA2', 'THETA3'])
	
	return angles_df




# function to plot points/lines being drawn as they are drawn in a scatterplot
def plot_points():

	color_array = []
	count = 0
	progress = 0
	plt.axis([0, width, height, 0])
	plt.ion()

	image_2 = plt.imread('plot_image.jpg')
	image_plot = plt.imshow(image_2, cmap = 'gray')
	
	for r in range(1, len(pix_list)-1, 2):
		count += 1
		r_float = float(r) # this necessary so progress != 0.0 every time
		progress = round((100.0 * (r_float / len(pix_list))), 1)
		theta_three = math.radians(angle_array[r][2])

		# keep track of and tell user progress so far 
		if (count % 10 == 0):
			print
			print "\rprogress: ", progress, "%"
			print

		if theta_three == (math.pi / 3):
			print "\rpen_down = true"
			line_color = 'r'
			alpha_val = 1.0
			plot_pen_state = True
		else:
			print "\rpen_down = false"
			line_color = 'w--'
			alpha_val = 0.2
			plot_pen_state = False

		lines = plt.plot([pix_list[r-1][1], pix_list[r][1]], [pix_list[r-1][0], pix_list[r][0]], line_color, alpha = alpha_val)
		lines = plt.plot([pix_list[r][1], pix_list[r+1][1]], [pix_list[r][0], pix_list[r+1][0]], line_color, alpha = alpha_val) 
		plt.draw()





# take_image()

find_pix('mountain_river.jpg')
start_time = time.time()
#find_pix('twocircles.jpg')
exec_time = time.time() - start_time
m, s = divmod(exec_time, 60)
h, m = divmod(m, 60)
print("Executed in %d:%02d:%02d" % (h, m, s))
sleep(5)
# find_pix('lana_bw.jpg')

print "algorithm has ran its course"
print

print "now creating sql table"
connection = create_engine('mysql+mysqlconnector://root:passwd@localhost:3306/ECE_439')
angles_df.to_sql(name = 'ANGLES', con = connection, if_exists = 'replace', index_label = 'ID')

print
print
print "angles_df = ", angles_df
print

print "begin plotting what the robot is drawing"
print
#plot_points()

cv2.waitKey(0)
cv2.destroyAllWindows()


