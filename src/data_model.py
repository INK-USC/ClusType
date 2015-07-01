from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
from string import punctuation
import heapq
from scipy.sparse import *
from scipy import *
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import normalize
from numpy import *

def load_dict(file_name):
	dictionary = defaultdict(float)
	with open(file_name) as f:
		for line in f:
			entry = line.split('\t') # ',' or '\t' 
			if len(entry) == 2:
				dictionary[entry[0]] = float(entry[1])
	return dictionary


def find_first_left_RP_new(left_window):
	for i in range(len(left_window)):
		if left_window[-(i+1)].endswith(':RP'):
			RP_string = left_window[-(i+1)][:-len(':RP')].lower()

			if RP_string.startswith('ppv'):
				while RP_string.startswith('ppv'):
					RP_string = RP_string[len('ppv'):].strip()
			elif RP_string.endswith('ppv'):
				while RP_string.endswith('ppv'):
					RP_string = RP_string[:-len('ppv')].strip()

			if RP_string != '':
				return (RP_string, i)
			else:
				return (False, False)
	return (False, False)

def get_left_RP_new(left_window):
	# ad-hoc way
	RP, idx = find_first_left_RP_new(left_window)
	start_offset = idx
	end_offset = idx
	if RP:
		return [(RP, start_offset, end_offset)]
	else:
		return []

def find_first_right_RP_new(right_window):
	for i in range(len(right_window)):
		if right_window[i].endswith(':RP'):
			RP_string = right_window[i][:-len(':RP')].lower()

			if RP_string.startswith('ppv'):
				while RP_string.startswith('ppv'):
					RP_string = RP_string[len('ppv'):].strip()
			elif RP_string.endswith('ppv'):
				while RP_string.endswith('ppv'):
					RP_string = RP_string[:-len('ppv')].strip()

			if RP_string != '':
				return (RP_string, i)
			else:
				return (False, False)
	return (False, False)


def get_right_RP_new(right_window):
	# ad-hoc way
	RP, idx = find_first_right_RP_new(right_window)
	start_offset = idx + 1
	end_offset = idx + 1
	if RP:
		return [(RP, start_offset, end_offset)]
	else:
		return []


def construct_PiLR(PiL_RPs, PiR_RPs, mention_mid):
	PiL = defaultdict(float)
	PiR = defaultdict(float)
	RP_pid = defaultdict(int)
	pid_RP = defaultdict(str)
	pid = 0

	# most frequent one as the asscoaited RP
	for mention in mention_mid:

		if mention in PiL_RPs: 
			for RP in PiL_RPs[mention]:
				## add all RPs
				if RP not in RP_pid:
					RP_pid[RP] = pid
					pid_RP[pid] = RP
					pid += 1
				PiL[(mention_mid[mention][0], RP_pid[RP])] += 1.0

		if mention in PiR_RPs:
			for RP in PiR_RPs[mention]:
				## add all RPs
				if RP not in RP_pid:
					RP_pid[RP] = pid
					pid_RP[pid] = RP
					pid += 1
				PiR[(mention_mid[mention][0], RP_pid[RP])] += 1.0

	return (PiL, PiR, RP_pid, pid_RP)

def construct_PiLR_mostfreq(PiL_RPs, PiR_RPs, mention_mid):
	# most frequent one as the asscoaited RP for a mention

	PiL = defaultdict(int)
	PiR = defaultdict(int)
	RP_pid = defaultdict(int)
	pid_RP = defaultdict(str)
	pid = 0

	for mention in mention_mid:
		if mention in PiL_RPs: 

			RP_count = defaultdict(int)
			for RP in PiL_RPs[mention]:
				RP_count[RP] += 1
			RP = max(RP_count.iteritems(), key=itemgetter(1))[0]
			if RP not in RP_pid:
				RP_pid[RP] = pid
				pid_RP[pid] = RP
				pid += 1
			PiL[(mention_mid[mention][0], RP_pid[RP])] = RP_count[RP]

		if mention in PiR_RPs:
			RP_count = defaultdict(int)
			for RP in PiR_RPs[mention]:
				RP_count[RP] += 1
			RP = max(RP_count.iteritems(), key=itemgetter(1))[0]
			if RP not in RP_pid:
				RP_pid[RP] = pid
				pid_RP[pid] = RP
				pid += 1
			PiR[(mention_mid[mention][0], RP_pid[RP])] = RP_count[RP]

	return (PiL, PiR, RP_pid, pid_RP)

### Mention Graph
# Sol 1: use non-stopword, non-RP unigrams within sentence as context words
def get_mention_context(context_window, stoplist):
	context = []
	for term in context_window:
	
		### both EP and non-RP as contexts
		if not term.endswith(':RP'):
			if term.endswith(':EP'):
				term = term[:-len(':EP')]
			term = term.lower()

		 	if term not in stoplist:
		 		context.append(term)

		 		# add unigram
		 		if ' ' in term:
		 			for unigram in term.split():
		 				if unigram not in stoplist:
		 					context.append(unigram)
	return context

def construct_WM(mention_context, mention_context_DF, doc_num, candidate_degree, mention_mid, K):
	W_M = defaultdict(float)
	count = 0
	miss = 0

	# Sol 1: KNN graph by Euclidean distance
	for candidate in candidate_degree:

		## sklearn.neighbors
		mid = 0
		m_mid = defaultdict(int)
		mid_m = defaultdict(int)
		wid = 0
		w_wid = defaultdict(int)
		val = []
		row = []
		col = []
		k_adapt = min(K, len(candidate_degree[candidate])-1)

		if k_adapt > 0:

			for mention in candidate_degree[candidate]:

				if mention not in m_mid:
					m_mid[mention] = mid
					mid_m[mid] = mention
					mid += 1

				w_tf = defaultdict(float)
				for word in mention_context[mention]:
					if word not in w_wid:
						w_wid[word] = wid
						wid += 1
					w_tf[word] += 1.0 

				if len(w_tf) > 0:
					# TF-IDF weight (similar to PMI between mention and terms)
					max_tf = max(w_tf.iteritems(), key=itemgetter(1))[1]
					for word in w_tf:
						tf = 0.5 + 0.5 * w_tf[word] / max_tf
						tfidf = tf * log( doc_num / (1.0 + len(mention_context_DF[word])) )

						row.append(m_mid[mention])
						col.append(w_wid[word])
						val.append(tfidf)
						
			if mid > 0 and wid > 0:
				if mid * wid < 1890600000:
					G_mention_context = coo_matrix((val, (row, col)), shape = (mid, wid)).tocsr()
					# normalize each row to unit vector
					G_mention_context = normalize(G_mention_context, norm='l2', axis=1, copy=True)
					KNN_graph = kneighbors_graph(G_mention_context, k_adapt, mode='distance')
					ridx, cidx = KNN_graph.nonzero()
					for i in range(len(ridx)):
						mention1 = mid_m[ridx[i]]
						mention2 = mid_m[cidx[i]]
						sim = exp( -KNN_graph[ridx[i], cidx[i]]**2 / 2 ) # heat kernel with t=2
						W_M[(mention_mid[mention1][0], mention_mid[mention2][0])] = sim
						W_M[(mention_mid[mention2][0], mention_mid[mention1][0])] = sim
				else: # too high dimensional to get knn!
					print candidate, mid, wid
					miss += 1
			else: # no context for this candidate's mentions at all!
				# print candidate, mid, wid
				miss += 1
		count += 1
		if count % 10000 == 0:
			print count
	return (W_M, miss)


def get_RP_context(context_window, stoplist):
	context = []
	for term in context_window:
		
		if not term.endswith(':RP'):

			if term.endswith(':EP'):
				term = term[:-len(':EP')]
			term = term.lower()

			if term not in stoplist:
				# context.append(term)

				for unigram in term.split():
					unigram = unigram.strip().strip(punctuation)
					if unigram != '' and unigram not in stoplist:
						context.append(unigram)
	return context

def feature_generation(RP_pid, RP_context, RP_context_DF, doc_num, stoplist):
	string_wid = defaultdict(int)
	context_wid = defaultdict(int)
	F_string = defaultdict(float)
	F_context = defaultdict(float)
	miss = 0

	wid_s = 0
	wid_c = 0
	for RP in RP_pid:

		# mention's string
		vector_sum = 0.0
		string_set = set()
		for word in RP.split():
			if word != 'ppv': ####
				string_set.add(word)
				vector_sum += 1.0
				if word not in string_wid:
					string_wid[word] = wid_s
					wid_s += 1
				F_string[(RP_pid[RP], string_wid[word])] = 1.0

		# normalize each sample to unit vector
		for word in string_set:
			F_string[(RP_pid[RP], string_wid[word])] = F_string[(RP_pid[RP], string_wid[word])] / sqrt(vector_sum)

		# mention's contexts
		context_tf = defaultdict(float)
		if RP in RP_context:

			for word in RP_context[RP]:
				if len(RP_context_DF[word]) > 1: # MIN_SUP for RP's context words = 1
					if word not in context_wid:
						context_wid[word] = wid_c
						wid_c += 1
					context_tf[word] += 1.0

			if len(context_tf) > 0:
				vector_sum = 0.0
				max_tf = max(context_tf.iteritems(), key=itemgetter(1))[1]
				for word in context_tf:	
					tf = 0.5 + 0.5 * context_tf[word] / max_tf
					tfidf = tf * log( doc_num / (1.0 + len(RP_context_DF[word])) )
					F_context[(RP_pid[RP], context_wid[word])] = tfidf
					vector_sum += tfidf**2

				# normalize each sample to unit vector
				for word in context_tf:
					F_context[(RP_pid[RP], context_wid[word])] = F_context[(RP_pid[RP], context_wid[word])] / sqrt(vector_sum)
		else:
			miss += 1
	# print 'total# RPs with no context: ', miss
	return (F_string, F_context, string_wid, context_wid)




def dump_id(file_name, ID):
	with open(file_name, 'w') as f:
		for name in ID:
			f.write(str(name) + '\t' + str(ID[name]) + '\n')
	return 0

def dump_mid(file_name, ID):
	with open(file_name, 'w') as f:
		for name in ID:
			f.write(str(name) + '\t' + str(ID[name][0]) + '\n')
	return 0

def dump_PiC(file_name, Pi):
	with open(file_name, 'w') as f:
		for i in Pi:
			f.write(str(i) + '\t' + str(Pi[i]) + '\t1\n')
	return 0

def dump_PiL(file_name, Pi):
	with open(file_name, 'w') as f:
		for pair in Pi:
			f.write(str(pair[0]) + '\t' + str(pair[1]) + '\t' + str(Pi[pair]) + '\n')
	return 0

def dump_PiR(file_name, Pi):
	with open(file_name, 'w') as f:
		for pair in Pi:
			f.write(str(pair[0]) + '\t' + str(pair[1]) + '\t' + str(Pi[pair]) + '\n')
	return 0

def dump_graph(file_name, graph):
	with open(file_name, 'w') as f:
		for node_pair in graph:
			f.write(str(node_pair[0]) + '\t' + str(node_pair[1]) + '\t' + str(graph[node_pair]) + '\n')
	return 0

def load_id(file_name):
	name_id = defaultdict(int)
	with open(file_name) as f:
		for line in f:
			if len(line.split('\t')) == 2:
				pair = line.split('\t')
				name_id[int(pair[1])] = pair[0]
	# print len(name_id)
	return (name_id, len(name_id))

def load_graph(file_name, size_row, size_col):
    row = []
    col = []
    val = []
    max_row_idx = 0
    max_col_idx = 0
    with open(file_name) as f:
        for line in f:
            entry = line.split('\t')
            if len(entry) == 3:
                row.append(int(entry[0]))
                col.append(int(entry[1]))
                val.append(float(entry[2]))
                max_row_idx = max(max_row_idx, int(entry[0]))
                max_col_idx = max(max_col_idx, int(entry[1]))
    # print max_row_idx, max_col_idx
    # print 'loaded matrix, #rows:', size_row,  ', #cols:', size_col
    G = coo_matrix((val, (row, col)), shape = (size_row, size_col)).tocsr()
    return G

def normalize_graph(G):
	# print 'row-by-col = ', G.shape
	G_col = G.sum(axis=0)# 1-by-#col vector
	G_row = G.sum(axis=1) # #row-by-1 vector

	miss_col = 0
	col_val = []
	for i in range(G_col.shape[1]):
		val = G_col[0, i]
		if val > 0:
			col_val.append(pow(val, -0.5))
		else:
			col_val.append(0.0)
			miss_col += 1

	miss_row = 0
	row_val = []
	for i in range(G_row.shape[0]):
		val = G_row[i, 0]
		if val > 0:
			row_val.append(pow(val, -0.5))
		else:
			row_val.append(0.0)
			miss_row += 1
	# print miss_row, 'rows missed', miss_col, 'col missed'

	G = diags(row_val, 0) * G * diags(col_val, 0)
	return G

def print_sorted_graph(graph, rid_rname, cid_cname, file_name):
	graph_sorted = sorted(graph.iteritems(), key=itemgetter(1), reverse=True)
	with open(file_name, 'w') as f:
		for pair in graph_sorted:
			rname = rid_rname[pair[0][0]]
			cname = cid_cname[pair[0][1]]
			f.write( rname + '\t' + cname + '\t' + str(pair[1]) + '\n')
	print 'output graph DONE'
	return 0

def print_WL(graph, rid_rname, cid_cname, file_name):
	row, col = graph.nonzero()
	graph_dump = defaultdict(float)
	for i in range(len(row)):
		graph_dump[(row[i], col[i])] = graph[row[i], col[i]]

	graph_sorted = sorted(graph_dump.iteritems(), key=itemgetter(1), reverse=True)
	with open(file_name, 'w') as f:
		for pair in graph_sorted:
			rname = rid_rname[pair[0][0]]
			cname = cid_cname[pair[0][1]]
			f.write( '[' + rname + ']\t' + cname + '\t' + str(pair[1]) + '\n')
	return 0

def print_WR(graph, rid_rname, cid_cname, file_name):
	row, col = graph.nonzero()
	graph_dump = defaultdict(float)
	for i in range(len(row)):
		graph_dump[(row[i], col[i])] = graph[row[i], col[i]]

	graph_sorted = sorted(graph_dump.iteritems(), key=itemgetter(1), reverse=True)
	with open(file_name, 'w') as f:
		for pair in graph_sorted:
			rname = rid_rname[pair[0][0]]
			cname = cid_cname[pair[0][1]]
			f.write(  cname + '\t[' + rname + ']' + '\t' + str(pair[1]) + '\n')
	return 0
