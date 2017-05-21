from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
import random as rn
import time
from numpy import * # install numpy
from scipy import * # install scipy
from numpy.linalg import norm
import numpy.linalg as npl
from scipy.sparse import *
import scipy.sparse.linalg as spsl
from sklearn.preprocessing import normalize ### install from http://scikit-learn.org/stable/


def create_matrix(size_row, size_col):
    return csr_matrix((size_row, size_col))

def create_dense_matrix(size_row, size_col):
    return mat(zeros((size_row, size_col)))

def set_Y(train_mid, seedMention_tid_score, mid_mention, size_row, size_col):
    row = []
    col = []
    val = []
    num_NIL = 0
    num_target = 0
    NIL_set = set()
    for mid in train_mid:
        # in training set
        mention = mid_mention[mid]
        if mention in seedMention_tid_score:
            # in ground truth
            tid = seedMention_tid_score[mention][0]
            score = seedMention_tid_score[mention][1]
            
            if tid == (size_col - 1):
                # NIL
                num_NIL += 1
                # NIL_set.add((mid, tid, score))
                NIL_set.add((mid, tid, 1.0))
            else:
                num_target += 1
                row.append(mid)
                col.append(tid)
                # val.append(score)
                val.append(1.0)

    if num_target < 1:
        print 'No target type entity seeded!!!!'

    ### random sample NIL examples
    # neg_size = num_NIL
    neg_size = min(num_NIL, 5*num_target)
    # neg_size = int(min(num_NIL, num_target/(size_col-1.0)))

    neg_example = rn.sample(NIL_set, neg_size)
    for entry in neg_example:
        row.append(entry[0])
        col.append(entry[1])
        val.append(entry[2])

    Y = coo_matrix((val, (row, col)), shape = (size_row, size_col)).tocsr()
    
    # print Y.nnz, '#ground truth mentions in Y'
    print 'Percent Seeded Mention:', (Y.nnz+0.0)/len(mid_mention) * 100, '% of', len(mid_mention), \
    ', #target/All = ', num_target/(Y.nnz+0.0) * 100
    
    return Y


def update_Y_closed_form(S_M, Y, Y0, Theta, PiC, gamma, mu):
    # row = []
    # col = []
    # val = []

    for j in range(PiC.shape[1]):
        # for each candidate j, slicing to get submatrix
        mid_list = PiC[:, j].nonzero()[0].tolist()
        Y0_j = Y0[mid_list, :]
        Theta_j = Theta[mid_list, :]
        S_M_j = S_M[mid_list, :][:, mid_list]

        if S_M_j.shape[0] * S_M_j.shape[1] < 2520800000:

            # transform to dense matrix
            tmp = ((1+gamma+mu)*identity(len(mid_list)) - gamma*S_M_j).todense()
            Y_j = npl.inv(tmp) * (Theta_j + mu*Y0_j)
            Y[mid_list, :] = Y_j

            # # sparse 
            # Yc = spsl.inv((1+gamma+mu)*identity(len(mid_list)) - gamma*S_M_j) * (Theta_j + mu*Y0_j)
            # Yc = spsl.spsolve( ((1+gamma+mu)*identity(len(mid_list)) - gamma*S_M_j), (Theta_j + mu*Y0_j) )
            # row_idx, col_idx = Yc.nonzero()
            # for i in range(len(row_idx)):
            #     mid = mid_list[row_idx[i]]
            #     row.append(mid)
            #     col.append(col_idx[i])
            #     val.append(Yc[row_idx[i], col_idx[i]])

        if j % 1000 == 0:
            print 'candidate', j

    # Y = coo_matrix((val, (row, col)), shape = Y0.shape).tocsr()
    return Y



def inverse_matrix(X):
    X.data[:] = 1/(X.data)
    return X


def clustype_appx(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, ITER, K):
    PiLL = PiL.T*PiL
    PiRR = PiR.T*PiR

    ### initialization #############################################################
    m = PiC.shape[0]
    n, l = S_L.shape
    C = create_dense_matrix(n, T)
    PL = create_dense_matrix(l, T)
    PR = create_dense_matrix(l, T)
    Y = Y0.copy()
    Theta = PiC*C + PiL*PL + PiR*PR
    obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
    lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

    ### Start algorithm #############################################################
    for i in range(ITER):

        lambda4 = 1+gamma+mu
        Y = 1/lambda4 * (gamma*S_M*Y + Theta + mu*Y0)
        C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*(Y-PiL*PL-PiR*PR) )
        PL = inverse_matrix(identity(PiL.shape[1]) + lambda_O*PiLL) * (S_L.T*C + lambda_O*PiL.T*(Y-PiC*C-PiR*PR))
        PR = inverse_matrix(identity(PiR.shape[1]) + lambda_O*PiRR) * (S_R.T*C + lambda_O*PiR.T*(Y-PiC*C-PiL*PL))
        
        obj_old = obj
        Theta = PiC*C + PiL*PL + PiR*PR
        obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
        lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))
        
        if (i+1) % 10 == 0:
            print 'iter', i+1, 'obj: ', obj, 'rel obj change: ', (obj_old-obj)/obj_old

    # Y = PiC*C
    # Y = PiL*PL + PiR*PR
    Y = PiC*C + PiL*PL + PiR*PR
    return (Y, C, PL, PR)


def clustype_noClus_inner(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, ITER, tol, C, PL, PR, Y):
    PiLL = PiL.T*PiL
    PiRR = PiR.T*PiR

    ### initialization #############################################################
    m = PiC.shape[0]
    n, l = S_L.shape

    Theta = PiC*C + PiL*PL + PiR*PR
    obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
    lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

    ### Start algorithm #############################################################
    for i in range(ITER):

        lambda4 = 1+gamma+mu
        Y = 1/lambda4 * (gamma*S_M*Y + Theta + mu*Y0)
        C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*(Y-PiL*PL-PiR*PR) )
        PL = inverse_matrix(identity(PiL.shape[1]) + lambda_O*PiLL) * (S_L.T*C + lambda_O*PiL.T*(Y-PiC*C-PiR*PR))
        PR = inverse_matrix(identity(PiR.shape[1]) + lambda_O*PiRR) * (S_R.T*C + lambda_O*PiR.T*(Y-PiC*C-PiL*PL))
        
        obj_old = obj
        Theta = PiC*C + PiL*PL + PiR*PR
        obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
        lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))
        rel = abs(obj_old - obj)/obj_old
        
        if (i+1) % 10 == 0:
            print '\tClusType_noClus_inner Iter', i+1, 'obj: ', obj, 'rel obj change: ', (obj_old-obj)/obj_old

        if rel < tol:
            print '  ClusType_noClus_inner Converges!'
            Y = PiC*C + PiL*PL + PiR*PR
            return (Y, C, PL, PR)

    # Y = PiC*C
    # Y = PiL*PL + PiR*PR
    Y = PiC*C + PiL*PL + PiR*PR
    print '  ClusType_noClus_inner Reach MaxIter!'
    return (Y, C, PL, PR)


def clustype_noClus_PiLR(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, ITER):
    ### pre-compuatation #############################################################
    m = PiC.shape[0]
    n, l = S_L.shape
    PiLL = PiL.T*PiL # l-by-l
    PiRR = PiR.T*PiR # l-by-l

    ### initialization #############################################################
    C = create_dense_matrix(n, T)
    PL = create_dense_matrix(l, T)
    PR = create_dense_matrix(l, T)
    Y = Y0.copy()
    theta = PiL*PL + PiR*PR
    obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
    lambda_O*(norm(Y-theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

    ### Start algorithm #############################################################
    for i in range(ITER):
        
        lambda4 = 1+gamma+mu
        Y = 1/lambda4 * (gamma*S_M*Y + theta + mu*Y0)
        C = 1/2.0 * ( S_L*PL + S_R*PR )
        PL = inverse_matrix(identity(PiL.shape[1]) + lambda_O*PiLL) * lambda_O*PiL.T*(Y-PiR*PR)
        PR = inverse_matrix(identity(PiR.shape[1]) + lambda_O*PiRR) * lambda_O*PiR.T*(Y-PiL*PL)

        obj_old = obj
        theta = PiL*PL + PiR*PR
        obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
        lambda_O * (norm(Y-theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))
        
        if (i+1) % 10 == 0:
            print 'iter', i+1, 'obj: ', obj, 'rel obj change: ', (obj_old-obj)/obj_old

    Y = PiL*PL + PiR*PR

    return Y


def clustype_noClus_PiC(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, ITER):
    ### initialization #############################################################
    m = PiC.shape[0]
    n, l = S_L.shape
    C = create_dense_matrix(n, T)
    PL = create_dense_matrix(l, T)
    PR = create_dense_matrix(l, T)
    Y = Y0.copy()
    obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
    lambda_O * (norm(Y-PiC*C,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

    ### Start algorithm #############################################################
    for i in range(ITER):

        lambda4 = 1+gamma+mu
        Y = 1/lambda4 * (gamma*S_M*Y + PiC*C + mu*Y0)
        C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*Y )
        PL = S_L.T*C 
        PR = S_R.T*C

        obj_old = obj
        obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
        lambda_O * (norm(Y-PiC*C,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))
        
        if (i+1) % 10 == 0:
            print 'iter', i+1, 'obj: ', obj, 'rel obj change: ', (obj_old-obj)/obj_old

    Y = PiC*C
    
    return Y



def clustype_onlycandidate(S_L, S_R, PiC, PiL, PiR, Y0, T, ITER):
    ### pre-compuatation #############################################################
    u = 0.5 # u=0.5

    ### initialization #############################################################
    m = PiC.shape[0]
    n, l = S_L.shape
    C0 =  PiC.T * Y0
    C = C0.copy()
    PL = create_dense_matrix(l, T)
    PR = create_dense_matrix(l, T)

    Theta = PiC*C + PiL*PL + PiR*PR
    obj = trace((2+u)*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR - 2*u*C.T*C0 + u*C0.T*C0)

    ### Start algorithm #############################################################
    for i in range(ITER):
        
        C = 1/(2+u) * (S_L*PL + S_R*PR + u*C0)
        PL = S_L.T*C
        PR = S_R.T*C

        obj_old = obj
        obj = trace((2+u)*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR - 2*u*C.T*C0 + u*C0.T*C0)

        if (i+1) % 10 == 0:
            print 'ClusType_Cand Iter', i+1, 'obj: ', obj, 'rel obj change: ', (obj_old-obj)/obj_old

    Y = PiC*C

    return (Y, C, PL, PR)
    