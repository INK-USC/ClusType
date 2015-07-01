__author__ = 'xiang'
import sys
import pickle

from Segmentor import Segmentor
from PostProcess import PostProcess
from Patterns import *


class EntityRelation:
    def __init__(self,sentence_path, full_sentence_path, pos_path,full_pos_path, frequent_patterns_path,significance,out_path,capitalize=False):
        self.Docs = []
        self.FullDocs = []
        self.POS = []
        self.FullPOS = []
        self.PP = PostProcess()
        self.CC = ConsecutiveCapital()
        self.CN = ConsecutiveNouns()
        self.VB = VerbPhrase()
        self.significance = significance
        self.capitalize=capitalize
        self.TotalWords = 0
        self.frequent_patterns = pickle.load(open(frequent_patterns_path,'r'))
        self.out_path = out_path
        index = -1
        with open(sentence_path, 'r') as f,\
                open(pos_path, 'r') as g,\
                open(full_sentence_path, 'r') as h,\
                open(full_pos_path, 'r') as k:
            while True:
                sent1 = f.readline()
                sent1_full = h.readline()
                sent1_pos = g.readline().strip()
                sent1_full_pos = k.readline().strip()
                if not sent1:
                    break
                doc_index, sent_index, seg_index, sent1 = sent1.split(":")
                full_doc_index, full_doc_sent_index, full_doc_seg_index, sent1_full = sent1_full.split(":")
                doc_index = int(doc_index)
                sent_index = int(sent_index)
                seg_index = int(seg_index)
                while doc_index > index:
                    index += 1
                    self.FullDocs.append([])
                    self.Docs.append([])
                    self.POS.append([])
                    self.FullPOS.append([])
                split_sentence = sent1.strip().split()
                split_full_sentence = sent1_full.strip().split()
                split_pos_tags = sent1_pos.split()
                split_full_pos_tags = sent1_full_pos.split()
                self.TotalWords += len(split_sentence)
                if len(self.Docs[doc_index]) == sent_index:
                    self.FullDocs[doc_index].append([])
                    self.Docs[doc_index].append([])
                    self.POS[doc_index].append([])
                    self.FullPOS[doc_index].append([])
                self.Docs[doc_index][sent_index].append(split_sentence)
                self.FullDocs[doc_index][sent_index].append(split_full_sentence)
                self.POS[doc_index][sent_index].append(split_pos_tags)
                self.FullPOS[doc_index][sent_index].append(split_full_pos_tags)
        # load segmentor
        self.S = Segmentor(significance, self.frequent_patterns, self.TotalWords)
    def extract(self):
        out_path = self.out_path
        with open(out_path, 'w') as f:
            for i in xrange(len(self.Docs)):
                if i%10000 ==0 and i!=0 : print str(i)+" documents processed"

                doc = self.Docs[i]
                full_doc = self.FullDocs[i]
                pos_for_doc = self.POS[i]
                full_pos_for_doc = self.FullPOS[i]
                for j in xrange(len(doc)):
                    sentence = doc[j]
                    full_sentence = full_doc[j]
                    sentence_pos = pos_for_doc[j]
                    full_sentence_pos = full_pos_for_doc[j]
                    final_sentence = []
                    for k in xrange(len(sentence)):
                        seg = sentence[k]

                        full_seg = full_sentence[k]
                        pos = sentence_pos[k]
                        full_seg_pos = full_sentence_pos[k]
                        combined = [seg[m]+":"+pos[m] for m in xrange(len(pos))]
                        final_result = []
                        if seg:
                            #result = self.S.segment(sentence, pos)

                            #result = self.S.pattern_segment([self.CC, self.CN], seg, pos)
                            used_patterns = [self.CN]
                            if self.capitalize:
                                used_patterns.append(self.CC)
                            result = self.S.pattern_segment(used_patterns, seg, pos)

                            final_result = self.PP.reconstruct(result,full_seg, pos, full_seg_pos)
                        else:
                            final_result = full_seg

                        final_result = ",".join(final_result)
                        final_sentence.append(final_result)
                    f.write(str(i) + "\t" + ",".join(final_sentence)+"\n")
                        # f.write(",".join(result)+"\n")


if __name__ == "__main__":
    sentences_path = sys.argv[1]
    full_sentence_path = sys.argv[2]
    pos_path = sys.argv[3]
    full_pos_path = sys.argv[4]
    frequent_patterns_path = sys.argv[5]
    significance = sys.argv[6]
    out_path = sys.argv[7]
    capitalize = int(sys.argv[8])
    ER = EntityRelation(sentences_path,full_sentence_path,pos_path,full_pos_path,frequent_patterns_path,significance,out_path,capitalize)
    ER.extract()
    print 'Candidate generation done.'
