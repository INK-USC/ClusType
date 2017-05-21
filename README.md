# ClusType

Source code for SIGKDD'15 paper *[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)* ([Slides](http://web.engr.illinois.edu/~xren7/KDD15-ClusType_v3.pdf))

## Dependencies

* python 2.7
* numpy, scipy, scikit-learn, lxml, TextBlob and related corpora
```
$ sudo pip install numpy scipy sklearn lxml textblob
$ sudo python -m textblob.download_corpora
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

Input: Download [Freebase-to-DBpedia mapping file](https://drive.google.com/open?id=0Bw2KHcvHhx-gQ2RJVVJLSHJGYlk). Place it under "data/" directory
```
FreebaseMap='data/freebase_links.nt'
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


## Reference

```
@inproceedings{ren2015clustype,
  title={Clustype: Effective entity recognition and typing by relation phrase-based clustering},
  author={Ren, Xiang and El-Kishky, Ahmed and Wang, Chi and Tao, Fangbo and Voss, Clare R and Han, Jiawei},
  booktitle={Proceedings of the 21th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  pages={995--1004},
  year={2015},
  organization={ACM}
}
```
