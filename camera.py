#!/usr/bin/env python
import cv2
import math
import numpy as np
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

GPIO.setmode(GPIO.BCM)
# universal setup for GPIO pin numbering


def find_pix():

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
		image ='lana_bw.jpg'
		image = cv2.imread(image)
		# image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
		image = cv2.resize(image, (220, 170))
		cv2.imshow('Saved Original', image)
		image = cv2.Canny(image, 200, 220)
		cv2.imshow('Saved Edges', image)
	        height, width = image.shape
       		print "image height = ", height
       		print "image width = ", width
		print
		print "image has been read"
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
	cx = (11.0 / width) * (px + (2.0*(width/11.0)-px))
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




find_pix()
connection = create_engine('mysql+mysqlconnector://root:passwd@localhost:3306/ECE_439')
angles_df.to_sql(name = 'ANGLES', con = connection, if_exists = 'replace', index_label = 'ID')
print
print
print "angles_df = ", angles_df
print
# get_pix_saved_image('mountain_river.jpg')
# pix_to_ik(1280, 1024)

cv2.waitKey(0)
cv2.destroyAllWindows()


