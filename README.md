# GBILI
**About**

This is an alternative Python implementation of graph construction method GBILI (graph based on the informativeness of labeled instances), published by [Berton and Lopes (2014)] ([1]). The implementation is based on Kd-tree and Multithreading and is faster than the original described in the paper, specially for large data sets. 

**Usage**

Execute GBILI
	`python gbili.py -f input/${dataset}.dat -l input/${dataset}.labels --ki=2 --ke=20`

Obs:
The implementation supports any numerical dataset as input and the output is a weighted undirected graph.

Results are written to a list of connections, one connection per line.

Parameters k1 and k2 need to be set with integer values. In general k1 < k2. 

**References**

@inproceedings{Berton_Lopes_2014,
 * title = {Graph construction based on labeled instances for Semi-Supervised Learning}, 
 * author = {Lilian Berton and Alneu de Andrade Lopes}, 
 * booktitle = {22nd International Conference on Pattern Recognition}, 
 * keywords = {graph construction; semi-supervised learning; classification; complex network}, 
 * doi = {10.1109/ICPR.2014.428},
 * year = {2014},
 * pages = {2477-2482},
}
