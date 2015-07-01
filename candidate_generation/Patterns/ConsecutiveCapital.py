__author__ = 'ahmed'
class ConsecutiveCapital:
    def __init__(self):
        self.type = "CC"
    def match(self, node1, node2):

        if (node1.pos.startswith("NN") or node1.pos.startswith("JJ")) \
                and node2.pos.startswith("NN") \
                and node1.actual[0][0].isupper() \
                and node2.actual[0][0].isupper():

            return True
        return False
    def compare(self, sig, thresh):
        return True