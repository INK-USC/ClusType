__author__ = 'ahmed'
class VerbPhrase:
    def __init__(self):
        pass
    def match(self, node1, node2):
        if node1.pos.startswith("VB") \
                and (node2.pos.startswith("VB") \
                or node2.pos.startswith("RB") \
                or node2.pos.startswith("IN")\
                or node2.pos.startswith("JJ")\
                or node2.pos.startswith("PRP")):
            return True
        return False
    def isMatch(self, pos1, pos2, phrase2):
        if pos1.startswith("VB") and not phrase2[0][0].isupper() \
                and (pos2.startswith("VB") \
                or pos2.startswith("RB") \
                or pos2.startswith("IN")\
                or pos2.startswith("JJ")\
                or pos2.startswith("PRP")\
                or (pos2.startswith("NN") and len(phrase2)==1 )):
            return True
    def compare(self, sig, thresh):
        if sig < thresh:
            return True
        return False