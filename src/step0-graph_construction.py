from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
from data_model import *
from string import punctuation
import sys
import os

### Parameters #############################################################
CANDIDATE_MINSUP = 1 # min_sup of mentions for each candidate -->  =1 leads to 91% fuzzy Recall
RP_CONTEXT_WINDOW_SIZE = 2 # context windows size for F_context
K_SM = 1 # number of nearest neighbors in S_M

### Input #############################################################
if not os.path.exists('tmp'):
    os.makedirs('tmp')
if not os.path.exists('result'):
    os.makedirs('result')

corpus_path = sys.argv[1] # 'result/segment.txt'
stop_path =  'data/stopwords.txt'
with open(stop_path) as f:
	stoplist = set([line.strip() for line in f])
entity_stoplist = stoplist

stat_path = sys.argv[2]
fff = open(stat_path, 'w')
fff.write('CANDIDATE_MINSUP='+str(CANDIDATE_MINSUP)+', RP_CONTEXT_WINDOW_SIZE='+str(RP_CONTEXT_WINDOW_SIZE)+', K_SM='+str(K_SM)+'\n')

PiC_path = 'tmp/PiC.txt'
cid_path = 'tmp/candidate_cid.txt'
mid_path = 'tmp/mention_mid.txt' # Y_0 = (mention, mid, initial_score)
pid_path = 'tmp/RP_pid.txt'
PiL_path = 'tmp/PiL.txt'
PiR_path = 'tmp/PiR.txt'
mention_graph_path = 'tmp/W_M.txt' # mention-mention graph
F_string_path = 'tmp/F_string.txt'
string_wid_path = 'tmp/string_wid.txt'
F_context_path = 'tmp/F_context.txt'
context_wid_path = 'tmp/context_wid.txt'

### Canaidate-Relation Phrase Graph #############################################################
candidate_cid = defaultdict(int)
cid_candidate = defaultdict(str)
candidate_degree = defaultdict(set)

RP_pid = defaultdict(int)
pid_RP = defaultdict(str)

mention_mid = defaultdict(tuple)
mid_mention = defaultdict(str)
mention_context = defaultdict(list) # mention's doc-level contextual mentions
mention_context_DF = defaultdict(set) # doc-frequency for mention's doc-level contextual mentions
doc_mention = defaultdict(list)
W_M = defaultdict(float)

PiC = defaultdict(int)
PiL = defaultdict(int)
PiL_RPs = defaultdict(list) # for PiL construction
PiR = defaultdict(int)
PiR_RPs = defaultdict(list) # for PiR construction

RP_context = defaultdict(list) # context terms for RPs
RP_context_DF = defaultdict(set) # doc-frequency for context terms
string_wid = defaultdict(int) # term-wid for mention strings
context_wid = defaultdict(int) # term-wid for mention contexts
F_string = defaultdict(float) # feature matrix for mention string
F_context = defaultdict(float) # feature matrix for mention context

### start passing corpus #############################################################
doc_set = set()
print 'start parsing the corpus...'
with open(corpus_path) as f:
	for line in f:
		if '\t' in line.strip():
			doc_id, sentence = line.strip().split('\t')
			if (len(doc_set)+1) % 10000 == 0 and doc_id not in doc_set:
				print len(doc_set)+1
			doc_set.add(doc_id)
			term_list = sentence.strip().split(',')
			
			RP_set = set() # to store unique RPs in each sentence
			for idx in range(len(term_list)):

				if term_list[idx].endswith(':EP'):

					### Get mention's relation phrase
					if idx >= 1:
						left_window = term_list[:idx]
						left_RPs = get_left_RP_new(left_window)
					else:
						left_RPs = []
						left_window = []

					if idx < (len(term_list) - 1):
						right_window = term_list[(idx+1):]
						right_RPs = get_right_RP_new(right_window)
					else:
						right_RPs = []
						right_window = []

					### add to candidate_list if is valid mention
					if len(left_RPs)>0 or len(right_RPs)>0:

						candidate = term_list[idx][:-len(':EP')].lower().strip(punctuation)
						mention = doc_id + '_' + candidate
						candidate_degree[candidate].add(mention) # new mention added

						# get mention context from SENTENCE WINDOW
						context_list = get_mention_context(left_window+right_window, stoplist)
						mention_context[mention].extend(context_list)
						for term in context_list:
							mention_context_DF[term].add(doc_id)

						# Check left side for relation phrase (RP's right argument)
						if len(left_RPs) > 0:
							for triple in left_RPs:
								PiR_RPs[mention].append(triple[0])

						# check right side for relation phrase (RP's left argument)
						if len(right_RPs) > 0:
							for triple in right_RPs:
								PiL_RPs[mention].append(triple[0])

						# get RP's context
						for triple in left_RPs + right_RPs:
							RP = triple[0]
							start_idx = triple[1] + idx
							end_idx = triple[2] + idx

							### Get RP's context window
							if start_idx >= 1:
								left_window = term_list[max(start_idx-RP_CONTEXT_WINDOW_SIZE, 0): start_idx]
							else:
								left_window = []
							# print 'left_window', left_window

							if end_idx < (len(term_list) - 1):
								right_window = term_list[(end_idx+1): min(end_idx+1+RP_CONTEXT_WINDOW_SIZE, len(term_list))]
							else:
								right_window = []
							# print 'right_window', right_window

							context_list = get_RP_context(left_window+right_window, stoplist)
							RP_context[RP].extend(context_list)
							for term in context_list:
								RP_context_DF[term].add(doc_id)


print 'construct WL, WR, PiL, PiR DONE'
print '#mention before filter:', len(mention_context), ', #PiL rows:', len(PiL_RPs), ', #PiR rows:', len(PiR_RPs), ', #candidates before filter:', len(candidate_degree)
fff.write('#mention before filter: ' +  str(len(mention_context)) + ', #candidates before filter:' + str(len(candidate_degree)) + ', #RPs before filter' + str(len(RP_context)) + '\n')

### Candidate/mention filtering #############################################################
print 'start filtering mentions...'
for candidate in candidate_degree.keys():
	if candidate == '' or len(candidate_degree[candidate]) < CANDIDATE_MINSUP or candidate in entity_stoplist:
		for mention in candidate_degree[candidate]:
			# delete mentions of the candidate
			mention_context.pop(mention, None)
			PiL_RPs.pop(mention, None)
			PiR_RPs.pop(mention, None)
		candidate_degree.pop(candidate, None)
print 'filter mentions DONE'


### construct mention-mid, candidate-cid, PiC #############################################################
print 'start construct mid, cid, PiC...'
mid = 0
cid = 0
candidate_mentioncount = defaultdict(int)
contextcount = defaultdict(float)
for mention in mention_context:
	mention_mid[mention] = (mid, 7, 0.0) # (mid, type=NIL, confidence=0.0)
	mid_mention[mid] = mention
	mid += 1

	# candidate-cidk
	candidate = mention.split('_')[1]
	if candidate not in candidate_cid:
		candidate_cid[candidate] = cid
		cid_candidate[cid] = candidate
		cid += 1
	# add PiC
	PiC[mention_mid[mention][0]] = candidate_cid[candidate]
	# add mention count
	candidate_mentioncount[candidate] += 1
dump_PiC(PiC_path, PiC)
dump_id(cid_path, candidate_cid)
dump_mid(mid_path, mention_mid)
print 'construct mention-mid, PiC, candidate-cid DONE'
print '#mentions after filter:', len(mention_mid), ', PiC #rows:', len(PiC), ', #candidates after filter:', len(candidate_cid)
a, b = max(candidate_mentioncount.iteritems(), key=itemgetter(1))
print 'candidate, max# mentions: ', a, b
print 'candidate avg# mentions: ', (mid+0.0)/cid
fff.write('#mention after filter: ' +  str(len(mention_mid)) + ', #candidates after filter:' + str(len(candidate_cid)) + ', candidate avg#mentions' + str((mid+0.0)/cid) + ', candidate, max# mentions: '+a +', '+str(b) + '\n')
del PiC


### PiL, PiR, RP_pid, pid_RP construction #############################################################
print 'start construct PiL, PiR, RP_pid'
# PiL, PiR, RP_pid, pid_RP = construct_PiLR(PiL_RPs, PiR_RPs, mention_mid) ## use all RPs of a mention
PiL, PiR, RP_pid, pid_RP = construct_PiLR_mostfreq(PiL_RPs, PiR_RPs, mention_mid) ## use most freq RP of a mention
del PiL_RPs
del PiR_RPs

dump_id(pid_path, RP_pid)
dump_PiL(PiL_path, PiL)
dump_PiR(PiR_path, PiR)
print 'construct PiL, PiR, RP_pid DONE'
print '#RPs:', len(RP_pid)
fff.write('#RPs after filter: ' +  str(len(RP_pid)) + '\n')
del PiL
del PiR

PiL = load_graph(PiL_path, len(mid_mention), len(pid_RP))
PiR = load_graph(PiR_path, len(mid_mention), len(pid_RP))
PiLR_row = (PiL+PiR).sum(axis=0)
count = 0
for i in range(PiLR_row.shape[1]):
	if PiLR_row[0, i] == 0:
		count += 1
del PiL
del PiR

### Mention-Mention Graph #############################################################
print 'start mention KNN graph construction...'
W_M, miss = construct_WM(mention_context, mention_context_DF, len(doc_set), candidate_degree, mention_mid, K_SM)
dump_graph(mention_graph_path, W_M)
print 'construct W_M DONE'
fff.write('#edges in W_M: ' +  str(len(W_M)) + ', total #candidates with no mention graphs:' + str(miss) + '\n')
del W_M


### clustering feature generation #############################################################
print 'start feature generation...'
F_string, F_context, string_wid, context_wid = feature_generation(RP_pid, RP_context, RP_context_DF, len(doc_set), stoplist)
dump_graph(F_string_path, F_string)
dump_id(string_wid_path, string_wid)
dump_graph(F_context_path, F_context)
dump_id(context_wid_path, context_wid)
print 'generate feature matrices, string_wid, context_wid DONE'
print '#RP string terms:', len(string_wid), ', #RP context terms:', len(context_wid)
fff.write('#RP string terms: ' +  str(len(string_wid)) + ', #RP context terms:' + str(len(context_wid)) + '\n')
fff.close()