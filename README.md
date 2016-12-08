## RGCLI

**About**

This is an alternative Python implementation of graph construction method RGCLI (Robust Graph that Considers Labeled Instances), published by Berton and Lopes (2016) [1]. The implementation is based on Kd-tree and Multi-threading and is faster than the original described in the paper, specially for large data sets.

**Usage**

> RGCLI execution

    `python gbili.py -f input/dataset.dat -l input/dataset.labels -1 20 -2 2`

> Input: any numerical dataset with any delimiter for attributes

> Output: a weighted undirected graph in the format: filename + '-gbili.ncol'

**Parameters**

* -f (dataset as input file)
* -o (output file default .ncol list)
* -l (list of labels points used to construct RGCLI graph in the format edgelist with a blank line)
* -1 (ke for KNN default 20)
* -2 (ki for RGCLI default 2)
* -t (number of  threads default 4)
* -c (skip the last column)

**References**

> [1] Berton, Lilian; Faleiros, T.; Valejo, A.; Valverde-Rebaza, J.; and Lopes, A. A.: RGCLI: Robust Graph that Considers Labeled Instances for Semi-Supervised Learning. Neurocomputing, (2016)

~~~~~{.bib}
@article{Berton_2016,
    author={Lilian Berton and Thiago de Paulo Faleiros and Alan Valejo and Jorge Valverde-Rebaza and Alneu de Andrade Lopes},
    title={RGCLI: Robust Graph that Considers Labeled Instances for Semi-Supervised Learning},
	journal={Neurocomputing},
    year={2016}
}
~~~~~
