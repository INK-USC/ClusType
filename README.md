# ClusType

## Publication

* [Xiang Ren](http://web.engr.illinois.edu/~xren7/)\*, Ahmed El-Kishky, Chi Wang, Fangbo Tao, Clare R. Voss, Heng Ji, Jiawei Han, "**[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)**”, Proc. of 2015 ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD'15), Sydney, Australia, August 2015. ([Slides](http://web.engr.illinois.edu/~xren7/KDD15-ClusType_v3.pdf))

* [Xiang Ren](http://web.engr.illinois.edu/~xren7/)\*, Ahmed El-Kishky, Chi Wang, Jiawei Han, "**[Automatic Entity Recognition and Typing from Massive Text Corpora: A Phrase and Network Mining Approach](http://research.microsoft.com/en-us/people/chiw/kdd15tutorial.aspx)**”, Proc. of 2015 ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD'15 Conference Tutorial), Sydney, Australia, August 2015. ([Website](http://research.microsoft.com/en-us/people/chiw/kdd15tutorial.aspx)) ([Slides](http://hanj.cs.illinois.edu/kdd-15/UIUC-Tutorial.pdf))

## Note

"./result" folder contains results on a sample of 50k Yelp reviews.

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
* TextBlob and data for its POS tagger
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

Input: dataset folder. There are one sample Yelp review dataset (yelp) and one NYT news dataset (nyt).
```
DataPath='data/yelp'
```

Input data file path.
- Format: "docId \TAB document \n".
```
RawText='data/yelp/yelp_sample50k.txt'
```

Input: type mapping file path.
- Format: "type name \TAB typeId \n". "NIL" means "Not-of-Interest".
```
TypeFile='data/yelp/type_tid.txt'
```

Input: stopword list.
```
StopwordFile='data/stopwords.txt'
```

Output: output file from candidate generation.
- Format: "docId \TAB segmented sentence \n".
- Segments are separated by ",". Entity mention candidates are marked with ":EP". Relation phrases are marked with ":RP".
```
SegmentOutFile='result/segment.txt'
```

Output: entity linking output file.
- Format: "docId \TAB entity name \TAB Original Freebase Type \TAB Refined Type \TAB Freebase EntityID \TAB Similarity Score \TAB Relative Rank \n". 
- Download [Seed file](https://www.dropbox.com/s/w628rwpb3kbmuea/seed_yelp.txt?dl=0) for Yelp dataset. 
- Download [Seed file](https://www.dropbox.com/s/k0qzsvbbpngptjt/seed_nyt.txt?dl=0) for NYT dataset.

NOTE: Our entity linking module calls [DBpediaSpotLight Web service](https://github.com/dbpedia-spotlight/dbpedia-spotlight/wiki/Web-service), which has limited querying speed. This process can be largely accelarated by installing the tool on your local machine [Link](https://github.com/dbpedia-spotlight/dbpedia-spotlight/wiki/Installation).
```
SeedFile='result/seed.txt'
```

Output: data statistics on graph construction.
```
DataStatsFile='result/data_model_stats.txt'
```

Output: Typed entity mentions.
- Format: "docId \TAB entity mention \TAB entity type \n".
```
ResultFile='result/results.txt'
```

Output: Typed mentions annotated in the segmented text. 
```
ResultFileInText='result/resultsInText.txt'
```

## Parameters - run.sh

Threshold on significance score for candidate generation.
```
significance="1"
```

Switch on capitalization feature for candidate generation.
```
capitalize="1"
```

Maximal phrase length for candidate generation.
```
maxLength='4'
```

Minimal support of phrases for candidate generation.
```
minSup='10'
```

Number of relation phrase clusters.
```
NumRelationPhraseClusters='50'
```