# GBILI
**About**

This is an alternative Python implementation of graph construction method GBILI (graph based on the informativeness of labeled instances), published by [Berton and Lopes (2014)] ([1]). The implementation is based on Kd-tree and Multithreading and is faster than the original described in the paper, specially for large data sets. 

**Usage**

*GBILI execution*:  `python gbili.py -f input/dataset.dat -l input/dataset.labels -1 20 -2 2`

*Input*: any numerical dataset with any delimiter for attributes 

*Output*: a weighted undirected graph in the format: filename + '-gbili.ncol'

*Parameters*: 
* -f (dataset as input file)
* -o (output file default .ncol list)
* -l (list of labels points used to construct GBILI graph in the format edgelist with a blank line)
* -1 (ke for KNN default 20)
* -2 (ki for GBILI default 2)
* -t (number of  threads default 4)
* -c (skip the last column). 

**References**

@inproceedings{Berton_Lopes_2014,   
 title = {Graph construction based on labeled instances for Semi-Supervised Learning},   
 author = {Lilian Berton and Alneu de Andrade Lopes},   
 booktitle = {22nd International Conference on Pattern Recognition},   
 keywords = {graph construction; semi-supervised learning; classification; complex network},    
 doi = {10.1109/ICPR.2014.428},   
 year = {2014},   
 pages = {2477-2482},   
}
