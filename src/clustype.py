from collections import defaultdict
from operator import itemgetter
from math import log, sqrt
import random
import time
from numpy import * # install numpy
from scipy import * # install scipy
from numpy.linalg import norm
import numpy.linalg as npl
from scipy.sparse import *
import scipy.sparse.linalg as spsl
from sklearn.preprocessing import normalize ### install from http://scikit-learn.org/stable/
from algorithm import *


def getMatPos(X): # sparse matrix or matrix
	Xpos = (abs(X) + X)/2
	Xneg = (abs(X) - X)/2
	return (Xpos, Xneg)

def normalize_V(V):
	# column-normalized
	V = mat(normalize(V, norm='l2', axis=0))
	return V

def normalize_U(U):
	# joint prob. 
	U = U/sum(U)
	return U

def normalizeUV_noNorm(U, V):
	V_colSum = maximum(V.sum(axis=0), 1e-10)
	Q = diags(asarray(V_colSum)[0,:], 0)
	Qinv = diags(asarray(1.0/V_colSum)[0,:], 0)
	U = U*Q # n-by-K
	V = V*Qinv # d-by-K
	return (U, V, Q)

def normalizeUV(U, V, X_Fnorm):
	X_Fnorm = max(X_Fnorm, 1e-10)
	V_colSum = maximum(V.sum(axis=0), 1e-10)
	Q = diags(asarray(V_colSum/X_Fnorm)[0,:], 0)
	Qinv = diags(asarray(X_Fnorm/V_colSum)[0,:], 0)
	U = U*Q # n-by-K
	V = V*Qinv # d-by-K
	return (U, V, Q)

def calculate_obj_NMF(X, U, V, trXTX):
	UTU = U.T*U
	VTV = V.T*V
	UTX = U.T*X
	obj = sqrt(trXTX + trace(VTV*UTU) - 2*trace(UTX*V))
	return obj

def NMF(X, U, V, INNER_ITER, tol, VERBOSE):
	## X -- nSam x nFea data matrix (dense for PL, PR, sparse for Fs, Fc)
	## U -- nSam x K cluster membership for samples (dense)
	## V -- nFea x K (dense)
	Xpos, Xneg = getMatPos(X)
	U, V, _ = normalizeUV_noNorm(U, V)
	trXTX = sum((X.T*X).diagonal())
	obj = calculate_obj_NMF(X, U, V, trXTX) ### Ucannot handle U*V.T -- n-by-d dense matrix

	if VERBOSE:
		print '\tNMF start...'

	for iter in range(INNER_ITER):
		
		## Update U
		# multiply(A, B) means element-wise multiplication
		XposV = Xpos*V # n-by-K
		XnegV = Xneg*V # n-by-K
		UVTV = U*(V.T*V) # n-by-K
		U = multiply(U, XposV/maximum(UVTV+XnegV, 1e-10))

		## Update V
		XposTU = Xpos.T*U # d-by-K
		XnegTU = Xneg.T*U # d-by-K
		UTU = U.T*U # k-by-k
		VUTU = V*UTU # d-by-K
		V = multiply(V, XposTU/maximum(VUTU+XnegTU, 1e-10))

		U, V, Q = normalizeUV_noNorm(U, V)

		# print iter
		obj_old = obj
		obj = calculate_obj_NMF(X, U, V, trXTX)
		rel = (obj_old - obj)/obj_old

		# calculate obj
		if iter % 10 == 0 and iter > 0:
			if VERBOSE:
				print '\tinner loop:', iter, obj, rel

		if abs(rel) < tol:
			if VERBOSE:
				print '\tNMF converges!', iter, obj, rel
			return (U, V, obj)

	if VERBOSE:
		print '\treach NMF MaxIter!', iter, obj, rel

	return (U, V, obj)


def calculate_obj(X, U, V, Ustar, alpha, trXTX):
	# for X with large dims
	VTV = V.T*V
	UTU = U.T*U
	UTX = U.T*X
	obj = alpha*norm(U-Ustar, 'fro') + sqrt(trXTX + trace(VTV*UTU) - 2*trace(UTX*V))
	return obj


def perViewNMF(X, U, V, Ustar, alpha, INNER_ITER, tol, VERBOSE):
	###
	## X -- nSam x nFea data matrix (dense for PL, PR, sparse for Fs, Fc)
	## U -- nSam x K cluster membership for samples (dense)
	## V -- nFea x K (dense)
	trXTX = sum((X.T*X).diagonal())
	Xpos, Xneg = getMatPos(X)

	if issparse(X):
		X_Fnorm = sqrt(sum(X.data)**2)
	else:
		X_Fnorm = sqrt(sum(square(X)))
	U, V, Q = normalizeUV(U, V, X_Fnorm)
	# U, V, Q = normalizeUV_noNorm(U, V)

	obj = calculate_obj(X, U, V, Ustar, alpha, trXTX)
	if VERBOSE:
		print '\tPerViewNMF START...'

	for iter in range(INNER_ITER):
		
		## Update U
		# multiply(A, B) means element-wise multiplication
		XposV = Xpos*V # n-by-K
		XnegV = Xneg*V # n-by-K
		UVTV = U*(V.T*V) # n-by-K
		U = multiply(U, (XposV+alpha*Ustar)/maximum(UVTV+XnegV+alpha*U, 1e-10))

		## Update V
		XposTU = Xpos.T*U # d-by-K
		XnegTU = Xneg.T*U # d-by-K
		UTU = U.T*U # k-by-k
		VUTU = V*UTU # d-by-K
		UstarTU = Ustar.T*U # k-by-k
		V_colSum = V.sum(axis=0)

		# for k in range(V.shape[1]):
		# 	tmp = (XposTU[:,k] + alpha*UstarTU[k,k])/maximum(VUTU[:,k]+XnegTU[:,k]+alpha*UTU[k,k]*V_colSum[0,k], 1e-10)
		# 	V[:,k] = multiply(V[:,k], tmp)

		tmp1 = XposTU + alpha*tile(UstarTU.diagonal(), (V.shape[0], 1))
		tmp2 = VUTU + XnegTU + alpha*multiply( tile(UTU.diagonal(),(V.shape[0],1)), tile(V_colSum[0,:],(V.shape[0],1)) )
		tmp2 = tmp1/maximum(tmp2, 1e-10)
		del tmp1
		V = multiply(V, tmp2)
		del tmp2

		## Normalize U, V
		## Q: Q_kk = (k-th col sum of V) / |X|_2, U = UQ, V = VQ^-1
		U, V, Q = normalizeUV(U, V, X_Fnorm)
		# U, V, Q = normalizeUV_noNorm(U, V)

		# calculate obj
		obj_old = obj
		obj = calculate_obj(X, U, V, Ustar, alpha, trXTX)
		rel = (obj_old - obj)/obj_old

		if iter % 20 == 0:
			if VERBOSE:
				print '\tinner loop:', iter, obj, rel

		if abs(rel) <= tol:
			if VERBOSE:
				print '\tConverges!', iter, obj, rel
			return (U, V, obj)

	if VERBOSE:
		print '\tReach MatIter', iter, obj, rel

	return (U, V, obj)



### single step of MultiNMF
def multiNMF_onestep(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, alpha, K, INNER_ITER, tol, VERBOSE):


	## update Ustar
	beta_sum = max(betaWL + betaWR + betaFs + betaFc, 1e-10)
	Ustar = multiply(betaWL, Ul)
	Ustar = (Ustar + multiply(betaWR, Ur) + multiply(betaFs, Us) + multiply(betaFc, Uc)) / beta_sum

	## update beta
	RE_sum = max(obj_WL + obj_WR + obj_Fs + obj_Fc, 1e-10)
	betaWL = -log(obj_WL/RE_sum)
	betaWR = -log(obj_WR/RE_sum)
	betaFs = -log(obj_Fs/RE_sum)
	betaFc = -log(obj_Fc/RE_sum)

	## update U and V for each view
	(Ul, Vl, obj_WL) = perViewNMF(PL, Ul, Vl, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView PL done, perViewNMF obj', obj_WL
	(Ur, Vr, obj_WR) = perViewNMF(PR, Ur, Vr, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView PR done, perViewNMF obj', obj_WR
	(Us, Vs, obj_Fs) = perViewNMF(F_string, Us, Vs, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView Fs done, perViewNMF obj', obj_Fs
	(Uc, Vc, obj_Fc) = perViewNMF(F_context, Uc, Vc, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView Fc done, perViewNMF obj', obj_Fc

	# calculate obj
	obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc

	return (Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, obj_multiNMF)


def clustype_inexact(S_L, S_R, S_M, PiC, PiL, PiR, F_context, F_string, Y0, lambda_O, gamma, mu, lambda_L, alpha, T, K, ITER, INNER_ITER, tol, Y_cand, C_cand, PL_cand, PR_cand, VERBOSE):
	PiLL = PiL.T*PiL
	PiRR = PiR.T*PiR

	### initialization #############################################################
	m = PiC.shape[0]
	n, l = S_L.shape
	ns = F_string.shape[1]
	nc = F_context.shape[1]

	C = C_cand
	PL = PL_cand
	PR = PR_cand

	Ul = abs(mat(random.rand(l, K)))
	Ur = abs(mat(random.rand(l, K)))
	Us = abs(mat(random.rand(l, K)))
	Uc = abs(mat(random.rand(l, K)))

	Vl = abs(mat(random.rand(T, K)))
	Vr = abs(mat(random.rand(T, K)))
	Vs = abs(mat(random.rand(ns, K)))
	Vc = abs(mat(random.rand(nc, K)))

	Ul = normalize_U(Ul)
	Vl = normalize_V(Vl)
	Ur = normalize_U(Ur)
	Vr = normalize_V(Vr)
	Us = normalize_U(Us)
	Vs = normalize_V(Vs)
	Uc = normalize_U(Uc)
	Vc = normalize_V(Vc)

	betaWL = 1.0 ## uniform weights
	betaWR = 1.0
	betaFs = 1.0
	betaFc = 1.0

	Y = Y_cand # Y = Y0.copy()
	Theta = PiC*C + PiL*PL + PiR*PR

	obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
	lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

	### Start algorithm #############################################################
	for i in range(ITER):

		lambda4 = 1+gamma+mu
		Y = 1/lambda4 * (gamma*S_M*Y + Theta + mu*Y0)

		C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*(Y-PiL*PL-PiR*PR) )
		PL = inverse_matrix((1+lambda_L*betaWL)*identity(PiL.shape[1]) + lambda_O*PiLL) * (S_L.T*C + lambda_O*PiL.T*(Y-PiC*C-PiR*PR) + lambda_L*betaWL*Ul*Vl.T)
		PR = inverse_matrix((1+lambda_L*betaWR)*identity(PiR.shape[1]) + lambda_O*PiRR) * (S_R.T*C + lambda_O*PiR.T*(Y-PiC*C-PiL*PL) + lambda_L*betaWR*Ur*Vr.T)

		if i == 0:
			print '\tNMF warn start...'
			(Ul, Vl, obj_WL) = NMF(PL, Ul, Vl, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview PL, NMF obj:', obj_WL
			(Ur, Vr, obj_WR) = NMF(PR, Ur, Vr, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview PR, NMF obj:', obj_WR
			(Us, Vs, obj_Fs) = NMF(F_string, Us, Vs, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview Fs, NMF obj:', obj_Fs
			(Uc, Vc, obj_Fc) = NMF(F_context, Uc, Vc, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview Fc, NMF obj:', obj_Fc
			obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
			obj += obj_multiNMF
			
			## normalize {Ur, Vr} and {Ul, Vl}
			if issparse(PL):
				X_Fnorm = sqrt(sum(PL.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PL)))
			Ul, Vl, _ = normalizeUV(Ul, Vl, X_Fnorm)

			if issparse(PR):
				X_Fnorm = sqrt(sum(PR.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PR)))
			Ur, Vr, _ = normalizeUV(Ur, Vr, X_Fnorm)

			###
			if issparse(F_string):
				X_Fnorm = sqrt(sum(F_string.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_string)))
			Us, Vs, _ = normalizeUV(Us, Vs, X_Fnorm)
			if issparse(F_context):
				X_Fnorm = sqrt(sum(F_context.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_context)))
			Uc, Vc, _ = normalizeUV(Uc, Vc, X_Fnorm)
			print '\twarm start DONE!'
			print 'ClusType-full-inexact', obj,  ', betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		(Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, obj_multiNMF) = \
		multiNMF_onestep(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, alpha, K, INNER_ITER, tol, VERBOSE)

		obj_old = obj
		Theta = PiC*C + PiL*PL + PiR*PR
		obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
		lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y)) + lambda_L*obj_multiNMF
		rel = (obj_old-obj)/obj_old
		if (i+1) % 1 == 0:
			print 'OutIter', i+1, 'DONE, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		if abs(rel) < tol:
			print 'OutIter Converges!!, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc
			Y = PiC*C + PiL*PL + PiR*PR
			return Y

	Y = PiC*C + PiL*PL + PiR*PR
	return Y




### fully-convergeded multi-view NMF
def multiNMF(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, Ustar, alpha, K, OUTER_ITER, INNER_ITER, tol, VERBOSE):

	obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
	for iter in range(OUTER_ITER):

		## update Ustar
		beta_sum = max(betaWL + betaWR + betaFs + betaFc, 1e-10)
		Ustar = multiply(betaWL, Ul)
		Ustar = (Ustar + multiply(betaWR, Ur) + multiply(betaFs, Us) + multiply(betaFc, Uc)) / beta_sum

		## update beta
		RE_sum = max(obj_WL + obj_WR + obj_Fs + obj_Fc, 1e-10)
		betaWL = -log(obj_WL/RE_sum)
		betaWR = -log(obj_WR/RE_sum)
		betaFs = -log(obj_Fs/RE_sum)
		betaFc = -log(obj_Fc/RE_sum)

		## update U and V for each view
		print '\tView PL...'
		(Ul, Vl, obj_WL) = perViewNMF(PL, Ul, Vl, Ustar, alpha, INNER_ITER, tol, VERBOSE)
		print '\tView PR...'
		(Ur, Vr, obj_WR) = perViewNMF(PR, Ur, Vr, Ustar, alpha, INNER_ITER, tol, VERBOSE)
		print '\tView Fs...'
		(Us, Vs, obj_Fs) = perViewNMF(F_string, Us, Vs, Ustar, alpha, INNER_ITER, tol, VERBOSE)
		print '\tView Fc...'
		(Uc, Vc, obj_Fc) = perViewNMF(F_context, Uc, Vc, Ustar, alpha, INNER_ITER, tol, VERBOSE)

		# calculate obj
		obj_multiNMF_old = obj_multiNMF
		obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
		rel = (obj_multiNMF_old - obj_multiNMF)/obj_multiNMF_old

		if iter % 5 == 0:
			print '  MultiNMF Outer', iter, obj_multiNMF, rel

		if abs(rel) < tol:
			print '  MultiNMF Outer Converges!', iter, obj_multiNMF, rel
			return (Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, Ustar, obj_multiNMF)

	print '  MultiNMF Outer Reach MaxIter!'
	return (Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, Ustar, obj_multiNMF)


def clustype_exact(S_L, S_R, S_M, PiC, PiL, PiR, F_context, F_string, Y0, lambda_O, gamma, mu, lambda_L, alpha, T, K, ITER, OUTER_ITER, INNER_ITER, tol, Y_cand, C_cand, PL_cand, PR_cand, VERBOSE):
	PiLL = PiL.T*PiL
	PiRR = PiR.T*PiR

	### initialization #############################################################
	m = PiC.shape[0]
	n, l = S_L.shape
	ns = F_string.shape[1]
	nc = F_context.shape[1]

	C = C_cand
	PL = PL_cand
	PR = PR_cand

	Ul = abs(mat(random.rand(l, K)))
	Ur = abs(mat(random.rand(l, K)))
	Us = abs(mat(random.rand(l, K)))
	Uc = abs(mat(random.rand(l, K)))

	Vl = abs(mat(random.rand(T, K)))
	Vr = abs(mat(random.rand(T, K)))
	Vs = abs(mat(random.rand(ns, K)))
	Vc = abs(mat(random.rand(nc, K)))

	betaWL = 1.0 ## uniform weights
	betaWR = 1.0
	betaFs = 1.0
	betaFc = 1.0

	Y = Y_cand # Y0.copy()
	Theta = PiC*C + PiL*PL + PiR*PR

	obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
	lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

	### Start algorithm #############################################################
	for i in range(ITER):

		### run clustype_noClus, till it converges
		Y, C, PL, PR = clustype_noClus_inner(S_L, S_R, S_M, PiC, PiL, PiR, Y0, lambda_O, gamma, mu, T, INNER_ITER, tol, C, PL, PR, Y)

		### run multiview NMF, till it converges
		if i == 0:
			(Ul, Vl, obj_WL) = NMF(PL, Ul, Vl, INNER_ITER, tol, VERBOSE)
			(Ur, Vr, obj_WR) = NMF(PR, Ur, Vr, INNER_ITER, tol, VERBOSE)
			(Us, Vs, obj_Fs) = NMF(F_string, Us, Vs, INNER_ITER, tol, VERBOSE)
			(Uc, Vc, obj_Fc) = NMF(F_context, Uc, Vc, INNER_ITER, tol, VERBOSE)
			obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
			obj += obj_multiNMF
			print '  NMF warm start DONE!'
			Ustar = Ul

		print '  start MultiNMF'
		(Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, Ustar, obj_multiNMF) = \
		multiNMF(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, Ustar, alpha, K, OUTER_ITER, INNER_ITER, tol, VERBOSE)
		
		### calculate obj
		obj_old = obj
		obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
		lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y)) + lambda_L*obj_multiNMF
		
		if (i+1) % 1 == 0:
			print 'OutIter', i+1, ', obj:', obj, ', rel_obj:', (obj_old-obj)/obj_old
			print '-- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

	Y = PiC*C + PiL*PL + PiR*PR

	return Y


### single step of MultiNMF
def multiNMF_onestep_fixBeta(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, alpha, K, INNER_ITER, tol, VERBOSE):


	## update Ustar
	beta_sum = max(betaWL + betaWR + betaFs + betaFc, 1e-10)
	Ustar = multiply(betaWL, Ul)
	Ustar = (Ustar + multiply(betaWR, Ur) + multiply(betaFs, Us) + multiply(betaFc, Uc)) / beta_sum

	## update U and V for each view
	(Ul, Vl, obj_WL) = perViewNMF(PL, Ul, Vl, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView PL done, perViewNMF obj', obj_WL
	(Ur, Vr, obj_WR) = perViewNMF(PR, Ur, Vr, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView PR done, perViewNMF obj', obj_WR
	(Us, Vs, obj_Fs) = perViewNMF(F_string, Us, Vs, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView Fs done, perViewNMF obj', obj_Fs
	(Uc, Vc, obj_Fc) = perViewNMF(F_context, Uc, Vc, Ustar, alpha, INNER_ITER, tol, VERBOSE)
	if VERBOSE:
		print '\tView Fc done, perViewNMF obj', obj_Fc

	# calculate obj
	obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc

	return (Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, obj_multiNMF)


def clustype_uniform(S_L, S_R, S_M, PiC, PiL, PiR, F_context, F_string, Y0, lambda_O, gamma, mu, lambda_L, alpha, T, K, ITER, INNER_ITER, tol, Y_cand, C_cand, PL_cand, PR_cand, VERBOSE):
	PiLL = PiL.T*PiL
	PiRR = PiR.T*PiR

	### initialization #############################################################
	m = PiC.shape[0]
	n, l = S_L.shape
	ns = F_string.shape[1]
	nc = F_context.shape[1]

	C = C_cand
	PL = PL_cand
	PR = PR_cand

	Ul = abs(mat(random.rand(l, K)))
	Ur = abs(mat(random.rand(l, K)))
	Us = abs(mat(random.rand(l, K)))
	Uc = abs(mat(random.rand(l, K)))

	Vl = abs(mat(random.rand(T, K)))
	Vr = abs(mat(random.rand(T, K)))
	Vs = abs(mat(random.rand(ns, K)))
	Vc = abs(mat(random.rand(nc, K)))

	Ul = normalize_U(Ul)
	Vl = normalize_V(Vl)
	Ur = normalize_U(Ur)
	Vr = normalize_V(Vr)
	Us = normalize_U(Us)
	Vs = normalize_V(Vs)
	Uc = normalize_U(Uc)
	Vc = normalize_V(Vc)

	betaWL = 1.0 ## uniform weights
	betaWR = 1.0
	betaFs = 1.0
	betaFc = 1.0

	Y = Y_cand # Y = Y0.copy()
	Theta = PiC*C + PiL*PL + PiR*PR

	obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
	lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

	### Start algorithm #############################################################
	for i in range(ITER):

		lambda4 = 1+gamma+mu
		Y = 1/lambda4 * (gamma*S_M*Y + Theta + mu*Y0)

		C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*(Y-PiL*PL-PiR*PR) )
		PL = inverse_matrix((1+lambda_L*betaWL)*identity(PiL.shape[1]) + lambda_O*PiLL) * (S_L.T*C + lambda_O*PiL.T*(Y-PiC*C-PiR*PR) + lambda_L*betaWL*Ul*Vl.T)
		PR = inverse_matrix((1+lambda_L*betaWR)*identity(PiR.shape[1]) + lambda_O*PiRR) * (S_R.T*C + lambda_O*PiR.T*(Y-PiC*C-PiL*PL) + lambda_L*betaWR*Ur*Vr.T)

		if i == 0:
			print '\tNMF warn start...'
			(Ul, Vl, obj_WL) = NMF(PL, Ul, Vl, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview PL, NMF obj:', obj_WL
			(Ur, Vr, obj_WR) = NMF(PR, Ur, Vr, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview PR, NMF obj:', obj_WR
			(Us, Vs, obj_Fs) = NMF(F_string, Us, Vs, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview Fs, NMF obj:', obj_Fs
			(Uc, Vc, obj_Fc) = NMF(F_context, Uc, Vc, INNER_ITER, tol, VERBOSE)
			if VERBOSE:
				print '\tview Fc, NMF obj:', obj_Fc
			obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
			obj += obj_multiNMF
			
			## normalize {Ur, Vr} and {Ul, Vl}
			if issparse(PL):
				X_Fnorm = sqrt(sum(PL.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PL)))
			Ul, Vl, _ = normalizeUV(Ul, Vl, X_Fnorm)

			if issparse(PR):
				X_Fnorm = sqrt(sum(PR.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PR)))
			Ur, Vr, _ = normalizeUV(Ur, Vr, X_Fnorm)

			###
			if issparse(F_string):
				X_Fnorm = sqrt(sum(F_string.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_string)))
			Us, Vs, _ = normalizeUV(Us, Vs, X_Fnorm)
			if issparse(F_context):
				X_Fnorm = sqrt(sum(F_context.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_context)))
			Uc, Vc, _ = normalizeUV(Uc, Vc, X_Fnorm)
			print '\twarm start DONE!'
			print 'ClusType-full-inexact', obj,  ', betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		(Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, obj_multiNMF) = \
		multiNMF_onestep_fixBeta(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, alpha, K, INNER_ITER, tol, VERBOSE)

		obj_old = obj
		Theta = PiC*C + PiL*PL + PiR*PR
		obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
		lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y)) + lambda_L*obj_multiNMF
		rel = (obj_old-obj)/obj_old
		if (i+1) % 1 == 0:
			print 'OutIter', i+1, 'DONE, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		if abs(rel) < tol:
			print 'OutIter Converges!!, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc
			Y = PiC*C + PiL*PL + PiR*PR
			return Y

	Y = PiC*C + PiL*PL + PiR*PR
	return Y




def clustype_noFsFc(S_L, S_R, S_M, PiC, PiL, PiR, F_context, F_string, Y0, lambda_O, gamma, mu, lambda_L, alpha, T, K, ITER, INNER_ITER, tol, Y_cand, C_cand, PL_cand, PR_cand, VERBOSE):
	PiLL = PiL.T*PiL
	PiRR = PiR.T*PiR

	### initialization #############################################################
	m = PiC.shape[0]
	n, l = S_L.shape
	ns = F_string.shape[1]
	nc = F_context.shape[1]

	C = C_cand
	PL = PL_cand
	PR = PR_cand

	Ul = abs(mat(random.rand(l, K)))
	Ur = abs(mat(random.rand(l, K)))
	Us = abs(mat(random.rand(l, K)))
	Uc = abs(mat(random.rand(l, K)))

	Vl = abs(mat(random.rand(T, K)))
	Vr = abs(mat(random.rand(T, K)))
	Vs = abs(mat(random.rand(ns, K)))
	Vc = abs(mat(random.rand(nc, K)))

	Ul = normalize_U(Ul)
	Vl = normalize_V(Vl)
	Ur = normalize_U(Ur)
	Vr = normalize_V(Vr)
	Us = normalize_U(Us)
	Vs = normalize_V(Vs)
	Uc = normalize_U(Uc)
	Vc = normalize_V(Vc)

	betaWL = 1.0 ## uniform weights
	betaWR = 1.0
	betaFs = 0.0
	betaFc = 0.0

	Y = Y_cand # Y = Y0.copy()
	Theta = PiC*C + PiL*PL + PiR*PR

	obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
	lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y))

	### Start algorithm #############################################################
	for i in range(ITER):

		lambda4 = 1+gamma+mu
		Y = 1/lambda4 * (gamma*S_M*Y + Theta + mu*Y0)

		C = 1/(2+lambda_O) * ( S_L*PL + S_R*PR + lambda_O*PiC.T*(Y-PiL*PL-PiR*PR) )
		PL = inverse_matrix((1+lambda_L*betaWL)*identity(PiL.shape[1]) + lambda_O*PiLL) * (S_L.T*C + lambda_O*PiL.T*(Y-PiC*C-PiR*PR) + lambda_L*betaWL*Ul*Vl.T)
		PR = inverse_matrix((1+lambda_L*betaWR)*identity(PiR.shape[1]) + lambda_O*PiRR) * (S_R.T*C + lambda_O*PiR.T*(Y-PiC*C-PiL*PL) + lambda_L*betaWR*Ur*Vr.T)

		if i == 0:
			print '\tNMF warn start...'
			(Ul, Vl, obj_WL) = NMF(PL, Ul, Vl, INNER_ITER, tol, VERBOSE)
			print '\tview PL, NMF obj:', obj_WL
			(Ur, Vr, obj_WR) = NMF(PR, Ur, Vr, INNER_ITER, tol, VERBOSE)
			print '\tview PR, NMF obj:', obj_WR
			(Us, Vs, obj_Fs) = NMF(F_string, Us, Vs, INNER_ITER, tol, VERBOSE)
			print '\tview Fs, NMF obj:', obj_Fs
			(Uc, Vc, obj_Fc) = NMF(F_context, Uc, Vc, INNER_ITER, tol, VERBOSE)
			print '\tview Fc, NMF obj:', obj_Fc
			obj_multiNMF = betaWL*obj_WL + betaWR*obj_WR + betaFs*obj_Fs + betaFc*obj_Fc
			obj += obj_multiNMF
			
			## normalize {Ur, Vr} and {Ul, Vl}
			if issparse(PL):
				X_Fnorm = sqrt(sum(PL.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PL)))
			Ul, Vl, _ = normalizeUV(Ul, Vl, X_Fnorm)

			if issparse(PR):
				X_Fnorm = sqrt(sum(PR.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(PR)))
			Ur, Vr, _ = normalizeUV(Ur, Vr, X_Fnorm)

			###
			if issparse(F_string):
				X_Fnorm = sqrt(sum(F_string.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_string)))
			Us, Vs, _ = normalizeUV(Us, Vs, X_Fnorm)
			if issparse(F_context):
				X_Fnorm = sqrt(sum(F_context.data)**2)
			else:
				X_Fnorm = sqrt(sum(square(F_context)))
			Uc, Vc, _ = normalizeUV(Uc, Vc, X_Fnorm)
			print '\twarm start DONE!'
			print 'ClusType-full-inexact', obj,  ', betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		(Ul, Vl, betaWL, obj_WL, Ur, Vr, betaWR, obj_WR, Us, Vs, betaFs, obj_Fs, Uc, Vc, betaFc, obj_Fc, obj_multiNMF) = \
		multiNMF_onestep_fixBeta(PL, Ul, Vl, betaWL, obj_WL, PR, Ur, Vr, betaWR, obj_WR, \
			F_string, Us, Vs, betaFs, obj_Fs, F_context, Uc, Vc, betaFc, obj_Fc, alpha, K, INNER_ITER, tol, VERBOSE)

		obj_old = obj
		Theta = PiC*C + PiL*PL + PiR*PR
		obj = trace(2*C.T*C + PL.T*PL + PR.T*PR - 2*C.T*S_L*PL - 2*C.T*S_R*PR) + \
		lambda_O * (norm(Y-Theta,ord='fro')**2 + mu*norm(Y-Y0,ord='fro')**2 + gamma*trace(Y.T*Y-Y.T*S_M*Y)) + lambda_L*obj_multiNMF
		rel = (obj_old-obj)/obj_old
		if (i+1) % 1 == 0:
			print 'OutIter', i+1, 'DONE, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc

		if abs(rel) < tol:
			print 'OutIter Converges!!, obj:', obj, ', rel_obj:', rel
			print ' -- betaWL', betaWL, ', betaWR', betaWR, ', betaFs', betaFs, ', betaFc', betaFc
			Y = PiC*C + PiL*PL + PiR*PR
			return Y

	Y = PiC*C + PiL*PL + PiR*PR
	return Y

