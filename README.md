# ClusType

## Publication

* Xiang Ren\*, Ahmed El-Kishky, Chi Wang, Fangbo Tao, Clare R. Voss, Heng Ji, Jiawei Han, "**[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)**”, Proc. of 2015 ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD'15), Sydney, Australia, August 2015.

## Note
The results on a sample of 50k Yelp reviews are in ./result folder.

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

We will take Yelp dataset as an example.

Input: dataset folder
```
DataPath='data/yelp'
```

Input: data file path
```
RawText='data/yelp/yelp_sample50k.txt'
```

Input: type mapping file path (type name \tab typeId)
```
TypeFile='data/yelp/type_tid.txt'
```

Input: stopword list
```
StopwordFile='data/stopwords.txt'
```

Input: Freebase type mapping; please download from [here](https://www.dropbox.com/s/nwwi0ig71fb3w2r/freebase_links.nt?dl=0)
```
FreebaseMapFile='data/freebase_links.nt'
```

Output: candidate generation output file
```
SegmentOutFile='result/segment.txt'
```

Output: entity linking output file
```
SeedFile='result/seed.txt'
```

Please replace with your own key; Apply from [here](https://code.google.com/apis/console)
```
FreebaseKey='AIzaSyBvkZaBXc1GzVs3d0QN2HjTjDZwlgxboW4' 
```

Threshold on significance score for candidate generation
```
significance="1"
```

Switch on capitalization feature for candidate generation
```
capitalize="1"
```

Maximal phrase length for candidate generation
```
maxLength='4'
```

Minimal support of phrases for candidate generation
```
minSup='10'
```

data statistics on graph construction
```
DataStatsFile='result/data_model_stats.txt'
```

number of relation phrase clusters
```
NumRelationPhraseClusters='50'
```

Output: Typed entity mentions
```
ResultFile='result/results.txt'
```


Output: Typed mentions annotated in segmented text
```
ResultFileInText='result/resultsInText.txt'
```
