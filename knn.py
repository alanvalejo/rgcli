#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Knn (TODO)
==========================

Copyright (C) 2015 Thiago Faleiros <thiagodepaulo@gmail.com>,
Alan Valejo <alanvalejo@gmail.com> All rights reserved.

TODO
"""

import os
import numpy as np

from scipy import spatial
from optparse import OptionParser
from multiprocessing import Process, Pipe

__author__ = 'Thiago Faleiros, Alan Valejo'
__license__ = 'GNU GENERAL PUBLIC LICENSE'
__docformat__ = 'restructuredtext en'
__version__ = '0.1'

def knn(obj_subset, data, kdtree, k, sender):

	ew = [] # Set of weighted edges
	for obj in obj_subset:
		obj_attrs = data[obj]
		obj_knn = kdtree.query(obj_attrs, k=(k+1));
		# For each KNN vertex
		for i, nn in enumerate(obj_knn[1]):
			d1 = obj_knn[0][i]
			ew.append((obj, nn, 1/(1+d1)))

	sender.send(ew)

if __name__ == '__main__':

	# Parse options command line
	parser = OptionParser()
	usage = "usage: python %prog [options] args ..."
	description = """Knn Graph Construction"""
	parser.add_option("-f", "--filename", dest="filename", help="Input file", metavar="FILE")
	parser.add_option("-o", "--output", dest="output", help="Output file", metavar="FILE")
	parser.add_option("-1", "--k", dest="k", help="Knn", default=3)
	parser.add_option("-t", "--threads", dest="threads", help="Number of threads", default=4)

	# Process options and args
	(options, args) = parser.parse_args()
	k = int(options.k) # Knn
	threads = int(options.threads) # Number of threads

	if options.filename is None:
		parser.error("required -f [filename] arg.")
	if options.output is None:
	 	filename, extension = os.path.splitext(os.path.basename(options.filename))
	 	options.output = 'output/' + filename + '-knn.edgelist'

	# Reading data table
	# Acess value by data[object_id][attribute_id]
	# Acess all attributs of an object by data[object_id]
	data = np.loadtxt(options.filename, unpack=True).transpose()
	attr_count = data.shape[1] # Number of attributes
	obj_count = data.shape[0] # Number of objects
	obj_set = range(0, obj_count) # Set of objects

	# Create KD tree from data
	kdtree = spatial.KDTree(data)

	# Size of the set of vertices by threads, such that V = {V_1, ..., V_{threads} and part = |V_i|
	part = obj_count / threads

	# Starting Knn processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=knn, args=(obj_set[i:i+part], data, kdtree, k, sender))
		p.daemon = True
		p.start()
		receivers.append(receiver)

	# Create set of weighted edges
	edgelist = ''
	for receiver in receivers:
		# Waiting threads
		ew = receiver.recv()
		for edge in ew:
			edgelist += '%s %s %s\n' % edge

	# Save edgelist in output file
	with open(options.output,'w') as fout:
		fout.write(edgelist)