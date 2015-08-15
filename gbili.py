#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GBILI (Graph Based on Informativeness of Labeled Instances)
==========================

Copyright (C) 2015 Thiago Faleiros <thiagodepaulo@gmail.com>,
Alan Valejo <alanvalejo@gmail.com>, Lilian Berton <lilian.2as@gmail.com>
All rights reserved

To exploit the informativeness conveyed by these few labeled instances
available in semi-supervised scenarios.

Required python igraph library
.. _igraph: http://igraph.sourceforge.net
"""

import Image
import math
import igraph
import numpy as np
import threading
import os
import random

from scipy import spatial
from optparse import OptionParser
from math import sqrt
from Queue import Queue
from multiprocessing import Process, Pipe
from scipy.spatial import distance

__author__ = 'Thiago Faleiros, Alan Valejo, Lilian Berton'
__license__ = 'GNU GENERAL PUBLIC LICENSE'
__docformat__ = 'restructuredtext en'
__version__ = '0.1'

def labeled_nearest(obj_subset, data, labeled_set, kdtree, k1, sender):
	"""
	...
	Attributes:
	Returns:
	"""

	buff = dict()
	dic_knn = dict()
	for obj in obj_subset:
		if obj % 10000 == 0:
			print obj
		min_dist = float('inf')
		min_label = -1
		obj_attrs = data[obj]
		for obj_labeled in labeled_set:
			obj_labeled_attrs = data[obj_labeled]
			dist = distance.euclidean(obj_attrs, obj_labeled_attrs)
			if dist < min_dist:
				min_dist = dist
				min_label = obj_labeled
		buff[obj] = (min_label, min_dist)

		# atribui lista de k vizinhos mais proximos
		# (dists, indexs) = kdtree.query(obj_attrs, k=(k+1))
		dic_knn[obj] = kdtree.query(obj_attrs, k=(k1+1))
		dic_knn[obj] = (dic_knn[obj][0][1:], dic_knn[obj][1][1:])	# considering the first nearst neighbor equal itself

	sender.send((buff, dic_knn))

def gbili(obj_subset, data, k1, k2, buff, dic_knn, sender):
	"""
	...
	Attributes:
	Returns:
	"""

	ew = []	
	for obj in obj_subset:
		if obj % 10000 == 0:
			print obj
		obj_dists = []
		obj_ew = []
		obj_knn = dic_knn[obj]
		# For each KNN vertex
		for i, nn in enumerate(obj_knn[1]):
			nn_knn = dic_knn[nn]
			# If it is mutual
			if obj in nn_knn[1]:
				# Distance between obj and nn
				d1 = obj_knn[0][i]
				# Labeled nearst neabord and distance between nn and labeled nerast neabord
				(labeled, d2) = buff[nn]
				obj_dists.append(d1 + d2)
				# Tuple (edge, weight)
				obj_ew.append((obj, nn, 1/(1+d1)))
				#print obj_ew

		for idx in np.argsort(obj_dists)[:k2]:
			ew.append(obj_ew[idx])

	#print ew

	sender.send(ew)

if __name__ == '__main__':

	# Parse options command line
	parser = OptionParser()
	usage = "usage: python %prog [options] args ..."
	description = """Graph Based on Informativeness of Labeled Instances"""
	parser.add_option("-f", "--filename", dest="filename", help="Input file", metavar="FILE")
	parser.add_option("-o", "--output", dest="output", help="Output file", metavar="FILE")
	parser.add_option("-l", "--labels", dest="labels", help="Labels")
	parser.add_option("-1", "--k1", dest="k1", help="Knn", default=3)
	parser.add_option("-2", "--k2", dest="k2", help="Semi-supervised k", default=3)
	parser.add_option("-t", "--threads", dest="threads", help="Number of threads", default=4)

	# Process options and args
	(options, args) = parser.parse_args()
	k1 = int(options.k1) # Knn
	k2 = int(options.k2) # Semi-supervised K
	threads = int(options.threads) # Number of threads

	if options.filename is None:
		parser.error("required -f [filename] arg.")
	if options.labels is None:
		parser.error("required -l [labels] arg.")
	if options.output is None:
	 	filename, extension = os.path.splitext(os.path.basename(options.filename))
	 	options.output = 'output/' + filename + '.edgelist'

	# Reading the labeled set of vertex
	f = open(options.labels, 'r')
	labeled_set = [int(line.rstrip('\n')) for line in f]

	# Reading data table
	# Acess value by get_attr(data, object_id, attr_id)
	# Acess all attributs of an object by get_attrs(data, object_id)
	data = np.loadtxt(options.filename, unpack=True).transpose()
	attr_count = data.shape[1] # Number of attributes
	obj_count = data.shape[0] # Number of objects
	obj_set = range(0, obj_count) # Set of objects

	# Create KD tree from data
	kdtree = spatial.KDTree(data)

	# Size of the set of vertices by threads, such that V = {V_1, ..., V_{threads} and part = |V_i|
	part = obj_count / threads

	# creating list of labeled nearst neighours
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=labeled_nearest, args=(obj_set[i:i+part], data, labeled_set, kdtree, k1, sender))
		p.daemon = True
		p.start()
		receivers.append(receiver)

	buff = dict()
	dic_knn = dict()
	for receiver in receivers:
		# waiting threads
		(buff_aux, dic_knn_aux) = receiver.recv()
		buff.update(buff_aux)
		dic_knn.update(dic_knn_aux)

	# starting GBILI processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=gbili, args=(obj_set[i:i+part], data, k1, k2, buff, dic_knn, sender))
		p.daemon = True
		p.start()
		receivers.append(receiver)

	# Create set of weighted edges
	l = []
	edgelist = ''
	for receiver in receivers:
		# waiting threads
		ew = receiver.recv()
		for edge in ew:
			edgelist += '%s %s %s\n' % edge
			l.append(edge)
	
	# save edgelist in output file
	with open(options.output,'w') as fout:
		fout.write(edgelist)


	# \node[main_node] (1) at (0,0) {1};
	s1 = ''
	for i in xrange(len(data)):
		s1 += '\n\\node[main_node] (%s) at (%s,%s) {%s};' %(i, data[i][0], data[i][1], i)

	s2 = '\n'.join( '\\draw ('+str(e[0])+') -- ('+str(e[1])+');' for e in l)+'\n'

	with open('output/plot','w') as fout:
		fout.write(s1+'\n'+s2)
	
	
	

