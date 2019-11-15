"""
author: Josefine Graebener
"""


import imageio
import glob
import numpy as np
from PIL import Image
#from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import scipy.misc as smp
import os
import sys
import matplotlib.pyplot as plt
# For voronoi map
#from PathPlanning.VoronoiRoadMap import voronoi_road_map as vrm

# function to skip indices for obstacles
def drange2(start, stop, step):
    numelements = int((stop-start)/float(step))
    for i in range(numelements+1):
            yield start + i*step

# read in obstacles from image
for im_path in glob.glob("imglib/layout_clean.png"):
     #im = imageio.imread(im_path)
     im = Image.open(im_path)
     pix=im.load()
     print('Size of the image: '+str(im.size))  # Get the width and height of the image for iterating over
     xnum,ynum=im.size
     obs=[]
     obstacleList=[]
     #print(pix[x,y])  
     # Get the RGBA Value of the a pixel of an image
     pix_val = list(im.getdata())
     # make the obstacle map - every pixel which is not white is an obstacle
     R, G, B = im.convert('RGB').split()
     r = R.load()
     g = G.load()
     b = B.load()
     # make a list of black pixels
     k=0
     #for i in drange2(0, xnum, 2):
     for i in range(xnum):
          for j in drange2(0,ynum,5):
          #for j in range(ynum):
               if(r[i, j] != 255 or g[i, j] != 255 or b[i, j] != 255):
                    k+=1
                    obs.append((i, j, 1)) # Make a list of obstacle pixels
                    obstacleList.append((i/100, j/100, 0.1)) # Make a list of obstacle pixels scaled
# check obs data
data = np.zeros( (xnum,ynum,3), dtype=np.uint8)
# for row in data
#      row = makecolor((255-r, 255-g, 255-b))
#data= [x*255 for x in data]
for row in obs:
     for item in row:
          data[row[0],row[1]] = [255,0,0] # makes obstacles red

img = Image.fromarray( data )       # Create a PIL image
#img.show()                      # View in default viewer

#print(obs)
#testobs=obs[0:60]
# to do 
# # generate voronoi grid
# vor = Voronoi(obs)
# voronoi_plot_2d(vor,show_vertices=True, line_colors='orange',line_width=1, line_alpha=0.6, point_size=1)
# plt.show()
#print(size(obs))

# Reeds Shepp and RRT*
# sys.path.append(os.path.dirname(os.path.abspath(__file__))
#                 + "/PythonRobotics-master/PathPlanning/RRTStarReedsShepp/")
# sys.path.append(os.path.dirname(os.path.abspath(__file__))
#                 + "/PythonRobotics-master/PathPlanning/ReedsSheppPath/")

try:
    import rrt_star_reeds_shepp as m
except:
    raise

# sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
#                 "/../PathPlanning/RRTStar/")

try:
    import rrt_star as rrtstar
except ImportError:
    raise

print('Number of obstacles '+str(len(obs)))

m.show_animation = False
# get Voronoi map of the obstacles

# Get Path from Voronoi map 
# get waypoints from Voronoi map

# Specify waypoints and connect RRT* through the waypoints by matching location and yaw (and velocity??)
waypoints=[[500/100,0.2,np.deg2rad(90.0)],[390/100,122/100,np.deg2rad(180.0)],[336/100,223/100,np.deg2rad(0.0)],[456/100,223/100,np.deg2rad(0)],[505/100,300/100,np.deg2rad(90.0)],[505/100,420/100,np.deg2rad(90.0)],[400/100,473/100,np.deg2rad(180.0)],[321/100,520/100,np.deg2rad(125.0)],[321/100,473/100,np.deg2rad(180.0)],[200/100,473/100,np.deg2rad(180.0)],[75/100,575/100,np.deg2rad(90.0)],[200/100,667/100,np.deg2rad(0.0)],[339/100,667/100,np.deg2rad(0.0)]]

# Compute, plot the path and save the x,y, yaw coordinates
try:
    pathA = m.mainAVPtest(obstacleList,waypoints[0],waypoints[1],[3.5, 5.0],[0.0,2.5], max_iter=300)
    plt.plot([x for (x, y,yaw) in pathA], [y for (x, y,yaw) in pathA], '-r')
    with open('PathA', 'w') as fh:
        for x, y, yaw in pathA: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathB = m.mainAVPtest(obstacleList,waypoints[1],waypoints[2],[2.5,3.5],[1,2.5],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathB], [y for (x, y, yaw) in pathB], '-r')
    with open('PathB', 'w') as fh:
        for x, y, yaw in pathB: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathC = m.mainAVPtest(obstacleList,waypoints[2],waypoints[3],[3,4.5],[1.5,2.5],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathC], [y for (x, y, yaw) in pathC], '-r')
    with open('PathC', 'w') as fh:
        for x, y, yaw in pathC: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathD = m.mainAVPtest(obstacleList,waypoints[3],waypoints[4],[4.0,5.5],[2, 4.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathD], [y for (x, y, yaw) in pathD], '-r')
    with open('PathD', 'w') as fh:
        for x, y, yaw in pathD: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathE = m.mainAVPtest(obstacleList,waypoints[4],waypoints[5],[4.5,5.5],[2.5,4.5],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathE], [y for (x, y, yaw) in pathE], '-r')
    with open('PathE', 'w') as fh:
        for x, y, yaw in pathE: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathF = m.mainAVPtest(obstacleList,waypoints[5],waypoints[6],[4.0,5.5],[3.5,5.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathF], [y for (x, y, yaw) in pathF], '-r')
    with open('PathF', 'w') as fh:
        for x, y, yaw in pathF: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathG = m.mainAVPtest(obstacleList,waypoints[6],waypoints[7],[2.5,4.5],[4.0, 5.5],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathG], [y for (x, y, yaw) in pathG], '-r')
    with open('PathG', 'w') as fh:
        for x, y, yaw in pathG: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass
try:
    pathH = m.mainAVPtest(obstacleList,waypoints[6],waypoints[7],[2.0,4.0],[4.0, 6.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathH], [y for (x, y, yaw) in pathH], '-r')
    with open('PathH', 'w') as fh:
        for x, y, yaw in pathH: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass

try:
    pathI = m.mainAVPtest(obstacleList,waypoints[7],waypoints[8],[1.5,4.0],[4.0, 6.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathI], [y for (x, y, yaw) in pathI], '-r')
    with open('PathI', 'w') as fh:
        for x, y, yaw in pathI: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass

try:
    pathJ = m.mainAVPtest(obstacleList,waypoints[8],waypoints[9],[0.5,2.2],[4.0, 6.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathJ], [y for (x, y, yaw) in pathJ], '-r')
    with open('PathJ', 'w') as fh:
        for x, y, yaw in pathJ: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass

try:
    pathK = m.mainAVPtest(obstacleList,waypoints[9],waypoints[10],[0.5,2.2],[5.5, 7.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathK], [y for (x, y, yaw) in pathK], '-r')
    with open('PathK', 'w') as fh:
        for x, y, yaw in pathK: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass

try:
    pathL = m.mainAVPtest(obstacleList,waypoints[10],waypoints[11],[2.0,4.0],[6.0, 7.0],max_iter=300)
    plt.plot([x for (x, y, yaw) in pathL], [y for (x, y, yaw) in pathL], '-r')
    with open('PathL', 'w') as fh:
        for x, y, yaw in pathL: 
            fh.write('{} {} {}\n'.format(x, y, yaw))
except:
    pass

# plot specified waypoints
for (ox, oy, oyaw) in waypoints:    
     plt.plot(ox, oy, "xr")

# plot obstacles
for (ox, oy, size) in obstacleList:    
     plt.plot(ox, oy, "ok", ms=30 * size)
plt.show()

