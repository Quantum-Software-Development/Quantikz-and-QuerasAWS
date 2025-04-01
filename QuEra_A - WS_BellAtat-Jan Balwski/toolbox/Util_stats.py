__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"


import numpy as np
from pprint import pprint


#...!...!....................
def do_yield_stats(dataY): # vectorized version
    '''
    WARNING: this code works for M>1 qubits measurement 
    INPUT:  yield[Nxy...,NB], where
         NB: number of N-qubit bit-strings
         NX,NY: user defined (preserved) dimensions

    OUTPUT: prob[PEY,Nxy...,NB] , where
         PEY=3 for: prob, probErr, yield
    '''

    # assumes input np array [...,NY,NX,NB] with last index 'NB' enumarating all possible bit-strings. E.g. for 2 qubit --> NB=2^2=4

    # short: variance of nj-base yield given Ns-shots: var nj = Ns*var <xj> = nj*(Ns-nj)/(Ns-1).
    
    ''' Steve V: The way I think about this problem is that you have a total of Ns trials.  On any one trial, the probability of the throw ending up in state j is 1 or 0.  The mean probability <xj> of ending up in state j, over Ns tries, is nj/Ns and the uncertainty in that mean probability is given by

var <xj> = Sum(xj-<xj>)^2/[Ns(Ns-1)] = [nj(1-<xj>)^2 + (Ns-nj)<xj>^2]/[Ns(Ns-1)]

This reduces to:

var nj = Ns*var <xj> = nj*(Ns-nj)/(Ns-1).

I think this works for any number of substates and any large number of trials.
note: var_nj fixed 2023-05
    '''
    
    assert dataY.ndim>=1  # works for arbitrary data dimensionality, just the bit-strings index must be the last one 
    NB=dataY.shape[-1]  # number of bit strings
    shots=np.sum(dataY,axis=-1)
    #print('DYS: dataY:',dataY.shape, dataY)
    
    # count empty labels
    nZero=np.sum(shots<=0)
    if nZero>0:
        print('\ndo_yield_stats:WARN, %d measurements have 0 shots ?!?, assume 1\n'%nZero)
    shots=np.clip(shots,1,None)  # assume std of yield==0 is 1
    
    #print('Steve:shots',shots.shape)
    shotsY=np.stack([shots]*NB,axis=-1)
    prob=dataY/shotsY
    noZeros=np.all(prob)
    #print('Steve:prob',prob.shape,', no zeros:',noZeros)  # can be false
    #print('prob-dump:',prob)
    
    nBelow0=np.sum(prob<0.)
    nAbove1=np.sum(prob>1.)
    print('Steve: nBelow0=%d nAbove1=%d'%(nBelow0,nAbove1))
    # NOT DO THAT :prob=np.clip(prob,0.,1.)   # to enforce probaility range
    # w/o clip the number of shots are preserved.
    
    # assume # of shots >>1, and for variance skip the '-1' in: 1/(shots-1)
            
    #math: var_nj=dataY * ( shotsY-dataY) / shotsY
    #      probErr1=np.sqrt(var_nj)/ shotsY
    # more computationally efficient 
    rvar_nj=prob*(1-prob)/shotsY  # relative variance, divided by shots
    zIdx=rvar_nj==0.
    #print('zIdx=',zIdx,'\n rvar_nj:',rvar_nj)
    rvar_nj[zIdx ]=1/(shotsY[zIdx]**2)  # this is a strange line - but it works
    #print('Steve:var no zeros:',np.all(rvar_nj))
    #print('end rvar_nj:',rvar_nj)
    probErr=np.sqrt(rvar_nj)
        
    print('Steve:err no zeros:',np.all(probErr))  # never can be false
    dataProb=np.stack( [prob,probErr,dataY], axis=0 ).astype('float32')
    return dataProb
    #where:  PEY=3 for: prob, probErr, yield


#...!...!..................
def prob_to_pauliExpectedValue(dataP):
    print('P2PEV:',dataP.shape)
    prob=dataP[0]
    probEr=dataP[1]
    dataEV=np.copy(dataP)  # keep yields and varYields as-is
    #dataEV[0]= 2*prob -1.  # wrong, fixed on 2022-02-11
    dataEV[0]= 1.-2*prob  #good
    dataEV[1]=2*probEr
    return dataEV

