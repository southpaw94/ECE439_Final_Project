import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as ani
import cv2

im = cv2.imread('mountain_river.jpg')

# dimensions should match ratio of 8.5" x 11" paper
# 352 x 272 
im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
h, w = im.shape
h, w = float(h), float(w)

fig = plt.figure()
im_plot = plt.imshow(im, cmap='gray')

edges = cv2.Canny(im, 150, 175)

# Get the x and y locations for all edge pixels
x, y = np.nonzero(edges)
scatter = plt.scatter([], [], c='r', edgecolors='none', s=1)

def animate(i):
	arr = np.array((y[:i], x[:i])).T
	scatter.set_offsets(arr)
					
	return scatter,
	


ani = ani.FuncAnimation(fig, animate, frames=len(x), interval=1)

plt.show()
