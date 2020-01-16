# On Strategyproof Conference Peer Review
This repository contains code and data for paper [On Strategyproof Conference Peer Review](https://arxiv.org/pdf/1806.06266.pdf). A shorter version is present in IJCAI 2019:

Yichong Xu\*, Han Zhao\*, Xiaofei Shi, Nihar Shah <br/>
[On Strategyproof Conference Peer Review](https://arxiv.org/pdf/1806.06266.pdf)</br>
Proceedings of the Twenty-Eighth International Joint Conference on Artificial Intelligence, IJCAI-19</br>
​(\*: equal contribution) </br>

Please cite the above paper if you use this code or data. 

## Compare Similarity Scores
1. To compare the similarity score with Divide-and-Rank partition and without:

``` > cd DivideClusters ```

``` > python compare_sim.py ```

2. To compute the similarity score with random partition: In the same folder run

``` > python compare_sim.py --compute_random```

## Use similarity matrix

The matrix is at ```iclr2018.npz```. Each line corresponds to an author and each column corresponds to a paper. The score between [0,1] represents the similarity.

