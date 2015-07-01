__author__ = 'ahmed'
class StopWords:
    def __init__(self):
        path = 'stopwords/en.txt'
        f = open(path, 'r')
        self.stop_words = set([line.strip() for line in f])
    def isStopWord(self, word):
        if word in self.stop_words:
            return True
        return False