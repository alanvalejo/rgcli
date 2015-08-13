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

__author__ = 'Thiago Faleiros, Alan Valejo, Lilian Berton'
__license__ = 'GNU GENERAL PUBLIC LICENSE'
__docformat__ = 'restructuredtext en'
__version__ = '0.1'

def labeled_nearest(vertex_set, graph, labeled_set, kdtree, sender):
	"""
	...
	Attributes:
	Returns:
	"""

	buff = dict()
	dic_nn = dict()
	for v in vertex_set:
		if v.index % 10000 == 0:
			print v.index
		min_d = float('inf')
		min_l = -1
		v_pts = [v["x"], v["y"], v["r"], v["g"], v["b"]]
		for u_idx in labeled_set:
			u = graph.vs()[u_idx]
			d = ((v_pts[0] - u["x"])**2 + (v_pts[1] - u["y"])**2 + (v_pts[2] - u["r"])**2 + (v_pts[3] - u["g"])**2 + (v_pts[4] - u["b"])**2)
			if d < min_d:
				min_d = d
				min_l = u_idx
		buff[v.index] = (min_l, min_d)

		# atribui lista de k vizinhos mais proximos
		dic_nn[v.index] = kdtree.query(np.array([v_pts]), k=(k+1))

	sender.send((buff, dic_nn))

def gbili(vertex_set, kdtree, k1, k2, buff, sender, dic_nn):
	"""
	...
	Attributes:
	Returns:
	"""

	#print k2
	l = []
	for v in vertex_set:
		if v.index % 10000 == 0:
			print v.index

		l_dists = []
		l_ew = []
		list_v_nn = dic_nn[v.index] # kdtree.query(np.array([[v["x"], v["y"], v["r"], v["g"], v["b"]]]), k=(k1+1));
		# for each KNN vertex
		for i, nn in enumerate(list_v_nn[1][0]):
			if nn == v.index:
				continue
			u = graph.vs()[nn]
			list_u_nn = dic_nn[nn] #kdtree.query(np.array([[u["x"], u["y"], u["r"], u["g"], u["b"]]]), k=(k1+1))
			# if it is mutual
			if v.index in list_u_nn[1][0]:
				d1 = list_v_nn[0][0][i]
				(lidx,d2) = buff[u.index] 		# near_labeled(v, pts, labeled, labeled_pts, buff)
				l_dists.append(d1 + d2)
				# tuple (edge, weight)
				l_ew.append(((v.index, nn), 1/(1+d1)))

		count = 0
		for idx in np.argsort(l_dists):
			if count < k2:
				# put(edge, weight)  (l_ew[idx][0], l_ew[idx][1])
				l.append(l_ew[idx])
			else:
				break
			count+=1
	#print 'sending %d' %len(l)
	sender.send(l)

def get_attrs(data, object_id):
	"""
	Acess all attributs of an object
	Attributes:
		data (): Data
		object_id (): Object identifier
	Returns:
		array: Attribute set of an object
	"""

	return data[:,object_id]

def get_attr(data, object_id, attr_id):
	"""
	Acess attribute value
	Attributes:
		data (np.array): Data
		object_id (int): Object identifier
		attr_id (int): Attribute identifier
	Returns:
		int: Attribute value
	"""

	return data[attr_id][object_id]

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
	data = np.loadtxt(options.filename, unpack=True)
	attr_count = data.shape[0] # Number of attributes
	obj_count = data.shape[1] # Number of objects
	obj_set = range(0, obj_count) # Set of objects

	# Create KD tree from data
	kdtree = spatial.KDTree(data)

	# Size of the set of vertices by threads, such that V = {V_1, ..., V_{threads} and part = |V_i|
	part = len(graph.vs()) / threads

	# # ******************************************
	# lq = []
	# l_threads = []
	# for i in xrange(0, len(graph.vs()), part ):
	# 	sender, receiver = Pipe()
	# 	p = Process(target=labeled_nearest, args=(graph.vs()[i:i+part], graph, labeled_set, kdtree, sender))
	# 	p.daemon = True
	# 	p.start()
	# 	lq.append(receiver)
	# 	l_threads.append(p)

	# buff = dict()
	# dic_nn = dict()
	# for receiver in lq:
	# 	(buff_p, dic_nn_p) = receiver.recv()
	# 	buff.update(buff_p)
	# 	dic_nn.update(dic_nn_p)
	# # ******************************************

	# lq = []
	# l_threads = []
	# for i in xrange(0, len(graph.vs()), part ):
	# 	sender, receiver = Pipe()
	# 	p = Process(target=gbili, args=(graph.vs()[i:i+part], kdtree, k, k2, buff, sender, dic_nn))
	# 	p.daemon = True
	# 	p.start()
	# 	l_threads.append(p)
	# 	lq.append(receiver)

	# # Create set of weighted edges
	# edges = []
	# weights = []
	# for receiver in lq:
	# 	l_ew = receiver.recv()
	# 	for edge, weight in l_ew:
	# 		edges += [edge]
	# 		weights.append(weight)

	# # Create graph by igraph library
	# graph = igraph.Graph()

	# # Insert weighted edges to graph
	# graph.add_edges(edges)
	# graph.es["weight"] = weights
	# graph.to_undirected()
	# graph.simplify(combine_edges='first')

	# # Save gbili graph to edgelist format
	# graph.write(options.output, format='edgelist')