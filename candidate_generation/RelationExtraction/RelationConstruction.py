__author__ = 'ahmed'
class RelationConstruction:
    def __init__(self, RelationPattern):
        self.RelationPattern = RelationPattern

    def extract_relations(self, sentence, sentence_pos):
        new_sentence = []
        new_sentence_pos = []
        i = 0

        while i < len(sentence):
            phrase = sentence[i]
            phrase_pos = sentence_pos[i]
            if i+1 == len(sentence):
                new_sentence.append(phrase)
                new_sentence_pos.append(phrase_pos)
                i+=1

            else:
                new_phrase = [k for k in phrase]
                new_phrase_pos = [k for k in phrase_pos]
                j = i+1
                while j < len(sentence):
                    next_phrase = sentence[j]
                    next_phrase_pos = sentence_pos[j]
                    valid = self.RelationPattern.isMatch(phrase_pos[0], next_phrase_pos[0], next_phrase)
                    if valid:
                        new_phrase.extend(next_phrase)
                        new_phrase_pos.extend(next_phrase_pos)
                        j+=1
                        if j==len(sentence):
                            i = len(sentence)
                    else:
                        i=j
                        new_sentence.append(new_phrase)
                        new_sentence_pos.append(new_phrase_pos)
                        break

        return new_sentence, new_sentence_pos








    def _reconstruct_relations(self, sentence):
        pass
