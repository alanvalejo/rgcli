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
import logging
import rgcli

from scipy import spatial
from multiprocessing import Pipe, Process

__maintainer__ = 'Alan Valejo'
__author__ = 'Alan Valejo, Thiago Faleiros'
__email__ = 'alanvalejo@gmail.com', 'thiagodepaulo@gmail.com'
__credits__ = ['Alan Valejo', 'Thiago Faleiros', 'Lilian Berton', 'Jorge Valverde-Rebaza', 'Alneu de Andrade Lopes']
__homepage__ = 'https://github.com/alanvalejo/rgcli'
__license__ = 'GNU'
__docformat__ = 'markdown en'
__version__ = '0.1'
__date__ = '2016-12-01'

def main():
	""" Main entry point for the application when run from the command line. """

	# Parse options command line
	description = 'Graph Based on Informativeness of labeled instances'
	parser = argparse.ArgumentParser(description=description, formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30, width=100))
	parser._action_groups.pop()

	required = parser.add_argument_group('required arguments')
	required.add_argument('-f', '--filename', required=True, dest='filename', action='store', type=str, metavar='FILE', default=None, help='name of the %(metavar)s to be loaded')
	required.add_argument('-l', '--label', required=True, dest='label', action='store', type=str, metavar='FILE', default=None, help='list of labels points used to construct RGCLI')

	optional = parser.add_argument_group('optional arguments')
	optional.add_argument('-d', '--directory', dest='directory', action='store', type=str, metavar='DIR', default=None, help='directory of FILE if it is not current directory')
	optional.add_argument('-o', '--output', dest='output', action='store', type=str, metavar='FILE', default=None, help='name of the %(metavar)s to be save')
	optional.add_argument('-1', '--ke', dest='ke', action='store', type=int, metavar='int', default=20, help='kNN (default: %(default)s)')
	optional.add_argument('-2', '--ki', dest='ki', action='store', type=int, metavar='int', default=2, help='semi-supervised k (default: %(default)s)')
	optional.add_argument('-t', '--threads', dest='threads', action='store', type=int, metavar='int', default=4, help='number of threads (default: %(default)s)')
	optional.add_argument('-e', '--format', dest='format', action='store', choices=['ncol', 'pajek'], type=str, metavar='str', default='ncol', help='format output file. Allowed values are ' + ', '.join(['ncol', 'pajek']) + ' (default: %(default)s)')
	optional.add_argument('-c', '--skip_last_column', dest='skip_last_column', action='store_false', default=True, help='skip last column (default: %(default)s)')

	required.add_argument('--required_arg')
	optional.add_argument('--optional_arg')
	options = parser.parse_args()

	# Instanciation and init Log
	log = logging.getLogger('OPM')
	level = logging.WARNING
	logging.basicConfig(level=level, format="%(message)s")

	# Process options and args
	if options.format not in ['ncol', 'pajek']:
		log.warning('supported formats: ncol and pajek.')
		sys.exit(1)
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

	# Reading the labeled set of vertex
	f = open(options.label, 'r')
	labeled_set = [int(line.rstrip('\n')) for line in f]

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
		p = Process(target=rgcli.labeled_nearest, args=(obj_set[i:i + part], data, labeled_set, kdtree, options.ke, sender))
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

	# Starting RGCLI processing
	receivers = []
	for i in xrange(0, obj_count, part):
		sender, receiver = Pipe()
		p = Process(target=rgcli.rgcli, args=(obj_set[i:i + part], options.ki, buff, dic_knn, sender))
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
		rgcli.write_ncol(options.output, edgelist)
	else:
		rgcli.write_pajek(options.output, obj_count, edgelist)

if __name__ == "__main__":
	sys.exit(main())
