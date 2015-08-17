#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mutual Knn (TODO)
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
	"""
	Knn
	Attributes:
		obj_subset (array): Set of vertices by threads
		data (np.array): Original data table
		kdtree (spatial.KDTree): KD tree accounting for from data
		k (int): K nearest neighbors
		sender (multiprocessing.Connection): Pipe connection objects
	"""

	dic_knn = dict()
	for obj in obj_subset:
		obj_attrs = data[obj]
		# (dists, indexs) = kdtree.query(obj_attrs, k=(k+1))
		dic_knn[obj] = kdtree.query(obj_attrs, k=(k+1))
		# Considering the first nearst neighbor equal itself
		dic_knn[obj] = (dic_knn[obj][0][1:], dic_knn[obj][1][1:])

	sender.send(dic_knn)

def mutual_knn(obj_subset, k, dic_knn, sender):
	"""
	Mutual Knn
	Attributes:
		obj_subset (array): Set of vertices by threads
		k2 (int): Semi-supervised K
		buff (dictinary): Each vertex is associated with the nearest neighbor labeled
		dic_knn (dictionary): List of Knn to each vertice
		sender (multiprocessing.Connection): Pipe connection objects
	"""

	ew = [] # Set of weighted edges
	for obj in obj_subset:
		obj_knn = dic_knn[obj]
		# For each KNN vertex
		for i, nn in enumerate(obj_knn[1]):
			nn_knn = dic_knn[nn]
			# If it is mutual
			if obj in nn_knn[1]:
				# Distance between obj and nn
				d1 = obj_knn[0][i]
				# Tuple (edge, weight)
				ew.append((obj, nn, 1/(1+d1)))

	sender.send(ew)

if __name__ == '__main__':

	# Parse options command line
	parser = OptionParser()
	usage = "usage: python %prog [options] args ..."
	description = """Graph Based on Informativeness of Labeled Instances"""
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
	 	options.output = 'output/' + filename + '-mutual.edgelist'

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

	# Creating list of labeled nearst neighours
	receivers = []
	for i in xrange(0, obj_count, part):
		# Returns a pair (conn1, conn2) of Connection objects representing the ends of a pipe
		sender, receiver = Pipe()
		p = Process(target=knn, args=(obj_set[i:i+part], data, kdtree, k, sender))
		p.daemon = True
		p.start()
		receivers.append(receiver)

	dic_knn = dict()
	for receiver in receivers:
		# Waiting threads
		dic_knn_aux = receiver.recv()
		dic_knn.update(dic_knn_aux)

	# Starting GBILI processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=mutual_knn, args=(obj_set[i:i+part], k, dic_knn, sender))
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