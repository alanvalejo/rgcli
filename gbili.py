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

def read_labels(file):
	"""
	Read file with labels
	Attributes:
		file (string): input file whit labels
	Returns:
		dictionary: List of vertices <vertice, label>
	"""

	vertices, labels = [], dict()
	with open(file, 'r') as f:
		for line in f:
			line = line.split()
			vertex = int(line[0])
			label = int(line[1])
			vertices.append(vertex)
			labels[vertex] = label
	return(vertices, labels)

def labeled_nearest(vertex_set, graph, labeled, tree, sender):
	"""
	Verify for each vertex which are the nearest labeled vertices
	Attributes:
		vertex_set ():
		graph (igraph): Set of vertices
		labeled ():
		tree ():
		sender ():
	"""

	buff = dict()
	dic_nn = dict()
	for v in vertex_set:
		if v.index % 10000 == 0:
			print v.index
		min_d = float('inf')
		min_l = -1
		v_pts = [v["x"], v["y"], v["r"], v["g"], v["b"]]
		for u_idx in labeled:
			u = graph.vs()[u_idx]
			d = ((v_pts[0] - u["x"])**2 + (v_pts[1] - u["y"])**2 + (v_pts[2] - u["r"])**2 + (v_pts[3] - u["g"])**2 + (v_pts[4] - u["b"])**2)
			if d < min_d:
				min_d = d
				min_l = u_idx
		buff[v.index] = (min_l, min_d)

		# atribui lista de k vizinhos mais proximos
		dic_nn[v.index] = tree.query(np.array([v_pts]), k=(k+1))

	sender.send((buff, dic_nn))


def cal_NN(vertex_set, tree, k1, k2, buff, sender, dic_nn):

	#print k2
	l = []
	for v in vertex_set:
		if v.index % 10000 == 0:
			print v.index

		l_dists = []
		l_ew = []
		list_v_nn = dic_nn[v.index] # tree.query(np.array([[v["x"], v["y"], v["r"], v["g"], v["b"]]]), k=(k1+1));
		# for each KNN vertex
		for i, nn in enumerate(list_v_nn[1][0]):
			if nn == v.index:
				continue
			u = graph.vs()[nn]
			list_u_nn = dic_nn[nn] #tree.query(np.array([[u["x"], u["y"], u["r"], u["g"], u["b"]]]), k=(k1+1))
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


if __name__ == '__main__':

	parser = OptionParser()

	usage = "usage: python %prog [options] args ..."
	description = """Description"""
	parser.add_option("-f", "--file", dest="filename", help="read FILE", metavar="FILE")
	parser.add_option("-1", "--knn", dest="k", help="knn")
	parser.add_option("-2", "--semiknn", dest="semik", help="semiknn")
	parser.add_option("-l", "--labels", dest="labels", help="labels FILE")
	parser.add_option("-t", "--nthreads", dest="nthreads", help="number of threads", default=4)
	parser.add_option("-o", "--out", dest="out_filename", help="write FILE", metavar="OUTFILE")
	parser.add_option("-c", "--ncluster", dest="nclusters", help="number of clusters", metavar="nclusters")

	(options, args) = parser.parse_args()
	filename = options.filename
	k = int(options.k)			# k1
	k2 = int(options.semik)			# k2
	labels_filename = options.labels	# vertices rotulados
	out_filename = options.out_filename
	n_threads = int(options.nthreads)
	c = int(options.nclusters)		# numero de clusters

	if filename is None:
		parser.error("required -f [filename] arg.")
	if labels_filename is None:
		parser.error("required -l [labels file] arg.")

	graph = igraph.Graph()
	graph.to_undirected()
	im = Image.open(filename)
	pix = im.load()
	x, y, r, g, b = [], [], [], [], []

	# Labeled set
	labeled, map_labels = read_labels(labels_filename)

	for j in range(0,im.size[1]):
		for i in range(0,im.size[0]):
			graph.add_vertex()
			vertex = graph.vs[graph.vcount()-1]
			vertex["name"] = vertex.index
			vertex["x"] = i
			vertex["y"] = j
			vertex["r"] = pix[i,j][0]
			vertex["g"] = pix[i,j][1]
			vertex["b"] = pix[i,j][2]
			x.append(i)
			y.append(j)
			r.append(pix[i,j][0])
			g.append(pix[i,j][1])
			b.append(pix[i,j][2])

	x = np.array(x)
	y = np.array(y)
	r = np.array(r)
	g = np.array(g)
	b = np.array(b)
	tree = spatial.KDTree(zip(x.ravel(), y.ravel(), r.ravel(), g.ravel(), b.ravel()))

	# atribui para os rotulados mais proximos

	# divide em subconjuntos de vertices pelo numero de threads
	# subconjunto de vertices (V = {V_1, ..., V_{n_threads})
	part = len(graph.vs())/n_threads

	# ******************************************
	lq = []
	l_threads = []
	for i in xrange(0, len(graph.vs()), part ):
		sender, receiver = Pipe()
		p = Process(target=labeled_nearest, args=(graph.vs()[i:i+part], graph, labeled, tree, sender))
		p.daemon = True
		p.start()
		lq.append(receiver)
		l_threads.append(p)

	buff = dict()
	dic_nn = dict()
	for receiver in lq:
		(buff_p, dic_nn_p) = receiver.recv()
		buff.update(buff_p)
		dic_nn.update(dic_nn_p)
	# ******************************************

	lq = []
	l_threads = []
	for i in xrange(0, len(graph.vs()), part ):
		sender, receiver = Pipe()
		p = Process(target=cal_NN, args=(graph.vs()[i:i+part], tree, k, k2, buff, sender, dic_nn))
		p.daemon = True
		p.start()
		l_threads.append(p)
		lq.append(receiver)

	edges = []
	weights = []
	for receiver in lq:
		l_ew = receiver.recv()
		for edge, weight in l_ew:
			edges += [edge]
			weights.append(weight)

	graph.add_edges(edges)
	graph.es["weight"] = weights

	graph.simplify(combine_edges='first')
	graph.write(out_filename, format='edgelist')