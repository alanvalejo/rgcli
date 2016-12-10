#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
kNN
K nearest neighbor graph construction
==========================

:Author: Alan Valejo <alanvalejo@gmail.com>, Thiago Faleiros <thiagodepaulo@gmail.com>

The nearest neighbor or, in general, the k nearest neighbor (kNN) graph of a data set is obtained by connecting each instance in the data set to its k closest instances from the data set, where a distance metric defines closeness.
"""

import numpy as np
import os
import sys
import csv

from helper import write_ncol
from helper import write_pajek
from multiprocessing import Pipe
from multiprocessing import Process
from optparse import OptionParser
from scipy import spatial

__author__ = 'Alan Valejo, Thiago Faleiros'
__email__ = 'alanvalejo@gmail.com', 'thiagodepaulo@gmail.com'
__maintainer__ = 'Alan Valejo'
__credits__ = ['Alan Valejo, Thiago Faleiros']
__license__ = 'GNU'
__docformat__ = 'restructuredtext en'
__version__ = '0.1'
__date__ = '2016-12-01'

def knn(obj_subset, data, kdtree, k, sender):
	""" K nearest neighbor graph construction.

	Args:
		obj_subset (array): Set of vertices by threads
		data (np.array): Original data table
		kdtree (spatial.KDTree): KD tree accounting for from data
		k (int): K nearest neighbors
		sender (multiprocessing.Connection): Pipe connection objects
	"""

	ew = [] # Set of weighted edges
	for obj in obj_subset:
		obj_attrs = data[obj]
		obj_knn = kdtree.query(obj_attrs, k=(k + 1))
		# For each KNN vertex
		for i, nn in enumerate(obj_knn[1]):
			if obj == nn: continue
			d1 = obj_knn[0][i]
			ew.append((obj, nn, 1 / (1 + d1)))

	sender.send(ew)

def main():
	""" Main entry point for the application when run from the command line. """

	# Parse options command line
	parser = OptionParser()
	usage = 'usage: python %prog [options] args ...'
	description = 'kNN Graph Construction'
	parser.add_option('-f', '--filename', dest='filename', help='Input file', metavar='FILE')
	parser.add_option('-o', '--output', dest='output', help='Output file', metavar='FILE')
	parser.add_option('-k', '--k', dest='k', help='kNN', default=3)
	parser.add_option('-t', '--threads', dest='threads', help='Number of threads', default=4)
	parser.add_option('-e', '--format', dest='format', help='Format file', default='ncol')
	parser.add_option("-c", '--skip_last_column', action='store_false', dest='skip_last_column', default=True)

	# Process options and args
	(options, args) = parser.parse_args()
	k = int(options.k) # kNN
	threads = int(options.threads) # Number of threads

	if options.filename is None:
		parser.error('required -f [filename] arg.')
	if options.format not in ['ncol', 'pajek']:
		parser.error('supported formats: ncol and pajek.')
	if options.output is None:
		filename, extension = os.path.splitext(os.path.basename(options.filename))
		if not os.path.exists('output'):
			os.makedirs('output')
		options.output = 'output/' + filename + '-knn' + str(options.k) + '.' + options.format

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

	# Starting Knn processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=knn, args=(obj_set[i:i + part], data, kdtree, k, sender))
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
