#!/usr/bin/env python
import cv2
import math
import numpy as np
import scipy as sp
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
import pandas as pd
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep
from sqlalchemy import create_engine

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
	process_image('image_captured.jpg')




def process_image(process_input):

	global image
	global image_processed
	global height, width
	global plot_image

	# check if first time through process_image, otherwise skip this step
	if image_processed == False:
		# image = saved image that we want processed/drawn
		# if you want to draw a test picture, simply replace following line with "image = 'name_of_test_image.jpg'"
		image = cv2.imread(process_input)
		print 
		print "image has been read"
		print
		height_original, width_original, color_dimension = image.shape
		print "original height = ", height_original
		print "original width = ", width_original
		print
		# dimensions should match ratio of 8.5" x 11" paper
		# 352 x 272 
		# image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
		image = cv2.resize(image, (352, 272))
		image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
		# image for plot_points() function; allows us to plot over original image
		plot_image = image
		cv2.imwrite('plot_image.jpg', plot_image)
		# cv2.imshow('Saved Original', image)
		print "Move the trackbar to adjust the number of edges"
                print "More edges means more detail, but a longer drawing time"
                print "Once the image with edges is ready, hit ESC"
		
                def nothing(x):
                        pass

                cv2.namedWindow('canny')
                
                cv2.createTrackbar('lower', 'canny', 0, 255, nothing)
                cv2.createTrackbar('upper', 'canny', 0, 255, nothing)
                
                while(1):
                        lower = cv2.getTrackbarPos('lower', 'canny')
                        upper = cv2.getTrackbarPos('upper', 'canny')
                        
                        edges = cv2.Canny(image, lower, upper)
                
                        # cv2.imshow('original', img)
                        cv2.imshow('canny', edges)
                        montage = np.concatenate((edges, image), axis = 1)
                        cv2. imshow('Canny Edge Detection vs. Original Image', montage)

                        k = cv2.waitKey(1) & 0xFF
                        
                        if k == 27:
                                break

                cv2.destroyAllWindows()		
		# cv2.imshow('Saved Edges', edges)
	        height, width = edges.shape
		print "resized image height = ", height
       		print "resized image width = ", width
		print

		image_processed = True
                find_pix(edges)
	




def find_pix(input_image):

	global image
	global pix_list
	global pen_down
	global current_pix
	global height, width
	global plot_image

	print "beginning to look for first white pixel"
	print

        image = input_image

	first_corner = [0, 0, False]
	second_corner = [0, 352, False]
	third_corner = [272, 352, False]
	fourth_corner = [272, 0, False]
	
	# pix_list.append(first_corner)
	# pix_list.append(second_corner)
	# pix_list.append(third_corner)
	# pix_list.append(fourth_corner)
	# pix_list.append(first_corner)

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




#  function to convert a pixel coordinate into angles for the servos
#  on each joint
def pix_to_ik(px, py, pen_state):

	global angle_array
	global angles_df

        # x_offset was 2.0 before shifting the drawing surface over to
        # accomodate extending a2 (to allow for theta_three = 65.0)
        # all units of measurement for distance should be in inches
        x_offset = 4.5
        y_offset = 8.5
        
	# 1280 is width of image from pi cam, 232.72 is 2 inches (for offset) 
	#  after multiplying by scalar
	cx = ((px * 11.0) / width) + x_offset
	# 1024 is height of image from pi cam, -py is to flip axis to Cartesian	
        cy = ((-py * 8.5) / height) + y_offset
	cartesian = [cx, cy]
	# print "cartesian coords = ", cartesian
	
	a1 = 200.0  # measurement in mm for link 1
	a2 = 236.0  # measurement in mm for link 2
	a1 = a1 / 25.4  # convert to inches
	a2 = a2 / 25.4  # convert to inches
	alpha = (math.pow(cx, 2.0) + math.pow(cy, 2.0) - math.pow(a1, 2.0) - math.pow(a2, 2.0)) / (2.0 * a1 * a2)

        # need to check so atan2 for theta_two stays within bounds; if not, set theta_two = 0
	if ((math.pow(alpha, 2)) > 1.0):
                print "pix_to_ik value out of bounds"
                print "(cx, cy) = ", cartesian
                print "setting theta_two to 0.0 degrees"
                print
                theta_two = 0.0
        else:
                theta_two = math.atan2(math.sqrt(1.0 - math.pow(alpha, 2.0)), alpha)
	
	#  0 <= theta_two <= +180
	# -90 <= theta_one <= +90 
	if (theta_two < 0.0):
		theta_two += math.pi
	elif (theta_two > math.pi):
		theta_two -= math.pi

        # use k1, k2, and gamma to avoid the use of acos()
	k1 = a1 + a2 * math.cos(theta_two)
	k2 = a2 * math.sin(theta_two)
	gamma = math.atan2(k2, k1)
	theta_one = math.atan2(cy, cx) - gamma

        # when the pen is down, theta_three is at 65 degrees
	if (pen_state == True):
		theta_three = 65.0
	elif (pen_state == False):
		theta_three = 0.0

	theta_one = round(math.degrees(theta_one))  # convert from rad to deg
	theta_one += 90.0                           # add +90 so we can stick with pos. integers
	theta_two = round(math.degrees(theta_two))  # convert from rad to deg
	
	angles = [theta_one, theta_two, theta_three]
	angle_array.append(angles)	
	angles_df = pd.DataFrame(angle_array, columns = ['THETA1', 'THETA2', 'THETA3'])
	
	return angles_df





##def trim_fat():
##
##        global angles_df
##        global angle_array_plot
##
##        angle_array_plot = angle_array
##
##        for s in range(1, len(angle_array)-1):
##                if ((angle_array[s][2] == 0.0) and (angle_array[s-1][2] == 0.0) and (angle_array[s+1][2] == 0.0)):                 
##                        del angle_array[s]
##
##        print 
##	angles_df = pd.DataFrame(angle_array, columns = ['THETA1', 'THETA2', 'THETA3'])
##	return angles_df





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

		if theta_three == math.radians(65.0):
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
# find_pix('mountain_river.jpg')
# find_pix('lana_bw.jpg')

process_image('Walter2.jpg')

print "algorithm has ran its course"
print

print "now creating sql table"
print
connection = create_engine('mysql+mysqlconnector://root:passwd@localhost:3306/ECE_439')
angles_df.to_sql(name = 'ANGLES', con = connection, if_exists = 'replace', index_label = 'ID')

print "angles_df = ", angles_df
print

print "begin plotting what the robot is drawing"
print
# plot_points()

cv2.waitKey(0)
cv2.destroyAllWindows()


