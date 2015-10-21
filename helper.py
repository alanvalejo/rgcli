#!/usr/bin/env python
# -*- coding: utf-8 -*-

def write_ncol(output, edgelist):
	with open(output, 'w') as f:
		f.write(edgelist)

def write_pajek(output, obj_count, edgelist):
	with open(output, 'w') as f:
		f.write('*Vertices ' + str(obj_count) + '\n')
		for i in range(0, obj_count):
			f.write(str(i+1) + ' \"' + str(i) + '\"\n')
		f.write('*Edges ' + '\n')
		for line in edgelist.split('\n'):
			if len(line.split(' ')) == 1: break
			u, v, w = line.split(' ')
			f.write(str(int(u) + 1) + ' ' + str(int(v) + 1) + ' ' + w + '\n')
