__author__ = 'ahmed'
from Word import Word
class ScoringFunctions:
    def __init__(self, frequent_patterns, corpus_length):
        self.frequent_patterns = frequent_patterns
        self.corpus_length = corpus_length
        self.max_length = len(self.frequent_patterns)
    def _score(self, left, right):
        if len(left) > self.max_length or len(right) > self.max_length:
            return -float('inf')
        left_count = self.frequent_patterns[len(left)-1][tuple(left)]
        right_count = self.frequent_patterns[len(right)-1][tuple(right)]
        combined = left+right
        combined_length = len(combined)
        if combined_length > self.max_length:
            return -float('inf')
        combined_count = self.frequent_patterns[combined_length-1][tuple(left+right)]
        numerator = float(combined_count)\
                    - self.corpus_length*(float(left_count)/self.corpus_length)\
                      *(float(right_count)/self.corpus_length)
        denominator = float(combined_count)**0.5

        if combined_count == 0:
            return -float('inf')
        else:
            return numerator/denominator

    def significance(self, head1, head2):
        left_phrase = head1.word
        right_phrase = head2.word
        score = -self._score(left_phrase, right_phrase)
        return score


