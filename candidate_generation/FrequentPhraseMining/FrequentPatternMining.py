__author__ = 'xiang'
from collections import Counter
from BitVector import BitVector
import pickle
import sys

class FrequentPatternMining:
    def __init__(self, Docs, max_pattern, minsup):
        self.Patterns = [None] *len(Docs)
        for i in xrange(len(Docs)):
            self.Patterns[i] = Docs[i].strip().split()
        self.minsup = minsup
        self.max_pattern = max_pattern
        self.frequent_patterns = [Counter() for i in xrange(max_pattern)]
        self.DocApriori = [None] * len(self.Patterns)
        for i in xrange(len(self.Patterns)):
            self.DocApriori[i] = BitVector(size=len(self.Patterns[i]))
            #self.DocApriori[i].setall(1)

    def mine(self,document, pattern_size, insufficient_patterns, doc_apriori):
        doc_size = len(document)
        continue_mining = False
        for i in xrange(doc_size+1 -pattern_size):
            if doc_apriori[i]==0:
                #HACK for checking for end of array
                if i==doc_size - 1 or doc_apriori[i+1]==0:
                    cand = tuple([document[i+j] for j in xrange(pattern_size)])
                    continue_mining = True
                    if not cand in self.frequent_patterns[pattern_size-1]:
                        curr_count = insufficient_patterns[cand] + 1
                        if curr_count >= self.minsup:
                            self.frequent_patterns[pattern_size-1][cand] = curr_count
                            del insufficient_patterns[cand]
                        else:
                            insufficient_patterns[cand] = curr_count
                    else:
                        self.frequent_patterns[pattern_size-1][cand] += 1
                else:
                    doc_apriori[i] = 1
        return continue_mining


    def mine_fixed_pattern(self, last_document, pattern_size):
        index = 0
        insufficient_patterns = Counter()
        while index <= last_document:
            doc = self.Patterns[index]
            doc_apriori = self.DocApriori[index]
            continue_mining = self.mine(doc, pattern_size, insufficient_patterns, doc_apriori)
            # check length of document
            if not continue_mining or len(doc) <= pattern_size:
                self.Patterns[index], self.Patterns[last_document] = self.Patterns[last_document], self.Patterns[index]
                self.DocApriori[index],self.DocApriori[last_document] = self.DocApriori[last_document],self.DocApriori[index]
                last_document -= 1
            else:
                index += 1
        del insufficient_patterns
        pattern_size += 1
        print "Ending Mining of Patterns of Size: "+str(pattern_size-1)
        print "Documents Remaining: "+str(last_document)
        return last_document

    def mine_patterns(self):
        pattern_size = 1
        last_document = len(self.Patterns)-1
        print "Mining Contiguous Patterns"
        while last_document >= 0:
            last_document = self.mine_fixed_pattern(last_document, pattern_size)
            pattern_size += 1
            if pattern_size > self.max_pattern:
                break
        return self.frequent_patterns
if __name__ == "__main__":
    path = sys.argv[1]
    max_pattern = int(sys.argv[2])
    minsup = int(sys.argv[3])
    documents = []
    with open("Intermediate/phrase_segments.txt",'r') as f:
        for line in f:
            documents.append(line.strip())
    FPM = FrequentPatternMining(documents, max_pattern, minsup)
    FrequentPatterns = FPM.mine_patterns()
    pickle.dump(FrequentPatterns, open("Intermediate/frequentPatterns.pickle", "w"))



