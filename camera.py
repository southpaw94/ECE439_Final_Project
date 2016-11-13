#!/usr/bin/env python
import cv2
import math
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import pandas as pd
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep
from sqlalchemy import create_engine

# ideas: resize image to something much smaller, with the same height/width ratio as either Pi camera
# or the paper (8.5" x 11")
# if we use a much smaller image, we will have less pixels and therefore less data, and the entire
# process will take a shorter amount of time


# global variables
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
		cv2.imshow('Saved Original', image)
		image = cv2.Canny(image, 125, 175)
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
			        	image[n, o] = 0
					follow_pix(current_pix[0], current_pix[1])



#  function to convert a pixel coordinate into angles for the servos
#  on each joint
def pix_to_ik(px, py, pen_state):

	global angle_array
	global angles_df
	global pix_list_df

	# 1280 is width of image from pi cam, 232.72 is 2 inches (for offset) 
	#  after multiplying by scalar
	cx = (11.0 / width) * (px +(2.0*(width/11.0)))
	# 1024 is height of image from pi cam, -py is to flip axis to Cartesian	
        cy = (8.5 / height) * (-py + height)
	cartesian = [cx, cy]
	# print "cartesian coords = ", cartesian
	
	a1 = 200.0  # measurement in mm for link 1
	a2 = 200.0  # measurement in mm for link 2
	a1 = a1 / 25.4  # convert to inches
	a2 = a2 / 25.4  # convert to inches
	alpha = (math.pow(cx, 2) + math.pow(cy, 2) - math.pow(a1, 2) - math.pow(a2, 2)) / (2 * a1 * a2)
	theta_two = math.atan2(math.sqrt(1 - math.pow(alpha, 2)), alpha)
	
	#  0 <= theta_two <= +180
	# -90 <= theta_one <= +90 
	if (theta_two < 0.0):
		theta_two += math.pi
	elif (theta_two > 180.0):
		theta_two -= math.pi

	k1 = a1 + a2 * math.cos(theta_two)
	k2 = a2 * math.sin(theta_two)
	gamma = math.atan2(k2, k1)
	theta_one = math.atan2(cy, cx) - gamma
	
	if pen_state == True:
		theta_three = 90.0
	elif pen_state == False:
		theta_three = 0.0

	theta_one = round(math.degrees(theta_one))  # convert from rad to deg
	theta_one += 90.0
	theta_two = round(math.degrees(theta_two))  # convert from rad to deg
	angles = [theta_one, theta_two, theta_three]
	angle_array.append(angles)	
	angles_df = pd.DataFrame(angle_array, columns = ['THETA1', 'THETA2', 'THETA3'])
	
	return angles_df

# function to plot points/lines being drawn as they are drawn
def plot_points():

	a1 = 200.0 / 25.4 # link 1 length
	a2 = 200.0 / 25.4 # link 2 length

	x_array = []
	y_array = []

	for q in range(0, len(angle_array)):
		theta_one = (angle_array[q][0]) - 90.0
		theta_one = math.radians(theta_one)
		theta_two = math.radians(angle_array[q][1])
		theta_three = math.radians(angle_array[q][2])
	
		x = a1 * math.cos(theta_one) + a2 * math.cos(theta_one + theta_two)
		y = a1 * math.sin(theta_one) + a2 * math.sin(theta_one + theta_two)
	
		if theta_three == (math.pi / 2):
			x_array.append(x)
			y_array.append(y)

	line = plt.scatter(x_array, y_array, s = 0.2)
	# to change size in above function, add 's = number' to end
	# plt.scatter(x_array, y_array, s = 1)
	plt.axis([0.0, 13.0, 0.0, 8.5])
	plt.show()

	# need to make this function plot continuously over time with a 
	# small delay, to make it appear as if the computer is drawing the 
	# picture along with the robot
	#
	# instead of points, the function should plot continuously from point
	# to point (tiny lines) with a small delay





# take_image()
find_pix('mountain_river.jpg')
plot_points()
print "algorithm has ran its course"
print "now creating sql table"
connection = create_engine('mysql+mysqlconnector://root:passwd@localhost:3306/ECE_439')
angles_df.to_sql(name = 'ANGLES', con = connection, if_exists = 'replace', index_label = 'ID')
print
print
print "angles_df = ", angles_df
print

cv2.waitKey(0)
cv2.destroyAllWindows()


