from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
from data_model import *
from algorithm import *
from clustype import *
from evaluation import *
from sklearn.preprocessing import normalize
import sys

### Parameter setting #############################################################
segment_path = sys.argv[1]
ground_truth_path = sys.argv[2] # 'result/seed.txt'
type_path = sys.argv[3]
K = int(sys.argv[4]) # #RP clusters, K < 1000 --> 6G --> 24G at least
annotation_path = sys.argv[5]
annotationInText_path = sys.argv[6]

confidence_score = 0.9 # to get seeds: PercentageOfRank < 1-conf^2
TRAIN_RATIO = 1.0 # percentage of seeds used
VERBOSE = False

gamma = 0.5 # info from mention graph S_M
mu = 0.5 # supervision from Y_0
alpha = 1.0 # consistency with cluster consensus
lambda_O = 1.0 # information from Y
lambda_L = 1.0 # information from RP clustering

clustype_ITER = 5 # max iterations for our full-model
INNER_ITER = 200 #200  # max #iters for MultiNMF inner loop--perViewNMF
OUTER_ITER = 5 # maxIter for MultiNMF outer loop
ITER = 20 # max iter for variants
tol = 5e-4 # tolerance for convergence: perViewNMF, MultiNMF, full-model


cid_path = 'tmp/candidate_cid.txt'
mid_path = 'tmp/mention_mid.txt' # Y_0 = (mention, mid, initial_score)
pid_path = 'tmp/RP_pid.txt'
string_wid_path = 'tmp/string_wid.txt'
context_wid_path = 'tmp/context_wid.txt'
PiC_path = 'tmp/PiC.txt'
PiL_path = 'tmp/PiL.txt'
PiR_path = 'tmp/PiR.txt'
mention_graph_path = 'tmp/W_M.txt'
F_context_path = 'tmp/F_context.txt'
F_string_path = 'tmp/F_string.txt'

### data preparation' #############################################################
print 'Load graph...'
type_tid, tid_type, T = load_type_file(type_path)
cid_candidate, n = load_id(cid_path)
mid_mention, m = load_id(mid_path)
doc_mid = get_doc_mid(mid_mention) # doc_id - mid mapping
pid_RP, l = load_id(pid_path)
wid_string, ns = load_id(string_wid_path)
wid_context, nc = load_id(context_wid_path)
PiC = load_graph(PiC_path, m, n)
PiL = load_graph(PiL_path, m, l)
PiR = load_graph(PiR_path, m, l)
PiC = normalize(PiC, norm='l2', axis=0) # column-normalize PiC to ensure PiC.T*PiC = I
PiCC = PiC.T * PiC
PiL = normalize(PiL, norm='l2', axis=0) # column-normalize PiC to ensure PiC.T*PiC = I
PiLL = PiL.T*PiL
PiR = normalize(PiR, norm='l2', axis=0) # column-normalize PiC to ensure PiC.T*PiC = I
PiRR = PiR.T*PiR
S_L = normalize_graph(PiC.T * PiL)
S_R = normalize_graph(PiC.T * PiR)
print '#links in S_L:', len(S_L.nonzero()[0]), ', #links in S_R:', len(S_R.nonzero()[0])
W_M = load_graph(mention_graph_path, m, m)
S_M = normalize_graph(W_M)
print 'S_M dims', S_M.shape[0], S_M.shape[1], '#links in S_M:', len(S_M.nonzero()[0])
del W_M
F_context = load_graph(F_context_path, l, nc)
F_string = load_graph(F_string_path, l, ns)
print 'graph loading DONE'

### Partition seed mentions by ratio #############################################################
seedMention_tid_score = load_ground_truth(ground_truth_path, type_path, confidence_score)
seed_mid, _ = partition_train_test(mid_mention, TRAIN_RATIO)
Y0 = set_Y(seed_mid, seedMention_tid_score, mid_mention, m, T).todense()
print 'seeding DONE'

### run methods #############################################################
### target type set
target_tid_set = set()
for type in set(type_tid.keys()) - set(['NIL']):
	target_tid_set.add(type_tid[type])

print 'start ClusType...'
Y_noclus, C_noClus, PL_noClus, PR_noClus = clustype_noClus(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, ITER)
write_output(annotation_path, Y_noclus, doc_mid, mid_mention, tid_type)
write_output_intext(segment_path, annotationInText_path, Y_noclus, doc_mid, mid_mention, tid_type)

# print 'Start ClusType-Full... #Clusters:', K 
# Y_full = clustype_inexact(S_L, S_R, S_M, PiC, PiL, PiR, F_context, F_string, Y0, lambda_O, gamma, mu, \
# 	lambda_L, alpha, T, K, clustype_ITER, INNER_ITER, tol, Y_noclus, C_noClus, PL_noClus, PR_noClus, VERBOSE)
print 'ClusType done!'