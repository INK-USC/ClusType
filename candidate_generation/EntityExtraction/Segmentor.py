__author__ = 'ahmed'
from HeapDictionary2 import heapdict
from Word import Word
from ScoringFunctions import ScoringFunctions
class Segmentor:
    def __init__(self, threshold, frequent_patterns, corpus_length):
        self.threshold = -float(threshold)
        self.frequent_patterns = frequent_patterns
        self.SF = ScoringFunctions(frequent_patterns, corpus_length)
    def tokenize(self, sent, pos_tags):
        head = Word()
        head.word = [sent[0].lower()]
        head.actual = [sent[0]]
        head.pos = pos_tags[0]
        curr = head
        length = len(sent)
        for i in xrange(1, len(sent)):
            new_word = Word()
            new_word.left = curr
            curr.right = new_word
            new_word.word = [sent[i].lower()]
            new_word.actual = [sent[i]]
            new_word.pos = pos_tags[i]
            curr = new_word
        return head, length


    def _merge(self, node1, node2):
        node1.right = node2.right
        if node2.right is not None:
            node2.right.left = node1
        node1.word = node1.word + node2.word
        node1.actual = node1.actual + node2.actual
        return node1

    def _initialize_heap(self, sent, pos):
        h = heapdict()
        head, length = self.tokenize(sent, pos)
        curr = head
        for i in xrange(length-1):
            h[curr] = sig = self.SF.significance(curr, curr.right)
            h[curr] = sig
            curr = curr.right
        return head, h
    def segment(self, sentence, pos):
        head, h = self._initialize_heap(sentence, pos)

        while len(h) > 1:
            node, sig = h.popitem()
            next_node = node.right
            if sig > self.threshold:
                break
            new_node = self._merge(node, next_node)
            if new_node.left is not None:
                left_node = new_node.left
                left_sig = self.SF.significance(left_node,new_node)
                h[left_node] = left_sig
            if next_node is not None:
                if next_node in h: del h[next_node]
                two_nodes_down = next_node.right
                if two_nodes_down is not None:
                    new_sig = self.SF.significance(new_node, next_node)
                    h[new_node] = new_sig
        segmented = []
        temp = head
        while temp is not None:
            segmented.append(" ".join(temp.actual))
            temp = temp.right
        return segmented
        return head
    def pattern_segment(self, patterns, sent, pos):
        head, length = self.tokenize(sent, pos)
        curr_node = head
        for pattern in patterns:
            curr_node = head
            while length > 1:
                if curr_node is None or curr_node.right is None:
                    break
                next_node = curr_node.right

                #if sig > self.threshold:
                #    break
                if pattern.match(curr_node, next_node):
                    sig = self.SF.significance(curr_node, next_node)

                    if pattern.compare(sig, self.threshold):
                        new_node = self._merge(curr_node,next_node)


                        length -=1
                    else:
                        curr_node = curr_node.right
                else:
                    curr_node = curr_node.right


        segmented = []
        temp = head
        while temp is not None:
            segmented.append(" ".join(temp.actual))
            temp = temp.right
        return segmented
        return head







