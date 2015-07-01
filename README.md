# ClusType

## Publication

* Xiang Ren\*, Ahmed El-Kishky, Chi Wang, Fangbo Tao, Clare R. Voss, Heng Ji, Jiawei Han, "**[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)**”, Proc. of 2015 ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD'15), Sydney, Australia, August 2015. [Slides](http://web.engr.illinois.edu/~xren7/KDD15-ClusType_v1.pdf)

## Note

"./result" folder contains typed entity mentions on a sample of 50k Yelp reviews.

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

## File path setting - run.sh

We will take Yelp dataset as an example.

```
DataPath='data/yelp'
```
Input: dataset folder. There are one sample Yelp review dataset (yelp) and one NYT news dataset (nyt).

```
RawText='data/yelp/yelp_sample50k.txt'
```
Input data file path.

```
TypeFile='data/yelp/type_tid.txt'
```
Input: type mapping file path. Format: "type name \tab typeId". "NIL" means "Not-of-Interest".

```
StopwordFile='data/stopwords.txt'
```
Input: stopword list.

```
FreebaseMapFile='data/freebase_links.nt'
```
Input: Freebase type mapping; please download from [here](https://www.dropbox.com/s/fse5wyjevq8etmo/freebase_links.nt?dl=0). This is used in entity linking module to map entities between DBpedia and Freebase. 

```
SegmentOutFile='result/segment.txt'
```
Output: output file from candidate generation. Format: "docId \TAB sentence". Segments are separated by ",". Entity mention candidates are marked with "：EP". Relation phrases are marked with ":RP".

```
SeedFile='result/seed.txt'
```
Output: entity linking output file. Format: "docId \TAB entity name \TAB Original Freebase Type \TAB Refined Type \TAB Freebase EntityID \TAB Similarity Score \TAB Relative Rank". Seed file for Yelp dataset can be download from [here](https://www.dropbox.com/s/w628rwpb3kbmuea/seed_yelp.txt?dl=0). Seed file for NYT dataset can be downloaded from [here](https://www.dropbox.com/s/k0qzsvbbpngptjt/seed_nyt.txt?dl=0).

```
DataStatsFile='result/data_model_stats.txt'
```
Output: data statistics on graph construction.

```
ResultFile='result/results.txt'
```
Output: Typed entity mentions. Format: "docId \TAB entity mention \TAB entity type".

```
ResultFileInText='result/resultsInText.txt'
```
Output: Typed mentions annotated in the segmented text. 

```
FreebaseKey='AIzaSyBvkZaBXc1GzVs3d0QN2HjTjDZwlgxboW4' 
```
Please replace with your own key; Apply from [here](https://code.google.com/apis/console). Note: the FreebaseAPI is shutting donw. We will update the entity linking module with new API soon.

## Parameters - run.sh

```
significance="1"
```
Threshold on significance score for candidate generation.

```
capitalize="1"
```
Switch on capitalization feature for candidate generation.

```
maxLength='4'
```
Maximal phrase length for candidate generation.

```
minSup='10'
```
Minimal support of phrases for candidate generation.

```
NumRelationPhraseClusters='50'
```
Number of relation phrase clusters.

