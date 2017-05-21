from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
from numpy import *
from scipy import *
from scipy.sparse import *
from sklearn.preprocessing import normalize
from string import punctuation

### seed generation #############################################

def load_type_file(file_name):
    type_tid = defaultdict(int)
    tid_type = defaultdict(str)
    with open(file_name) as f:
        for line in f:
            entry = line.strip().split('\t')
            if len(entry) == 2:
                type_tid[entry[0]] = int(entry[1])
                tid_type[int(entry[1])] = entry[0]
    return (type_tid, tid_type, len(type_tid))


def load_ground_truth(file_name, type_path, confidence_threshold):
    type_tid, tid_type, T = load_type_file(type_path)

    mention = defaultdict(tuple)
    score_set = set()
    with open(file_name) as f:
        for line in f:
            entry = line.strip().split('\t')
            if len(entry) == 7:
                doc_id = entry[0]
                mention_string = entry[1].lower().strip(punctuation) # strip punctuation
                mention_notableType = entry[2].strip(";")
                mention_type = entry[3].strip(";")
                # filter
                percentOfSecondRank = float(entry[6])
                simScore = float(entry[5])
                if percentOfSecondRank == -1:
                    percentOfSecondRank = 0.0
                score_set.add(percentOfSecondRank)
                if simScore > 0.05 and percentOfSecondRank <= (1 - confidence_threshold*confidence_threshold):
                    if mention_type in type_tid: # target type (positive examples)
                        mention[doc_id + '_' + mention_string] = (type_tid[mention_type], simScore)
                    else: # not target type (negative examples, 'NIL' with high confidence)
                        mention[doc_id + '_' + mention_string] = (type_tid['NIL'], simScore)

    return mention



def partition_train_test(mid_mention, TRAIN_RATIO):
    ### partition by docs
    doc_mid = defaultdict(set)
    for mid in mid_mention:
        doc_id = mid_mention[mid].split('_')[0]
        doc_mid[doc_id].add(mid)

    # random partition documents into train/test sets
    doc_id_list = doc_mid.keys()
    # random.shuffle(doc_id_list)
    doc_id_bound = int(len(doc_id_list) * TRAIN_RATIO)
    train_doc = set(doc_id_list[:doc_id_bound])
    test_doc = set(doc_id_list[doc_id_bound:])
    # print '#train doc: ', len(train_doc), '#test doc', len(test_doc)

    trainMid = set()
    testMid = set()
    for mid in mid_mention:
        doc_id = mid_mention[mid].split('_')[0]
        if doc_id in train_doc:
            trainMid.add(mid)
        elif doc_id in test_doc:
            testMid.add(mid)
    # print 'Percent Mentions to be seeded: ', len(trainMid)/(len(trainMid)+len(testMid)+0.0)*100, '%'
    return (trainMid, testMid)




####### Entity Recognition #################################
def get_doc_mid(mid_mention):
    doc_mid = defaultdict(set)
    for mid in mid_mention:
        mention = mid_mention[mid]
        doc_id, name = mention.strip().split('_')
        doc_mid[doc_id].add(mid)
    return doc_mid


def write_output(annotation_path, Y, doc_mid, mid_mention, tid_type):
    f = open(annotation_path, 'w')

    for doc_id in doc_mid:
        for mid in doc_mid[doc_id]:
            y = Y[mid, :]
            if y.sum() == 0:
                predict_tid = len(tid_type) - 1 # NIL
            else:
                predict_tid = y.argmax()

            mention = mid_mention[mid]
            mention_name = mention.split('_')[1]
            
            if predict_tid != len(tid_type) - 1:
                f.write(str(doc_id) + '\t' + mention_name + '\t' + tid_type[predict_tid] + '\n')
    f.close()
    return 0


def write_output_intext(output_path, annotation_path, Y, doc_mid, mid_mention, tid_type):
    doc_text = defaultdict(list)
    with open(output_path) as f:
        for line in f:
            if len(line.strip().split('\t')) == 2:
                doc_id, sentence = line.strip().split('\t')
                doc_text[doc_id].append(sentence.split(','))

    f = open(annotation_path, 'w')
    for doc_id in doc_mid:

        sentence_list = doc_text[doc_id]

        for mid in doc_mid[doc_id]:
            y = Y[mid, :]
            if y.sum() == 0:
                predict_tid = len(tid_type) - 1 # NIL
            else:
                predict_tid = y.argmax()

            mention = mid_mention[mid]
            mention_name = mention.split('_')[1]
            
            for j in range(len(sentence_list)):
                sentence_j_text = ' '.join(sentence_list[j]).lower()
                if mention_name + ':ep' in sentence_j_text:
                    for i in range(len(sentence_list[j])):
                        if mention_name+':ep' == sentence_list[j][i].lower():
                            doc_text[doc_id][j][i] = '[' + sentence_list[j][i][:-3] + ']:' + tid_type[predict_tid].upper()

    for doc_id in doc_text:
        for sentence in doc_text[doc_id]:
            f.write(doc_id + '\t' + ','.join(sentence) + '\n')
    f.close()

    return 0


def reader(file_path):
    data = defaultdict(set)
    with open(file_path) as f:
        for line in f:
            if line:
                did, name, label = line.strip().split('\t')
                data[did].add((name.lower(), label))
    print 'load', len(data), 'docs'
    return data


def writer(file_path, data):
    with open(file_path, 'w') as f:
        for did in data:
            for tuple in data[did]:
                f.write(did + '\t' + tuple[0] + '\t' + tuple[1] + '\n')


def evaluate(gt_dict, pred_dict):
    overlap_size = 0.0
    pred_size = 0.0
    gt_size = 0.0

    for did in gt_dict:
        gt_size += len(gt_dict[did])
        if did in pred_dict:
            pred_size += len(pred_dict[did])
            overlap_size += len(gt_dict[did] & pred_dict[did])

    print 'Precision = ', overlap_size / pred_size
    print 'Recall = ', overlap_size / gt_size
    print 'F1 = ', 2*(overlap_size / pred_size * overlap_size / gt_size) / (overlap_size / pred_size + overlap_size / gt_size)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print 'Usage: evaluation.py -RESULT -GOLD_STANDARD'
        exit(-1)
    ResultPath = sys.argv[1]
    GroundTruthPath = sys.argv[2]

    result = reader(ResultPath)
    ground_truth = reader(GroundTruthPath)
    evaluate(ground_truth, result)
