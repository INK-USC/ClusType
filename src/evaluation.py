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


#### Mention Classification ############################################################

def test(Y, test_mid, mention_ground_truth, mid_mention):
    tid_pos = defaultdict(float)
    tid_neg = defaultdict(float)
    tid_groundtruth = defaultdict(float)
    tid_predict = defaultdict(float)
    pos = 0.0
    neg = 0.0
    for mid in test_mid:
        mention = mid_mention[mid]
        if mention in mention_ground_truth:
            
            true_tid = mention_ground_truth[mention][0]
            tid_groundtruth[true_tid] += 1.0
            
            y = Y[mid, :]
            if y.sum() == 0:
                predict_tid = Y.shape[1] - 1
            else:
                # predict_tid = y.indices[y.data.argmax()] if y.nnz else 0 #??? DOUBLE CHECK!!!
                predict_tid = y.argmax()

            if predict_tid == true_tid:
                # positive
                tid_pos[predict_tid] += 1.0
                pos += 1.0
            else:
                tid_neg[predict_tid] += 1.0
                neg += 1.0

    print 'Percentage GroundTruth/TestSize', (pos+neg)/len(test_mid) * 100
    return (pos, neg, tid_pos, tid_neg, tid_groundtruth)


def test_method(result_path, Y, test_mid, mention_ground_truth, mid_mention, tid_type):
    fff = open(result_path, 'w')
    pos, neg, tid_pos, tid_neg, tid_groundtruth = test(Y, test_mid, mention_ground_truth, mid_mention)
    overall_accuracy = pos/(pos+neg) * 100
    print '#test instances=', pos+neg, ', Overall Accuracy: ', overall_accuracy
    print ''
    fff.write('#test instances=' + str(pos+neg) + ', Overall Accuracy: ' + str(overall_accuracy) + '\n\n')

    tid_prec = defaultdict(float)
    tid_recall = defaultdict(float)
    tid_F1 = defaultdict(float)
    for tid in tid_type:
        if tid_pos[tid] + tid_neg[tid] > 0:
            tid_prec[tid] = tid_pos[tid] / (tid_pos[tid] + tid_neg[tid])
        else:
            tid_prec[tid] = 0.0

        if tid_groundtruth[tid] > 0:
            tid_recall[tid] = tid_pos[tid] / tid_groundtruth[tid]
        else:
            tid_recall[tid] = 0.0
            print tid_type[tid], ' has NO ground truth in test!'

        if tid_prec[tid] > 0 and tid_recall[tid] > 0:
            tid_F1[tid] = 2*tid_prec[tid]*tid_recall[tid]/(tid_prec[tid]+tid_recall[tid])
        else:
            tid_F1[tid] = 0.0

        # print tid_type[tid], ', prec: ', tid_prec[tid], ', recall: ', tid_recall[tid], ', F1: ', str(tid_F1[tid]), ', total# true mentions: ', tid_groundtruth[tid]
        fff.write(str(tid_type[tid]) + ', prec: ' + str(tid_prec[tid]) + ', recall: ' + str(tid_recall[tid]) + \
            ', F1: ' + str(tid_F1[tid]) + ', total# true mentions: ' + str(tid_groundtruth[tid]) + '\n\n')
    fff.close()
    return 0




####### Entity Recognition #################################
def get_doc_mid(mid_mention):
    doc_mid = defaultdict(set)
    for mid in mid_mention:
        mention = mid_mention[mid]
        doc_id, name = mention.strip().split('_')
        doc_mid[doc_id].add(mid)
    return doc_mid


def check_detected_mention(hit_path, miss_path, extra_path, doc_mid, mid_mention, doc_trueMention):
    f1 = open(hit_path, 'w')
    f2 = open(miss_path, 'w')
    f3 = open(extra_path, 'w')
    overlap_count = 0.0
    true_count = 0.0
    predict_count = 0.0

    for doc_id in doc_trueMention:
        trueMention_set = set(doc_trueMention[doc_id].keys())
        true_count += len(trueMention_set)
        detectMention_set = set()
        for mid in doc_mid[doc_id]:
            detectMention_set.add(mid_mention[mid])
        overlap = trueMention_set & detectMention_set
        overlap_count += len(overlap)
        predict_count += len(set(doc_mid[doc_id]))

        if overlap:
            f1.write(str(doc_id) + '\t')
            for mention in overlap:
                 f1.write(mention + '\t')
            f1.write('\n')         
        miss = trueMention_set - detectMention_set
        if miss:
            f2.write(str(doc_id) + '\t')
            for mention in miss:
                 f2.write(mention + '\t')
            f2.write('\n') 
        extra = detectMention_set - trueMention_set
        if extra:
            f3.write(str(doc_id) + '\t')
            for mention in extra:
                 f3.write(mention + '\t')
            f3.write('\n')     


    recall = overlap_count / true_count
    prec = overlap_count / predict_count
    print 'Detected mention Recall =', recall, ', Prec = ', prec
    return recall


def load_annotation(file_name, test_doc, type_path):
    type_tid, tid_type, T = load_type_file(type_path)
    print '# target types: ', T-1

    doc_trueMention_tid = defaultdict(lambda: defaultdict(int))
    type_set = set()
    count = 0
    with open(file_name) as f:
        for line in f:
            entry = line.strip().split('\t')
            if len(entry) == 3:
                doc_id = entry[0]
                if doc_id in test_doc or int(doc_id) in test_doc:
                    mention_name = entry[1].lower().strip(punctuation) ### get the mention name
                    if mention_name.startswith('the '):
                        mention_name = mention_name[len('the '):]
                    elif mention_name.startswith('a '):
                        mention_name = mention_name[len('a '):]
                    elif mention_name.startswith('an '):
                        mention_name = mention_name[len('an '):]
                    type = entry[2].strip()
                    type_set.add(type)
                    mention = doc_id + '_' + mention_name
                    doc_trueMention_tid[doc_id][mention] = type_tid[type]
                    count += 1.0
        print '#Docs annotated', len(doc_trueMention_tid), ', #Mentions annotated: ', count, ', #Types annotated:', len(type_set)

    return doc_trueMention_tid


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

def eval_recognition(Y, doc_trueMention_tid, doc_mid, mid_mention, target_tid_set):
    ### suppose R is our predicted mentions (without NIL); A is true Mentions
    ### precision: #correct in A&R / |A&R| or |R|
    ### recall: #correct in A&R / |A|
    doc_predictMention_tid = defaultdict(lambda: defaultdict(int))
    tid_corr = defaultdict(float)
    tid_Rsize = defaultdict(float) # |A&R| or |R| of a type
    tid_Asize = defaultdict(float) # |A| of a type
    tid_prec = defaultdict(float)
    tid_recall = defaultdict(float)
    tid_f1 = defaultdict(float)

    for doc_id in doc_trueMention_tid:
        # evaluate in annotated docs
        for mention in doc_trueMention_tid[doc_id]:
            true_tid = doc_trueMention_tid[doc_id][mention]
            if true_tid in target_tid_set:
                tid_Asize[true_tid] += 1.0

        for mid in doc_mid[doc_id]:
            y = Y[mid, :]
            predict_tid = y.argmax()

            mention = mid_mention[mid]
            mention_name = mention.split('_')[1]
            
            doc_predictMention_tid[doc_id][mention_name] = predict_tid

            if int(predict_tid) in target_tid_set: 
                ### not NIL
                # tid_Rsize[predict_tid] += 1.0 # |R|

                if mention in doc_trueMention_tid[doc_id]:
                # or mention.strip(punctuation) in doc_trueMention_tid[doc_id] or mention[:-len('s')] in doc_trueMention_tid[doc_id]:
                    
                    tid_Rsize[predict_tid] += 1.0 # |A&R| -- this boost precision

                    if predict_tid == doc_trueMention_tid[doc_id][mention]:
                        tid_corr[predict_tid] += 1.0

    ### calculate metrics
    corr = 0.0
    Asize = 0.0
    Rsize = 0.0
    for tid in tid_Asize:
        Asize += tid_Asize[tid]
        Rsize += tid_Rsize[tid]
        if tid in tid_corr:
            corr += tid_corr[tid]
            tid_recall[tid] = tid_corr[tid] / tid_Asize[tid]
            tid_prec[tid] = tid_corr[tid] / tid_Rsize[tid]
            tid_f1[tid] = 2*(tid_prec[tid]*tid_recall[tid])/(tid_prec[tid]+tid_recall[tid])
        else:
            tid_recall[tid] = 0.0
            tid_prec[tid] = 0.0
            tid_f1[tid] = 0.0

    prec = 0.0
    recall = 0.0
    f1 = 0.0
    if corr > 0:
        prec = corr/Rsize
        recall = corr/Asize
        f1 = 2*(prec*recall)/(prec+recall)

    return (doc_predictMention_tid, prec, recall, f1, tid_prec, tid_recall, tid_f1)

def fuzzy_match(mention, trueMention_tid):
    if mention.startswith('the '):
        mention = mention[len('the '):]
    elif mention.startswith('a '):
        mention = mention[len('a '):]
    elif mention.startswith('an '):
        mention = mention[len('an '):]

    match_list = []
    mentionTokens = set(mention.split())
    # if mention.endswith('s'):
    #     mentionTokens = mentionTokens | set(mention[:-1])

    for trueMention in trueMention_tid:
        trueMentionName = trueMention.split('_')[1]
        trueMentionTokens = set(trueMentionName.split())
        if len(mentionTokens & trueMentionTokens) >= max(len(mentionTokens), len(trueMentionTokens)) - 2:
            match_list.append(trueMention)
    return match_list

def fuzzy_match_type(predict_tid, match_trueMentionList, trueMention_tid):
    ### boost corr: both precision and recall
    match = False
    match_trueMention = set()
    for trueMention in match_trueMentionList:
        if predict_tid == trueMention_tid[trueMention]:
            match = True
            match_trueMention.add(trueMention)
    return (match, match_trueMention)

def check_detected_mention_fuzzy(hit_path, miss_path, extra_path, doc_mid, mid_mention, doc_trueMention_tid):
    # f1 = open(hit_path, 'w')
    # f2 = open(miss_path, 'w')

    predict_count = 0.0
    overlap_count = 0.0
    overlap_prec_count = 0.0
    true_count = 0.0

    for doc_id in doc_trueMention_tid:
        overlap = set()
        miss = set()
        overlap_prec = set()
        for mid in doc_mid[doc_id]:
            mention = mid_mention[mid]
            mention = mention.split('_')[1]

            match_trueMentionList = fuzzy_match(mention, doc_trueMention_tid[doc_id])
            
            for trueMention in match_trueMentionList:
                overlap.add(trueMention)

            if match_trueMentionList:
                overlap_prec.add(mid)

        miss = set(doc_trueMention_tid[doc_id].keys()) - overlap

        # if overlap:
        #     f1.write(str(doc_id) + '\t')
        #     for mention in overlap:
        #          f1.write(mention + '\t')
        #     f1.write('\n')         
        # if miss:
        #     f2.write(str(doc_id) + '\t')
        #     for mention in miss:
        #          f2.write(mention + '\t')
        #     f2.write('\n') 

        overlap_count += len(overlap)
        overlap_prec_count += len(overlap_prec)
        true_count += len(doc_trueMention_tid[doc_id].keys())
        predict_count += len(set(doc_mid[doc_id]))

    prec = overlap_prec_count / predict_count
    recall = overlap_count / true_count
    print 'Detected mention (fuzzy match): Recall =', recall, ', Precision =', prec

    return recall

def eval_recognition_fuzzy(Y, doc_trueMention_tid, doc_mid, mid_mention, target_tid_set):
    ### suppose R is our predicted mentions (without NIL); A is true Mentions
    ### precision: #correct in A&R / |A&R| or |R|
    ### recall: #correct in A&R / |A|
    tid_corr_prec = defaultdict(float)
    tid_corr_rec = defaultdict(float)
    tid_Rsize = defaultdict(float) # |A&R| or |R| of a type
    tid_Asize = defaultdict(float) # |A| of a type
    tid_prec = defaultdict(float)
    tid_recall = defaultdict(float)
    tid_f1 = defaultdict(float)

    for doc_id in doc_trueMention_tid:
        for mention in doc_trueMention_tid[doc_id]:
            true_tid = doc_trueMention_tid[doc_id][mention]
            if true_tid  in target_tid_set:
                tid_Asize[true_tid] += 1.0

        tid_match_trueMention = defaultdict(set)
        for mid in doc_mid[doc_id]:
            y = Y[mid, :]
            predict_tid = y.argmax()

            if predict_tid in target_tid_set: 
                # not NIL
                mention = mid_mention[mid]

                # tid_Rsize[predict_tid] += 1.0 # |R|
                match_trueMentionList = fuzzy_match(mention, doc_trueMention_tid[doc_id])
                if match_trueMentionList:
                    tid_Rsize[predict_tid] += 1.0 # |A&R|
                    
                    match_flag, match_trueMention = fuzzy_match_type(predict_tid, match_trueMentionList, doc_trueMention_tid[doc_id])
                    if match_flag:
                        tid_corr_prec[predict_tid] += 1.0
                        
                        tid_match_trueMention[predict_tid] = tid_match_trueMention[predict_tid] | match_trueMention
                        # tid_corr_rec[predict_tid] += 1.0 ## for >= max(len(mentionTokens), len(trueMentionTokens)) - 1 case

        for tid in tid_match_trueMention:
            tid_corr_rec[tid] += len(tid_match_trueMention[tid])


    corr_prec = 0.0
    corr_recall = 0.0
    Asize = 0.0
    Rsize = 0.0
    for tid in tid_Asize:
        Asize += tid_Asize[tid]
        Rsize += tid_Rsize[tid]
        if tid in tid_corr_rec:
            corr_prec += tid_corr_prec[tid]
            corr_recall += tid_corr_rec[tid]
            tid_recall[tid] = tid_corr_rec[tid] / tid_Asize[tid]
            tid_prec[tid] = tid_corr_prec[tid] / tid_Rsize[tid]
            tid_f1[tid] = 2*(tid_prec[tid]*tid_recall[tid])/(tid_prec[tid]+tid_recall[tid])
        else:
            tid_recall[tid] = 0.0
            tid_prec[tid] = 0.0
            tid_f1[tid] = 0.0

    prec = 0.0
    recall = 0.0
    f1 = 0.0
    if corr_prec > 0 and corr_recall > 0:
        prec = corr_prec/Rsize
        recall = corr_recall/Asize
        f1 = 2*(prec*recall)/(prec+recall)

    return (prec, recall, f1, tid_prec, tid_recall, tid_f1)


def test_recognition(result_path, Y, doc_trueMention_tid, doc_mid, mid_mention, tid_type, target_tid_set):
    ### start evaluation
    fff = open(result_path, 'w')

    doc_predictMention_tid, prec, recall, f1, tid_prec, tid_recall, tid_f1 = eval_recognition(Y, doc_trueMention_tid, doc_mid, mid_mention, target_tid_set)
    print '#test docs=', len(doc_trueMention_tid), ', Precision: ', prec, ', Recall', recall, ', F1', f1

    fff.write('#test docs=' + str(len(doc_trueMention_tid)) + ', Precision: ' + str(prec) + ', Recall: ' + str(recall) + ', F1: ' + str(f1) + '\n\n')
    for tid in tid_f1:
        # print tid_type[tid], ', prec: ', tid_prec[tid], ', recall: ', tid_recall[tid], ', F1: ', str(tid_f1[tid])
        fff.write(str(tid_type[tid]) + ', prec: ' + str(tid_prec[tid]) + ', recall: ' + str(tid_recall[tid]) + ', F1: ' + str(tid_f1[tid]) + '\n\n')
    

    ### fuzzy match results
    prec, recall, f1, tid_prec, tid_recall, tid_f1 = eval_recognition_fuzzy(Y, doc_trueMention_tid, doc_mid, mid_mention, target_tid_set)
    print '[Fuzzy Match]  Precision: ', prec, ', Recall', recall, ', F1', f1
    fff.write('[Fuzzy Match]  Precision:' + str(prec) + ', Recall: ' + str(recall) + ', F1: ' + str(f1) + '\n\n')
    for tid in tid_f1:
        # print tid_type[tid], ', prec: ', tid_prec[tid], ', recall: ', tid_recall[tid], ', F1: ', str(tid_f1[tid])
        fff.write(str(tid_type[tid]) + ', prec: ' + str(tid_prec[tid]) + ', recall: ' + str(tid_recall[tid]) + ', F1: ' + str(tid_f1[tid]) + '\n\n')

    return f1



############ Baseline evaluation ###############################
def eval_baseline(doc_mention_type, doc_trueMention_tid, tid_type, type_tid, target_tid_set):
    ### suppose R is our predicted mentions (without NIL); A is true Mentions
    ### precision: #correct in A&R / |A&R| or |R|
    ### recall: #correct in A&R / |A|
    tid_corr = defaultdict(float)
    tid_Rsize = defaultdict(float) # |A&R| or |R| of a type
    tid_Asize = defaultdict(float) # |A| of a type
    tid_prec = defaultdict(float)
    tid_recall = defaultdict(float)
    tid_f1 = defaultdict(float)

    for doc_id in doc_trueMention_tid:
        # evaluate in annotated docs
        for mention in doc_trueMention_tid[doc_id]:
            true_type = tid_type[doc_trueMention_tid[doc_id][mention]]
            if type_tid[true_type] in target_tid_set:
                tid_Asize[true_type] += 1.0

        for pair in doc_mention_type[doc_id]:
            predict_type = pair[1]
            mention_name = pair[0]
            mention = doc_id + '_' + mention_name
            
            if type_tid[predict_type] in target_tid_set: 

                tid_Rsize[predict_type] += 1.0 # |R|

                if mention in doc_trueMention_tid[doc_id]:
                    
                    # tid_Rsize[predict_type] += 1.0 # |A&R| -- this boost precision

                    if predict_type == tid_type[doc_trueMention_tid[doc_id][mention]]:
                        tid_corr[predict_type] += 1.0

    ### calculate metrics
    corr = 0.0
    Asize = 0.0
    Rsize = 0.0
    for tid in tid_Asize:
        Asize += tid_Asize[tid]
        Rsize += tid_Rsize[tid]
        if tid in tid_corr:
            corr += tid_corr[tid]
            tid_recall[tid] = tid_corr[tid] / tid_Asize[tid]
            tid_prec[tid] = tid_corr[tid] / tid_Rsize[tid]
            tid_f1[tid] = 2*(tid_prec[tid]*tid_recall[tid])/(tid_prec[tid]+tid_recall[tid])
        else:
            tid_recall[tid] = 0.0
            tid_prec[tid] = 0.0
            tid_f1[tid] = 0.0

    prec = 0.0
    recall = 0.0
    f1 = 0.0
    if corr > 0:
        prec = corr/Rsize
        recall = corr/Asize
        f1 = 2*(prec*recall)/(prec+recall)

    return (prec, recall, f1, tid_prec, tid_recall, tid_f1)


def eval_baseline_fuzzy(doc_mention_type, doc_trueMention_tid, tid_type, type_tid, target_tid_set):
    ### suppose R is our predicted mentions (without NIL); A is true Mentions
    ### precision: #correct in A&R / |A&R| or |R|
    ### recall: #correct in A&R / |A|
    tid_corr_prec = defaultdict(float)
    tid_corr_rec = defaultdict(float)
    tid_Rsize = defaultdict(float) # |A&R| or |R| of a type
    tid_Asize = defaultdict(float) # |A| of a type
    tid_prec = defaultdict(float)
    tid_recall = defaultdict(float)
    tid_f1 = defaultdict(float)


    for doc_id in doc_trueMention_tid:
        # evaluate in annotated docs

        for mention in doc_trueMention_tid[doc_id]:
            true_type = tid_type[doc_trueMention_tid[doc_id][mention]]
            if type_tid[true_type] in target_tid_set:
                tid_Asize[true_type] += 1.0

        tid_match_trueMention = defaultdict(set)
        for pair in doc_mention_type[doc_id]:
            predict_type = pair[1]
            mention_name = pair[0]
            mention = doc_id + '_' + mention_name
            
            if type_tid[predict_type] in target_tid_set: 

                # tid_Rsize[predict_type] += 1.0 # |R|
                match_trueMentionList = fuzzy_match(mention, doc_trueMention_tid[doc_id])
                if match_trueMentionList:
                    tid_Rsize[predict_type] += 1.0 # |A&R|
                    
                    predict_tid = type_tid[predict_type]
                    match_flag, match_trueMention = fuzzy_match_type(predict_tid, match_trueMentionList, doc_trueMention_tid[doc_id])
                    if match_flag:
                        tid_corr_prec[predict_type] += 1.0
                        
                        tid_match_trueMention[predict_type] = tid_match_trueMention[predict_type] | match_trueMention
                        # tid_corr_rec[predict_tid] += 1.0 ## for >= max(len(mentionTokens), len(trueMentionTokens)) - 1 case

        for type in tid_match_trueMention:
            tid_corr_rec[type] += len(tid_match_trueMention[type])

    ### calculate metrics
    corr_prec = 0.0
    corr_recall = 0.0
    Asize = 0.0
    Rsize = 0.0
    for tid in tid_Asize:
        Asize += tid_Asize[tid]
        Rsize += tid_Rsize[tid]
        if tid in tid_corr_rec:
            corr_prec += tid_corr_prec[tid]
            corr_recall += tid_corr_rec[tid]
            tid_recall[tid] = tid_corr_rec[tid] / tid_Asize[tid]
            tid_prec[tid] = tid_corr_prec[tid] / tid_Rsize[tid]
            tid_f1[tid] = 2*(tid_prec[tid]*tid_recall[tid])/(tid_prec[tid]+tid_recall[tid])
        else:
            tid_recall[tid] = 0.0
            tid_prec[tid] = 0.0
            tid_f1[tid] = 0.0

    prec = 0.0
    recall = 0.0
    f1 = 0.0
    if corr_prec > 0 and corr_recall > 0:
        prec = corr_prec/Rsize
        recall = corr_recall/Asize
        f1 = 2*(prec*recall)/(prec+recall)

    return (prec, recall, f1, tid_prec, tid_recall, tid_f1)



def test_baseline(result_path, doc_mention_type, doc_trueMention_tid, tid_type, type_tid, target_tid_set):
    ### start evaluation
    fff = open(result_path, 'w')

    prec, recall, f1, tid_prec, tid_recall, tid_f1 = eval_baseline(doc_mention_type, doc_trueMention_tid, tid_type, type_tid, target_tid_set)
    print '#test docs=', len(doc_trueMention_tid), ', Precision: ', prec, ', Recall', recall, ', F1', f1

    fff.write('#test docs=' + str(len(doc_trueMention_tid)) + ', Precision: ' + str(prec) + ', Recall: ' + str(recall) + ', F1: ' + str(f1) + '\n\n')
    for type in tid_f1:
        fff.write(type + ', prec: ' + str(tid_prec[type]) + ', recall: ' + str(tid_recall[type]) + ', F1: ' + str(tid_f1[type]) + '\n\n')
    
    ### fuzzy match results
    prec, recall, f1, tid_prec, tid_recall, tid_f1 = eval_baseline_fuzzy(doc_mention_type, doc_trueMention_tid, tid_type, type_tid, target_tid_set)
    print '[Fuzzy Match]  Precision: ', prec, ', Recall', recall, ', F1', f1
    fff.write('[Fuzzy Match]  Precision:' + str(prec) + ', Recall: ' + str(recall) + ', F1: ' + str(f1) + '\n\n')
    for type in tid_f1:
        fff.write(type + ', prec: ' + str(tid_prec[type]) + ', recall: ' + str(tid_recall[type]) + ', F1: ' + str(tid_f1[type]) + '\n\n')

    return 0

def isint(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
