__author__ = 'ahmed'
from RelationExtraction import RelationConstruction
from Patterns import VerbPhrase
from PPV import PPV
class PostProcess:
    def __init__(self):
        self.RC = RelationConstruction(VerbPhrase())
        self.PPV = PPV()
    def _split_on_verb(self, sentence, pos_tags):
        new_sentence = []
        new_pos = []
        for i in xrange(len(sentence)):
            phrase = sentence[i]
            phrase_pos = pos_tags[i]
            if (phrase_pos[0].startswith("NN") or \
                        phrase_pos[0].startswith("JJ")) and \
                        any(x.startswith("VB") for x in phrase_pos):
                first_part = []
                first_part_pos = []
                verb = []
                verb_pos = []
                final = []
                final_pos = []
                flag = False
                for j in xrange(len(phrase_pos)):
                    if phrase_pos[j].startswith("VB"):
                        verb.append(phrase[j])
                        verb_pos.append(phrase_pos[j])
                        flag = True
                    elif not flag:
                        first_part.append(phrase[j])
                        first_part_pos.append(phrase_pos[j])

                    else:
                        if not phrase_pos[j].startswith("NN"):
                            verb.append(phrase[j])
                            verb_pos.append(phrase_pos[j])
                        else:
                            final.append(phrase[j])
                            final_pos.append(phrase_pos[j])
                new_sentence.append(first_part)
                for word in verb:
                    new_sentence.append([word])
                new_sentence.append(final)
                new_pos.append(first_part_pos)
                for pos in verb_pos:
                    new_pos.append([pos])
                new_pos.append(final_pos)
            else:
                new_sentence.append(phrase)
                new_pos.append(phrase_pos)
        return new_sentence, new_pos
    def original(self, sentence, pos_tags):
        condensed_pos = []
        for i in xrange(len(sentence)):
            phrase = sentence[i]
            phrase_pos = pos_tags[i]
            if (phrase_pos[0].startswith("NN") or phrase_pos[0].startswith("JJ")) and any(x.startswith("VB") for x in phrase_pos):
                first_part = []
                verb = []
                final = []
                flag = False
                for j in xrange(len(phrase_pos)):
                    if phrase_pos[j].startswith("VB"):
                        verb.append(phrase[j])
                        flag = True
                    elif not flag:
                        first_part.append(phrase[j])
                    else:
                        final.append(phrase[j])
                condensed_pos.append(" ".join(first_part)+":EP")
                if not len(first_part) == 1 or first_part[0][0].isupper():
                    condensed_pos.append(" ".join(first_part)+":EP")
                condensed_pos.append(" ".join(verb)+":RP")
                if not len(final) == 1 or first_part[0][0].isupper():
                    condensed_pos.append(" ".join(final)+":EP")
            elif phrase_pos[0].startswith("NN") and sum(1 if not (x.startswith("NN") or x.startswith("JJ"))else 0 for x in phrase_pos) > 3:
                for j in xrange(len(phrase_pos)):
                    if phrase_pos[j].startswith("NN") and phrase[j][0].isupper():
                        condensed_pos.append(phrase[j]+":EP")
                    elif phrase_pos[j].startswith("VB") or phrase_pos[j].startswith("IN"):
                        condensed_pos.append(phrase[j]+":RP")

            elif pos_tags[i][0].startswith("NN") or pos_tags[i][0].startswith("JJ"):
                if len(sentence[i]) > 1 or sentence[i][0][0].isupper():
                    condensed_pos.append(" ".join(sentence[i])+":EP")
                ### single word noun???
                else:
                    condensed_pos.append(" ".join(sentence[i]))

            elif pos_tags[i][0].startswith("VB") or pos_tags[i][0].startswith("IN"):
                condensed_pos.append(" ".join(sentence[i])+":RP")

            ### OTHER tags
            else:
                condensed_pos.append(" ".join(sentence[i]))

                #sentence[i][j] = sentence[i][j]+":"+pos_tags[i][j]
        #for i in xrange(len(sentence)):
        #    sentence[i] = " ".join(sentence[i])+":"+condensed_pos[i]
        return condensed_pos
    def reconstruct(self, partial, full, partial_pos, full_pos):
        sentence = []
        pos_tags = []
        if len(partial) == 0: return full
        partial = map(lambda x: x.split(), partial)
        index = 0
        word_index = 0
        new_phrase = []
        new_phrase_pos = []
        #print full
        #print partial
        #print "#####"
        i = 0
        while i <  len(full):
            word = full[i]
            pos = full_pos[i]
            if index >= len(partial):
                sentence.append([word])
                pos_tags.append([pos])
            else:
                curr_phrase = partial[index]
                #print word,curr_phrase
                if word_index >= len(curr_phrase):
                    index += 1
                    word_index = 0
                    sentence.append(new_phrase)
                    pos_tags.append(new_phrase_pos)
                    new_phrase = []
                    new_phrase_pos = []
                    continue

                if word != curr_phrase[word_index] and word_index == 0:
                    new_phrase.append(word)
                    new_phrase_pos.append(pos)
                    sentence.append(new_phrase)
                    pos_tags.append(new_phrase_pos)
                    new_phrase = []
                    new_phrase_pos = []
                elif word != curr_phrase[word_index]:
                    new_phrase.append(word)
                    new_phrase_pos.append(pos)
                elif word == curr_phrase[word_index]:
                    new_phrase.append(word)
                    new_phrase_pos.append(pos)
                    word_index+=1
            i += 1
        if len(new_phrase):
            sentence.append(new_phrase)
            pos_tags.append(new_phrase_pos)
        new_sentence, new_pos = self._split_on_verb(sentence,pos_tags)
        new_sentence, new_pos = self.RC.extract_relations(new_sentence,new_pos)
        new_sentence = self.PPV.collapse(new_sentence)
        return self.original(new_sentence, new_pos)
        return self.original(sentence,pos_tags)

