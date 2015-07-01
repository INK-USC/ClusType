__author__ = 'ahmed'
class PPV:
    def __init__(self):
        self.words = set([word.strip() for word in open('PPV/ppv.txt', 'r')])
        self.replacement = "ppv"
    def collapse(self, sentence):
        new_sentence = []
        for phrase in sentence:
            new_phrase = []
            for word in phrase:
                if word in self.words:
                    new_phrase.append(self.replacement)
                else:
                    new_phrase.append(word)
            new_sentence.append(new_phrase)
        return new_sentence