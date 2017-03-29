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

__maintainer__ = 'Alan Valejo'
__author__ = 'Alan Valejo, Thiago Faleiros'
__email__ = 'alanvalejo@gmail.com', 'thiagodepaulo@gmail.com'
__credits__ = ['Alan Valejo', 'Thiago Faleiros', 'Lilian Berton', 'Jorge Valverde-Rebaza', 'Alneu de Andrade Lopes']
__homepage__ = 'https://github.com/alanvalejo/rgcli'
__license__ = 'GNU'
__docformat__ = 'markdown en'
__version__ = '0.1'
__date__ = '2016-12-01'

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
