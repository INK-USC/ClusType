__author__ = 'ahmed'
class ConsecutiveNouns:
    def __init__(self):
        self.type = "CN"
    def match(self, node1, node2):
        if (node1.pos.startswith("NN") or node1.pos.startswith("JJ")) \
                and node2.pos.startswith("NN"):#\
                #and not node1.actual[0][0].isupper() \
                #and not node2.actual[0][0].isupper():
            return True
        return False
    def compare(self, sig, thresh):
        if sig < thresh:
            return True
        return False