## RGCLI

**About**

This is an alternative Python implementation of graph construction method RGCLI (Robust Graph that Considers Labeled Instances), published by Berton and Lopes (2016) [1]. The implementation is based on kd-tree and Multi-threading and is faster than the original described in the paper, specially for large data sets.

**Download**

- You can download the RGCLI software in http://www.alanvalejo.com.br/software?name=rgcli

**Usage**

> RGCLI execution

    python main.py -f input/square.dat -l input/square.label -1 20 -2 2 -d output

> Input: any numerical dataset with any delimiter for attributes

> Output: a weighted undirected graph in the format: filename + '-gbili.ncol'

**Parameters**

| Option					| Domain					| Required	| Default	| Description															|
|:------------------------- |:------------------------- | --------- | --------- |:--------------------------------------------------------------------- |
| -f, --filename			| string [FILE]				| yes		| -			| dataset as input file													|
| -o, --output				| string [FILE]				| no		| ncol		| output file															|
| -l, --label				| string [FILE]				| yes		| -			| list of labels points used to construct RGCLI 						|
| -1, --ke					| [1,n] Integer interval	| no		| 20		| ke for KNN															|
| -2, --ki					| [1,n] Integer interval	| no		| 2			| ki for RGCLI															|
| -t, --threads				| [0,n] Integer interval	| no		| 4			| number of  threads													|
| -e, --format				| ['ncol', 'pajek']			| no		| ncol		| format output file													|
| -c, --skip_last_column	| bool						| no		| true		| skip the last column													|
| -c, --skip_rows	        | [1,n-1]					| no		| None		| skip rows													            |

**Instal**

> Pip
    
    $ pip install -r /path/to/requirements.txt

> Anaconda env

    $ conda env create -f environment.yml
    $ conda activate rgcli

> Anaconda create

    $ conda create --name rgcli python=3.7.2
    $ conda activate rgcli
    $ conda install -c anaconda numpy
    $ conda install -c anaconda scipy 

**Known Bugs**

- Please contact the author for problems and bug report

**Contact**

- Alan Valejo.
- Ph.D. candidate at University of São Paulo (USP), Brazil.
- alanvalejo@icmc.ups.br.

**License and credits**

- The GNU General Public License v3.0
- Giving credit to the author by citing the papers [1]

**References**

> [1] Berton, Lilian and Faleiros, Thiago P. and Valejo, Alan and Valverde-Rebaza, Jorge Lopes, A. A., Rgcli: robust graph that considers labeled instances for semi-supervised learning, in Neurocomputing, p. 238-248, vol. 226, 2016, doi: https://doi.org/10.1016/j.neucom.2016.11.053

~~~~~{.bib}
@article{berton2016rgcli,
    author = {Berton, Lilian and Faleiros, Thiago P. and Valejo, Alan and Valverde-Rebaza, Jorge Lopes, A. A.},
    title = {Rgcli: robust graph that considers labeled instances for semi-supervised learning},
    journal = {Neurocomputing},
    year = {2016},
    pages = {238-248},
    volume = {226},
    doi = {https://doi.org/10.1016/j.neucom.2016.11.053}
}
~~~~~

<div class="footer"> &copy; Copyright (C) 2016 Alan Valejo &lt;alanvalejo@gmail.com&gt; All rights reserved.</div>
