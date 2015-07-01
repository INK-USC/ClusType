# ClusType

## Publication

* Xiang Ren\*, Ahmed El-Kishky, Chi Wang, Fangbo Tao, Clare R. Voss, Heng Ji, Jiawei Han, "**[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)**”, Proc. of 2015 ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD'15), Sydney, Australia, August 2015.

## Requirements

We will take Ubuntu for example.

* python 2.7
```
$ sudo apt-get install python
```
* numpy
```
$ sudo apt-get install pip
$ sudo pip install numpy
```
* scipy
```
$ sudo pip install scipy
```
* scikit-learn
```
$ sudo pip install sklearn
```
* TextBlob and dowmload training corpora
```
$ sudo pip install textblob
$ sudo python -m textblob.download_corpora
```
* lxml
```
$ sudo pip install lxml
```

## Default Run

```
$ ./run.sh  
```

## Parameters - run.sh
```
We will take Yelp dataset as an example.
```
DataPath='data/yelp'
```
RawText='data/yelp/yelp_sample50k.txt'
```
TypeFile='data/yelp/type_tid.txt'
```
StopwordFile='data/stopwords.txt'
```
FreebaseMapFile='data/freebase_links.nt'
```
SegmentOutFile='result/segment.txt'
```
SeedFile='result/seed.txt'
```
FreebaseKey='AIzaSyBvkZaBXc1GzVs3d0QN2HjTjDZwlgxboW4' # replace with your key
```
significance="1"
```
capitalize="1"
```
maxLength='4'
```
maximal phrase length
```
minSup='10'
```
minimal support for phrases in candidate generation
```
DataStatsFile='result/data_model_stats.txt'
```
data statistics on graph construction
```
NumRelationPhraseClusters='50'
```
number of relation phrase clusters
```
ResultFile='result/results.txt'
```
typed entity mentions
```
ResultFileInText='result/resultsInText.txt'
```
typed mentions annotated in segmented text