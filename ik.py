import math
import pandas as pd

pix_list = []
angle_array = []
angles_df = pd.DataFrame()

def pix_to_ik(px, py, pen_state):

	global pix_list
	global angle_array
	global angles_df

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
	# theta_one has the same constraints 
	if (theta_two < 0):
		theta_two += math.pi
	elif (theta_two > math.pi):
		theta_two -= math.pi

	k1 = a1 + a2 * math.cos(theta_two)
	k2 = a2 * math.sin(theta_two)
	gamma = math.atan2(k2, k1)
	theta_one = math.atan2(cy, cx) - gamma
	
	if pen_state == True:
		theta_three = 90
	elif pen_state == False:
		theta_three = 0

	theta_one = round(math.degrees(theta_one))  # convert from rad to deg
	theta_one += 90
	theta_two = round(math.degrees(theta_two))  # convert from rad to deg
	angles = [theta_one, theta_two, theta_three]
	angle_array.append(angles)	
	angles_df = pd.DataFrame(angle_array, columns = ['THETA1', 'THETA2', 'THETA3'])
#	angles_df += 90
	return angles_df
