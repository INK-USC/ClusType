__author__ = 'xiang'
import sys
from textblob import TextBlob
from textblob.taggers import PatternTagger
from Partition import Partition
from StopWords import StopWords

class Clean:
    def __init__(self, path):
        self.Documents = []
        self.allowed = set([chr(i) for i in xrange(ord('a'), ord('z')+1)]+ \
                [chr(i) for i in xrange(ord('A'), ord('Z')+1)] + \
            #[',','-',' '] + [str(i) for i in xrange(10)])
                [',','.','?','-','!',' '] + [str(i) for i in xrange(10)])
        self.punctuation = [';',':','&', '?', "/"]
        self.P = Partition(self.punctuation)
        self.tagger = PatternTagger()
        self.sw = StopWords()
        with open(path,'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.Documents.append(line)
    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    def remove_stopwords(self, words, pos):
        new_sent = []
        new_pos = []
        for i in xrange(len(words)):
            if not self.sw.isStopWord(words[i]):
                new_sent.append(words[i])
                new_pos.append(pos[i])
        return new_sent,new_pos

    def replace_nums(self,s):
        sent = str(s)
        if sent[len(sent)-1] == ".":
            sent = sent[0:len(sent)-1]
        sent = sent.split()
        new_sent = []
        for word in sent:
            if self.is_number(word):
                pass
                #new_sent.append("999999")
            else:
                new_sent.append(word)
        sent = " ".join(new_sent)

        return sent
    def remove_things(self, string):
        string = string.replace("\t", " ")
        string = string.replace(" and ", ", and ")
        new_string = [char for char in string if char in self.allowed]
        return "".join(new_string)

    def clean_and_tag(self):
        with open('Intermediate/full_sentences.txt', 'w') as f,\
                open('Intermediate/full_pos.txt','w') as g,\
                open('Intermediate/sentences.txt', 'w') as m,\
                open('Intermediate/pos.txt', 'w') as n:
            for i in xrange(len(self.Documents)):
                if i%10000 == 0 and i!=0:
                    print str(i)+" documents processed."
                doc = self.Documents[i]
                cleaned_doc = self.remove_things(doc)
                blob = TextBlob(cleaned_doc)
                for j in xrange(len(blob.sentences)):
                    sent = blob.sentences[j]
                    sent = self.replace_nums(sent)
                    split_sentence = self.P.split(sent)

                    for k in xrange(len(split_sentence)):
                        frag = split_sentence[k]
                        sent_blob = TextBlob(frag, pos_tagger=self.tagger)
                        words, pos = [],[]
                        for word,tag in sent_blob.pos_tags:
                            words.append(word)
                            pos.append(tag)
                        f.write(str(i)+":"+str(j)+":"+str(k)+":"+(" ".join(words)+"\n"))
                        g.write(" ".join(pos)+"\n")
                        no_stop_words, no_stop_pos = self.remove_stopwords(words,pos)
                        m.write(str(i)+":"+str(j)+":"+str(k)+":"+(" ".join(no_stop_words)+"\n"))
                        n.write(" ".join(no_stop_pos)+"\n")
if __name__ == "__main__":
    path = sys.argv[1]
    C = Clean(path)
    print "Start candidate generation..."
    C.clean_and_tag()



