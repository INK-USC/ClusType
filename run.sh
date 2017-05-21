#!/bin/sh
Data='yelp'
RawText='data/'$Data'/yelp_230k.txt'
TypeFile='data/'$Data'/type_tid.txt'
SeedFile='data/'$Data'/seed_yelp.txt'
ResultPath='result/'$Data
SegmentOutFile=$ResultPath'/segment.txt'
DataStatsFile=$ResultPath'/data_model_stats.txt' # data statistics on graph construction
ResultFile=$ResultPath'/results.txt' # typed entity mentions
ResultFileInText=$ResultPath'/resultsInText.txt' # typed mentions annotated in segmented text
significance="2"
capitalize="1"
maxLength='4' # maximal phrase length
minSup='20' # minimal support for phrases in candidate generationSegmentOutFile='result/yelp/segment.txt'
NumRelationPhraseClusters='500' # number of relation phrase clusters



### Candidate Generation
# mkdir $ResultPath
# sentences_path="Intermediate/sentences.txt"
# full_sentence_path="Intermediate/full_sentences.txt"
# pos_path="Intermediate/pos.txt"
# full_pos_path="Intermediate/full_pos.txt"
# frequent_patterns_path="Intermediate/frequentPatterns.pickle"
# segmentInput='Intermediate/phrase_segments.txt'
# cd candidate_generation
# rm -rf Intermediate
# mkdir Intermediate
# python DataPreprocessing/Clean.py $RawText 
# python FrequentPhraseMining/FrequentPatternMining.py $segmentInput $maxLength $minSup 
# python EntityExtraction/EntityRelation.py $sentences_path $full_sentence_path $pos_path $full_pos_path $frequent_patterns_path $significance $SegmentOutFile $capitalize
# cd ..


### Entity Linking (uncomment to run the entity linking via DBpediaSpotlight)
# FreebaseMap='data/freebase_links.nt'
# FreebaseKey='AIzaSyBvkZaBXc1GzVs3d0QN2HjTjDZwlgxboW4' # set your own freebase key
# cd entity_linking
# mkdir tmp
# python EntityLinking.py $RawText $TypeFile $FreebaseMap $SeedFile $FreebaseKey
# rm -rf tmp
# cd ..


### Typing
# python src/step0-graph_construction.py $SegmentOutFile $DataStatsFile
python src/step1-entity_recognition.py $SegmentOutFile $SeedFile $TypeFile $NumRelationPhraseClusters $ResultFile $ResultFileInText

