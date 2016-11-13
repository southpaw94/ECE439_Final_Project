#!/usr/bin/env python
import cv2
import math
import numpy as np
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep

angle_array = []
GPIO.setmode(GPIO.BCM)
# universal setup for GPIO pin numbering

# feeds pixel coords to pix_to_ik to output servo angles
# finds non-zero value in image, goes to that point, searches
# 3x3 neighborhood, deletes previous point, and repeats
def get_pix():

	camera = PiCamera()
	camera.start_preview()
	sleep(5)
	camera.capture('picture.jpg')
	camera.stop_preview()
	image_captured = cv2.imread('picture.jpg', 0)
	image_edged = cv2.Canny(image_captured, 125, 200)

	cv2.imshow('original image', image_captured)
	cv2.imshow('image with edges', image_edged)
	height, width = image_edged.shape

	# print image size
	print "image height = ", height
	print "image width = ", width
	# image will be current image that's drawn & modified
	# image = lana_edged
	image = image_edged
	pix_list = []
	
	for i in range(1, height):
		for j in range(1, width):
			if image[i,j] != 0:
				current_pix = [i, j]
				pix_list.append(current_pix)
				# delete already drawn pixels
				image[i, j] = 0
				# make sure we're in the boundaries of the image
				if ((i-1 > 0) and (j-1 > 0) and (i < height-1) and (j < width-1)):
					# check neighborhood (3x3)
					if (image[i-1,j-1]!=0 or image[i-1,j]!=0 or image[i-1,j+1]!=0 or \
					image[i,j-1]!=0 or image[i,j+1]!=0 or image[i+1,j-1]!=0 or \
					image[i+1,j]!=0 or image[i+1,j+1]!=0): 
				  		# index through rows and columns of neighborhood matrix (3x3)
						# current pixel here is image(k, l)
						for k in range(i-1, i+2):
							for l in range(j-1, j+2):
								if image[k, l] != 0:
									current_pix = [k, l]
									pix_list.append(current_pix)
								        image[k, l] = 0
									
	print "i = ", i
	print "j = ", j
	print "length of pix_list = ", len(pix_list)
	print "pix_list = ", pix_list
#	cv2.imshow("final image", image)



def get_pix_saved_image(im_2):
	
	im_2 = cv2.imread(im_2)
	cv2.imshow('Saved Original', im_2)
	im_2_edged = cv2.Canny(im_2, 230, 240)
	cv2.imshow('Saved Edges', im_2_edged)
	height_2, width_2 = im_2_edged.shape
	im_2 = im_2_edged
	pix_list_im_2 = []	

	for i in range(1, height_2):
		for j in range(1, width_2):
			if im_2[i,j] != 0:
				current_pix_im_2 = [i, j]
				pix_list_im_2.append(current_pix_im_2)
				# delete already drawn pixels
				im_2[i, j] = 0
				# make sure we're in the boundaries of the image
				if ((i-1 > 0) and (j-1 > 0) and (i < height_2-1) and (j < width_2-1)):
					# check neighborhood (3x3)
					if (im_2[i-1,j-1]!=0 or im_2[i-1,j]!=0 or im_2[i-1,j+1]!=0 or \
					im_2[i,j-1]!=0 or im_2[i,j+1]!=0 or im_2[i+1,j-1]!=0 or \
					im_2[i+1,j]!=0 or im_2[i+1,j+1]!=0): 
				  		# index through rows and columns of neighborhood matrix (3x3)
						# current pixel here is image(k, l)
						for k in range(i-1, i+2):
							for l in range(j-1, j+2):
								if im_2[k, l] != 0:
									current_pix_im_2 = [k, l]
									pix_list_im_2.append(current_pix_im_2)
								        im_2[k, l] = 0
									
#	print "i = ", i
#	print "j = ", j
	print "length of pix_list = ", len(pix_list_im_2)
#	print "pix_list = ", pix_list_im_2
	for n in range(0, len(pix_list_im_2)):
		px_input = pix_list_im_2[n][0]
		py_input = pix_list_im_2[n][1]
		pix_to_ik(px_input, py_input)





#  function to convert a pixel coordinate into angles for the servos
#  on each joint
def pix_to_ik(px, py):
	
	# 1280 is width of image from pi cam, 232.72 is 2 inches (for offset) 
	#  after multiplying by scalar
	cx = (11.0 / 1280.0) * (px + 232.727272727)
	# 1024 is height of image from pi cam, -py is to flip axis to Cartesian	
        cy = (8.5 / 1024.0) * (-py + 1024.0)
	cartesian = [cx, cy]
	# print "cartesian coords = ", cartesian
	
	a1 = 200.0  # measurement in mm for link 1
	a2 = 200.0  # measurement in mm for link 2
	a1 = a1 / 25.4  # convert to inches
	a2 = a2 / 25.4  # convert to inches
	alpha = (math.pow(cx, 2) + math.pow(cy, 2) - math.pow(a1, 2) - math.pow(a2, 2)) / (2 * a1 * a2)
	theta_two = math.atan2(math.sqrt(1 - math.pow(alpha, 2)), alpha)
	
	# -90 <= theta_two <= +90
	# ideall theta_one has the same constraints 
	if (theta_two < -(math.pi/2)):
		theta_two += math.pi
	elif (theta_two > (math.pi/2)):
		theta_two -= math.pi

	k1 = a1 + a2 * math.cos(theta_two)
	k2 = a2 * math.sin(theta_two)
	gamma = math.atan2(k2, k1)
	theta_one = math.atan2(cy, cx) - gamma
	
	theta_one = round(math.degrees(theta_one))  # convert from rad to deg
	theta_two = round(math.degrees(theta_two))  # convert from rad to deg
	angles = [theta_one, theta_two]
	angle_array.append(angles)	
	return angles;





get_pix_saved_image('mountain_river.jpg')
print "angle_array = ", (angle_array)
# pix_to_ik(1280, 1024)

cv2.waitKey(0)
cv2.destroyAllWindows()


