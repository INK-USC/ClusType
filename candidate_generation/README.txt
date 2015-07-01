Place your input file in the input folder.

You then have three scripts to run.

1.) preprocess.sh
    Put your input data name here and run this script. This places the data in the right formatting for FPM.

2.) minePhrases.sh
    This is the frequent contiguous pattern mining step. The parameters here are the minsup and the max_pattern_length. Both are self explanatory.

3.) extractEntities.sh
    This step allows for extracting entities. You should pick a significance threshold to run with. 