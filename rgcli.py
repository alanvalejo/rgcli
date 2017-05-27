#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RGCLI (Robust Graph that Considers Labeled Instances)
=====================================================

Copyright (C) 2016 Alan Valejo <alanvalejo@gmail.com> All rights reserved
Copyright (C) 2016 Thiago Faleiros <thiagodepaulo@gmail.com> All rights reserved

To exploit the informativeness conveyed by these few labeled
instances available in semi-supervised scenarios.

This file is part of RGCLI.

RGCLI is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RGCLI is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RGCLI. If not, see <http://www.gnu.org/licenses/>.
"""

import csv
import os
import sys
import argparse
import numpy as np

from scipy import spatial
from multiprocessing import Pipe, Process
from helper import write_ncol, write_pajek

__maintainer__ = 'Alan Valejo'
__author__ = 'Alan Valejo, Thiago Faleiros'
__email__ = 'alanvalejo@gmail.com', 'thiagodepaulo@gmail.com'
__credits__ = ['Alan Valejo', 'Thiago Faleiros', 'Lilian Berton', 'Jorge Valverde-Rebaza', 'Alneu de Andrade Lopes']
__homepage__ = 'https://github.com/alanvalejo/rgcli'
__license__ = 'GNU'
__docformat__ = 'markdown en'
__version__ = '0.1'
__date__ = '2016-12-01'

def labeled_nearest(obj_subset, data, labeled_set, kdtree, ke, sender):
	"""	Check the set of labeled nearest for all vertices.

	Args:
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
	""" GBILI kernel

	Args:
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
	""" Main entry point for the application when run from the command line. """

	# Parse options command line
	usage = 'use "%(prog)s --help" for more information'
	description = 'graph Based on Informativeness of Labeled Instances'
	parser = argparse.ArgumentParser(description=description, usage=usage, formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30, width=100))
	optional = parser._action_groups.pop()
	required = parser.add_argument_group('required arguments')
	required.add_argument('-f', '--filename', dest='filename', action='store', type=str, metavar='FILE', default=None, help='name of the %(metavar)s to be loaded')
	optional.add_argument('-d', '--directory', dest='directory', action='store', type=str, metavar='DIR', default=None, help='directory of FILE if it is not current directory')
	optional.add_argument('-o', '--output', dest='output', action='store', type=str, metavar='FILE', default=None, help='name of the %(metavar)s to be save')
	required.add_argument('-l', '--label', dest='label', action='store', type=str, metavar='FILE', default=None, help='list of labels points used to construct RGCLI')
	optional.add_argument('-1', '--ke', dest='ke', action='store', type=int, metavar='int', default=20, help='kNN (default: %(default)s)')
	optional.add_argument('-2', '--ki', dest='ki', action='store', type=int, metavar='int', default=2, help='semi-supervised k (default: %(default)s)')
	optional.add_argument('-t', '--threads', dest='threads', action='store', type=int, metavar='int', default=4, help='number of threads (default: %(default)s)')
	optional.add_argument('-e', '--format', dest='format', action='store', choices=['ncol', 'pajek'], type=str, metavar='str', default='ncol', help='format output file. Allowed values are ' + ', '.join(['ncol', 'pajek']) + ' (default: %(default)s)')
	optional.add_argument('-c', '--skip_last_column', dest='skip_last_column', action='store_false', default=True, help='skip last column (default: %(default)s)')
	parser._action_groups.append(optional)
	options = parser.parse_args()

	# Process options and args
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
	if options.directory is None:
		options.directory = os.path.dirname(os.path.abspath(options.filename))
	else:
		if not os.path.exists(options.directory): os.makedirs(options.directory)
	if not options.directory.endswith('/'): options.directory += '/'
	if options.output is None:
		filename, extension = os.path.splitext(os.path.basename(options.filename))
		options.output = options.directory + filename + '-rgcli' + '_' + str(options.ki) + '_' + str(options.ke) + '.' + options.format
	else:
		options.output = options.directory + options.output

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
	part = obj_count / options.threads

	# Creating list of labeled nearst neighours
	receivers = []
	for i in xrange(0, obj_count, part):
		# Returns a pair (conn1, conn2) of Connection objects representing the ends of a pipe
		sender, receiver = Pipe()
		p = Process(target=labeled_nearest, args=(obj_set[i:i + part], data, labeled_set, kdtree, options.ke, sender))
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
		p = Process(target=gbili, args=(obj_set[i:i + part], options.ki, buff, dic_knn, sender))
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
