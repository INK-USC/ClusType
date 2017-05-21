# ClusType

Source code for SIGKDD'15 paper *[ClusType: Effective Entity Recognition and Typing by Relation Phrase-Based Clustering](http://web.engr.illinois.edu/~xren7/fp611-ren.pdf)* ([Slides](http://web.engr.illinois.edu/~xren7/KDD15-ClusType_v3.pdf)). 

Given a *text corpus* (e.g., a collection of news articles), it performs automatically [entity extraction and typing](https://en.wikipedia.org/wiki/Named-entity_recognition) using [distant supervision](http://deepdive.stanford.edu/distant_supervision) (i.e., examples from external knowledge bases like Freebase). For example, from the sentence "`The best BBQ I’ve tasted in Phoenix `" the system will recognize `BBQ` as *food* and `phoenix` as *location*. More background can be found in our [WWW'16 tutorial](http://web.engr.illinois.edu/~elkishk2/www2016/).

ClusType works on coarse-grained entity types (e.g., Person, Location, Organization); for more fine-grained entity typing, please use [AFET](https://github.com/shanzhenren/AFET) (Ren et al., EMNLP'16).

## Data

- NYT:
  - Corpus: 110k New York Times news articles ([download](https://www.dropbox.com/s/y20wv7xmfgcjx65/nyt13_110k.txt?dl=0))
  - Seed entities: entity linking result by DBpediaSpotlight ([download](https://www.dropbox.com/s/k0qzsvbbpngptjt/seed_nyt.txt?dl=0))  
- Yelp:
  - Corpus: 230k Yelp reviews sampled from [Yelp Dataset](https://www.yelp.com/dataset_challenge) ([download](https://www.dropbox.com/s/nqouxgqmz2fdemy/yelp_230k.txt?dl=0))
  - Seed entities: entity linking result by DBpediaSpotlight ([download](https://www.dropbox.com/s/w628rwpb3kbmuea/seed_yelp.txt?dl=0))
- Tweet:
  - Corpus: 302k tweets from May 2011 ([download](https://www.dropbox.com/s/tlf4qi5siqka14n/tweet_302k.txt?dl=0))
  - Seed entities: entity linking result by DBpediaSpotlight ([download](https://www.dropbox.com/s/c1yuqy3fakga015/tweet_seed.txt?dl=0))


## System Output & Evaluation

The system output on NYT dataset can be downloaded from [here](https://www.dropbox.com/s/s1cqym4qmub3jkt/results.txt?dl=0). We evaluated the result over ~1k (20,874 annotated entity mentions) [gold standard set](https://www.dropbox.com/s/n46gr1aented5n1/gt_nyt.txt?dl=0). 

Evaluate the result:
```
python src/evaluation.py -ResultPath -GroundTruthPath
```


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

## Run.sh - File path setup
We take Yelp dataset as an example.

Input: text corpus path.
```
RawText='data/yelp/yelp_230k.txt'
```
- format: "docId \TAB document \n"


Input: type mapping file path.
```
TypeFile='data/yelp/type_tid.txt'
```
- format: "type name \TAB typeId \n". "NIL" means "Not-of-Interest"


Input: mapping between Freebase and DBpedia entities. 
```
FreebaseMap='data/freebase_links.nt'
```
- Download [Freebase-to-DBpedia mapping file](https://drive.google.com/open?id=0Bw2KHcvHhx-gQ2RJVVJLSHJGYlk). Place it under "data/" directory


Output: output file from candidate generation (format: "docId \TAB segmented sentence \n").
```
SegmentOutFile='result/segment.txt'
```
- Segments are separated by ",". Entity mention candidates are marked with ":EP". Relation phrases are marked with ":RP".


Output: entity linking result (please download the corresponding seed entity files).
```
SeedFile='result/yelp/seed_yelp.txt'
```
- Format: "docId \TAB entity name \TAB Original Freebase Type \TAB Refined Type \TAB Freebase EntityID \TAB Similarity Score \TAB Relative Rank \n". 
- NOTE: Our entity linking module calls [DBpediaSpotLight Web service](https://github.com/dbpedia-spotlight/dbpedia-spotlight/wiki/Web-service), which has limited querying speed. This process can be largely accelarated by installing the tool on your local machine [Link](https://github.com/dbpedia-spotlight/dbpedia-spotlight/wiki/Installation).


Output: entity mentions found in each document.
```
ResultFile='result/yelp/results.txt'
```
- Format: "docId \TAB entity mention \TAB entity type \n".


Output: In-text annotation of entity mentions. 
```
ResultFileInText='result/yelp/resultsInText.txt'
```

## Run.sh - Model parameters

Threshold on significance score for candidate generation.
```
significance="2"
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
minSup='30'
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
