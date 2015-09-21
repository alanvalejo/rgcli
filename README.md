# GBILI
**About**

This is an alternative Python implementation of graph construction method GBILI (graph based on the informativeness of labeled instances), published by Berton and Lopes (2014) [1]. The implementation is based on Kd-tree and Multithreading and is faster than the original described in the paper, specially for large data sets. 

**Usage**

Declare an array of datasets
`datasets=(dataset1 dataset2 dataset3)`

Now loop through the above datasets
`for dataset in "${datasets[@]}"
do
	echo ${dataset}
	gbili=()`
	
Execute GBILI
	`START=$(date +%s.%N)
	python gbili.py -f input/${dataset}.dat -l input/${dataset}.labels --k1=2 --k2=20
	END=$(date +%s.%N)
	DIFF=$(echo "$END - $START" | bc)
	gbili[${itr}]=$DIFF`

Obs:
The implementation supports any numerical dataset as input and the output is a weighted undirected graph.
Results are written to a list of connections, one connection per line.

**References**

[1] @inproceedings{Berton_Lopes_2014,
  title = {Graph construction based on labeled instances for Semi-Supervised Learning}, 
  author = {Lilian Berton and Alneu de Andrade Lopes}, 
  booktitle = {22nd International Conference on Pattern Recognition}, 
  keywords = {graph construction; semi-supervised learning; classification; complex network}, 
  doi = {10.1109/ICPR.2014.428},
  year = {2014},
  pages = {2477-2482},
}
