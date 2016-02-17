#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GBILI (Graph Based on Informativeness of Labeled Instances)
==========================

Copyright (C) 2015 Thiago Faleiros <thiagodepaulo@gmail.com>,
Alan Valejo <alanvalejo@gmail.com>, Lilian Berton <lilian.2as@gmail.com>
All rights reserved.

To exploit the informativeness conveyed by these few labeled instances
available in semi-supervised scenarios.
"""

import csv
import os
import sys
from multiprocessing import Pipe, Process
from optparse import OptionParser

import numpy as np
from scipy import spatial

from helper import write_ncol, write_pajek

__author__ = 'Thiago Faleiros, Alan Valejo, Lilian Berton'
__license__ = 'GNU GENERAL PUBLIC LICENSE'
__docformat__ = 'restructuredtext en'
__version__ = '0.1'

def labeled_nearest(obj_subset, data, labeled_set, kdtree, ke, sender):
	"""
	Check the set of labeled nearest for all vertices
	Attributes:
		obj_subset (array): Set of vertices by threads
		data (np.array): Original data table
		labeled_set (array): Set of lebeled vertices
		kdtree (spatial.KDTree): KD tree accounting for from data
		ke (int): K nearest neighbors
		sender (multiprocessing.Connection): Pipe connection objects
	"""

	buff = dict()
	dic_knn = dict()
	for obj in obj_subset:
		min_dist = float('inf')
		min_label = -1
		obj_attrs = data[obj]
		for obj_labeled in labeled_set:
			obj_labeled_attrs = data[obj_labeled]
			dist = spatial.distance.euclidean(obj_attrs, obj_labeled_attrs)
			if dist < min_dist:
				min_dist = dist
				min_label = obj_labeled
		# Map [object_id] = <labeled_id, distance>
		buff[obj] = (min_label, min_dist)

		# (dists, indexs) = kdtree.query(obj_attrs, k=(k+1))
		dic_knn[obj] = kdtree.query(obj_attrs, k=(ke + 1))
		# Considering the first nearst neighbor equal itself
		dic_knn[obj] = (dic_knn[obj][0][1:], dic_knn[obj][1][1:])

	sender.send((buff, dic_knn))

def gbili(obj_subset, ki, buff, dic_knn, sender):
	"""
	GBILI kernel
	Attributes:
		obj_subset (array): Set of vertices by threads
		ki (int): Semi-supervised K
		buff (dictinary): Each vertex is associated with the nearest neighbor labeled
		dic_knn (dictionary): List of Knn to each vertice
		sender (multiprocessing.Connection): Pipe connection objects
	"""

	ew = [] # Set of weighted edges
	for obj in obj_subset:
		obj_dists = []
		obj_ew = []
		obj_knn = dic_knn[obj]
		# For each KNN vertex
		for i, nn in enumerate(obj_knn[1]):
			if obj == nn: continue
			nn_knn = dic_knn[nn]
			# If it is mutual
			if obj in nn_knn[1]:
				# Distance between obj and nn
				d1 = obj_knn[0][i]
				# Labeled nearst neabord and distance between nn and labeled nerast neabord
				(labeled, d2) = buff[nn]
				obj_dists.append(d1 + d2)
				# Tuple (edge, weight)
				obj_ew.append((obj, nn, 1 / (1 + d1)))

		for idx in np.argsort(obj_dists)[:ki]:
			ew.append(obj_ew[idx])

	sender.send(ew)

def main():
	"""Main entry point for the application when run from the command line"""

	# Parse options command line
	parser = OptionParser()
	usage = 'usage: python %prog [options] args ...'
	description = 'Graph Based on Informativeness of Labeled Instances'
	parser.add_option('-f', '--filename', dest='filename', help='Input file', metavar='FILE')
	parser.add_option('-o', '--output', dest='output', help='Output file', metavar='FILE')
	parser.add_option('-l', '--label', dest='label', help='Labels')
	parser.add_option('-1', '--ke', dest='ke', help='Knn', default=20)
	parser.add_option('-2', '--ki', dest='ki', help='Semi-supervised k', default=2)
	parser.add_option('-t', '--threads', dest='threads', help='Number of threads', default=4)
	parser.add_option('-e', '--format', dest='format', help='Format file', default='ncol')
	parser.add_option("-c", '--skip_last_column', action='store_false', dest='skip_last_column', default=True)

	# Process options and args
	(options, args) = parser.parse_args()
	ke = int(options.ke) # Knn
	ki = int(options.ki) # Semi-supervised K
	threads = int(options.threads) # Number of threads

	if options.filename is None:
		parser.error('required -f [filename] arg.')
	if options.format not in ['ncol', 'pajek']:
		parser.error('supported formats: ncol and pajek.')
	if options.label is None:
		parser.error('required -l [label] arg.')
	else:
		# Reading the labeled set of vertex
		f = open(options.label, 'r')
		labeled_set = [int(line.rstrip('\n')) for line in f]
	if options.output is None:
		filename, extension = os.path.splitext(os.path.basename(options.filename))
		if not os.path.exists('output'):
			os.makedirs('output')
		options.output = 'output/' + filename + '-gbili.' + options.format

	# Detect wich delimiter and which columns to use is used in the data
	with open(options.filename, 'r') as f:
		first_line = f.readline()
	sniffer = csv.Sniffer()
	dialect = sniffer.sniff(first_line)
	ncols = len(first_line.split(dialect.delimiter))
	if not options.skip_last_column: ncols -= 1

	# Reading data table
	# Acess value by data[object_id][attribute_id]
	# Acess all attributs of an object by data[object_id]
	# To transpose set arg unpack=True
	data = np.loadtxt(options.filename, delimiter=dialect.delimiter, usecols=range(0, ncols))
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
		p = Process(target=labeled_nearest, args=(obj_set[i:i + part], data, labeled_set, kdtree, ke, sender))
		p.daemon = True
		p.start()
		receivers.append(receiver)

	buff = dict()
	dic_knn = dict()
	for receiver in receivers:
		# Waiting threads
		(buff_aux, dic_knn_aux) = receiver.recv()
		buff.update(buff_aux)
		dic_knn.update(dic_knn_aux)

	# Starting GBILI processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=gbili, args=(obj_set[i:i + part], ki, buff, dic_knn, sender))
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
	if options.format == 'ncol':
		write_ncol(options.output, edgelist)
	else:
		write_pajek(options.output, obj_count, edgelist)

if __name__ == "__main__":
    sys.exit(main())
