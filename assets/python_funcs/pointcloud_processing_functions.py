# -*- coding: utf-8 -*-

# This file is part of the data publication of the point cloud time series acquired at Kijkduin (Vos et al. 2021)
# Copyright (c) 2021 Katharina Anders, 3DGeo Research Group, Heidelberg University

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details (http://www.gnu.org/licenses/).


import sys
try:
	import numpy as np
except:
	print("Could not import required module: numpy")
	print("Please install the module for usage of the script functions")
	sys.exit()

try:
	import laspy
except:
	print("Could not import required module: laspy")
	print("Please install the module for usage of the script functions")
	sys.exit()

def read_las(pointcloudfile,get_attributes=False,useevery=1):
	'''

	:param pointcloudfile: specification of input file (format: las or laz)
	:param get_attributes: if True, will return all attributes in file, otherwise will only return XYZ (default is False)
	:param useevery: value specifies every n-th point to use from input, i.e. simple subsampling (default is 1, i.e. returning every point)
	:return: 3D array of points (x,y,z) of length number of points in input file (or subsampled by 'useevery')
	'''

	import laspy
	import numpy as np

	# read the file
	inFile = laspy.read(pointcloudfile)

	# get the coordinates (XYZ)
	coords = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()
	coords = coords[::useevery, :]

	if get_attributes == False:
		return (coords)

	else:
		las_fields= [info.name for info in inFile.points.point_format.dimensions]
		attributes = {}

		for las_field in las_fields[3:]: # skip the X,Y,Z fields
			attributes[las_field] = inFile.points[las_field][::useevery]

		return (coords, attributes)

def write_las(outpoints, outfilepath, attribute_dict={}):

		'''

		:param outpoints: 3D array of points to be written to output file
		:param outfilepath: specification of output file (format: las or laz)
		:param attribute_dict: dictionary of attributes (key: name of attribute; value: 1D array of attribute values in order of points in 'outpoints'); if not specified, dictionary is empty and nothing is added
		:return: None
		'''

		import laspy

		hdr = laspy.LasHeader(version="1.4", point_format=6)
		hdr.x_scale = 0.00025
		hdr.y_scale = 0.00025
		hdr.z_scale = 0.00025
		mean_extent = np.mean(outpoints, axis=0)
		hdr.x_offset = int(mean_extent[0])
		hdr.y_offset = int(mean_extent[1])
		hdr.z_offset = int(mean_extent[2])

		las = laspy.LasData(hdr)

		las.x = outpoints[:, 0]
		las.y = outpoints[:, 1]
		las.z = outpoints[:, 2]
		for key, vals in attribute_dict.items():
			try:
				las[key] = vals
			except:
				las.add_extra_dim(laspy.ExtraBytesParams(
					name=key,
					type=type(vals[0])
					))
				las[key] = vals

		las.write(outfilepath)

		return

def transform_points(points, trafomat):
	'''
	Applies a rigid transformation, i.e. rotation and translation, to 3D point data.
	:param points: 2D array of 3D points with shape (N,3)
	:param trafomat: 2D array of rigid transformation matrix with 3x3 rotation and 1x3 translation parameters
	:return: transformed points in 2D array of shape (N,3)
	'''
	rotation = np.array(trafomat)[:, :3]
	translation = np.array(trafomat)[:, 3].flatten()
	pts_rot = points.dot(rotation.T)
	pts_trafo = pts_rot + translation
	return pts_trafo[:,:3]

def get_scan_props_from_meta(metafile,incr_highres=0.013):
	'''
	Extracts scan properties from metadata files provided with point cloud files
	:param metafile: specification of input file (format: *_meta.txt)
	:param incr_highres: angular resolution of high-resolution scans (will be flagged in output dictionary)
	:return: dictionary with scan properties (theta_min, theta_max, theta_incr, phi_min, phi_max, phi_incr, highres)
	'''
	with open(metafile) as fo:
		lines = fo.readlines()

	fov_res_cols = lines[1].strip().split(' ')
	fov_res_vals = np.array(lines[2].strip().split(' ')).astype(float)
	fov_res_dict = {k: v for k, v in zip(fov_res_cols, fov_res_vals)}

	res = fov_res_dict['phi_incr']
	if (res - incr_highres) < 0.001:
		fov_res_dict['highres'] = True
	else:
		fov_res_dict['highres'] = False

	return fov_res_dict

if __name__ == "__main__":

	'''
	This is an example script procedure which 
		(1) reads a point cloud from a laz file, 
		(2) transforms the point cloud using a matrix from a specified supplementary file, and
		(3) writes the transformed points to an output laz file.
	Note: Writing compressed las files (i.e. laz) requires the availability of the laszip.dll in the program environment. Otherwise, only las format can be written.
	'''

	import os
	try:
		infile = sys.argv[1] # path to las file of point cloud
		outfile = sys.argv[2] # path to las file to store transformed point cloud
	except:
		print('Script arguments could not be parsed correctly. Check specified arguments.')
		print('USAGE: %s <path to input point cloud> <path to file transformation matrix> <path to file to store output point cloud>' % sys.argv[0])
		print('EXAMPLE: %s 161113_000123.laz 161113_000123_trafomat.txt 161113_000123_trafo.laz' % sys.argv[0])
		sys.exit()
	
	if not os.path.isfile(infile):
		print("Specified input point cloud cannot be accessed. Please check for file: %s" % infile)
		sys.exit()

	# read point cloud metadata
	print('Reading point cloud metadata...')
	metafile = '.'.join(infile.strip().split('.')[:-1]) + '_meta.txt'
	fov_res_dict = get_scan_props_from_meta(metafile)
	high_res = fov_res_dict['highres']

	if high_res == True:
		print('\tHigh resolution scan')
	else:
		print('\tLow resolution scan')
	print('\tangular resolution: %.3f' % fov_res_dict['phi_incr'])

	# read input point cloud from las/laz
	print('Reading point cloud data...')
	points, attributes = read_las(infile,get_attributes=True)
	print('\t%i points read' % len(points))

	# read transformation matrix and apply transformation to points
	print('Transforming point cloud data...')
	trafofile = '.'.join(infile.strip().split('.')[:-1]) + '_trafomat.txt'
	trafo_mat = np.loadtxt(trafofile)
	points_transformed = transform_points(points, trafo_mat)

	# store transformed point cloud to las/laz
	print('Writing transformed point cloud data...')
	write_las(points_transformed, outfile)
	print('\tOutput point cloud written to: %s' % outfile)
