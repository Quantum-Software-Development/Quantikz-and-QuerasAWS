#!/usr/bin/env python3
""" 
 concatenate mutiple measurements from Quera
"""

__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"

import numpy as np
import  time
import sys,os
from pprint import pprint
from toolbox.Util_H5io4 import  write4_data_hdf5, read4_data_hdf5
from toolbox.PlotterBackbone import PlotterBackbone

import argparse

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbosity",type=int,choices=[0, 1, 2],help="increase output verbosity", default=1, dest='verb')

    parser.add_argument("-o", "--outPath", default='out/',help="output path for plots and tables")

    parser.add_argument( "-X","--noXterm", dest='noXterm',  action='store_true', default=False, help="disable X-term for batch mode")
    parser.add_argument("-p", "--showPlots",  default='ab', nargs='+',help="abc-string listing shown plots")


    args = parser.parse_args()
    args.showPlots=''.join(args.showPlots)
    for arg in vars(args):  print( 'myArg:',arg, getattr(args, arg))
    return args

#............................
#............................
#............................
class Plotter(PlotterBackbone):
    def __init__(self, args):
        PlotterBackbone.__init__(self,args)

    #...!...!....................
    def bell4states(self,md,bigD,figId=1,ax=None,tit=None):
        if ax==None:
            nrow,ncol=1,1       
            figId=self.smart_append(figId)
            fig=self.plt.figure(figId,facecolor='white', figsize=(6,4))
            ax = self.plt.subplot(nrow,ncol,1)

        timeV=bigD["evolTime"]        
        probsSum=bigD["probsSum"]
        nTime=timeV.shape[0]

        if tit==None:
            tit='Bell states evolution, job=%s  m:%d'%(md['short_name'],nTime)

        dMkL=['o','D','^','s','*','+','x','>','1']
        stateLab=['gg','gr','rg','rr']
        mCol=['b','r','y','g']
        nSt=probsSum.shape[-1]
        
        for k in range(nSt):
            Y=probsSum[0,:,k]
            erY=probsSum[1,:,k]
            dLab=stateLab[k]
            dMk=dMkL[k]
            dC=mCol[k]
            #print('state %d probs:'%k,Y,erY)
            ax.errorbar(timeV, Y,yerr=erY,label=dLab,marker=dMk,color=dC,alpha=0.7,ms=4,lw=1.0)
                    
       
        ax.legend(title="state", loc='upper right') # center upper 
        ax.set(xlabel='evolution time (us)',ylabel='probability',title=tit)
        ax.grid()
        ax.set_ylim(-0.05,1.05)
        # ax.set_xlim(0.,)
        #ax.set_xlim(2.1,2.6)  # Bell-state zoom
        #ax.set_xlim(1.5,3.1)  # Bell-state wide
        #ax.set_xlim(1.6,2.1)  # equal superposition
        ax.set_xlim(0.3,1.3)  # equal superposition
        ax.axhline(0.5,color='k',ls='--')
        ax.axhline(0.25,color='k',ls='--')

        #.... mis text
        txt1='device: '+md['submit']['backend']
        txt1+='\nexec: %s'%md['job_qa']['exec_date']
        txt1+='\ndist %s um'%(md['payload']['atom_dist_um'])
        txt1+='\nOmaga %.1f MHz'%md['payload']['rabi_omega_MHz']
        txt1+='\nshots/job: %d'%md['submit']['num_shots']
        txt1+='\ntot atoms: %d'%md['payload']['tot_num_atom']
        txt1+='\nnum jobs: %d'%nTime
        ax.text(0.02,0.6,txt1,transform=ax.transAxes,color='g')

        return
    
   
            #break

#...!...!....................
def locateSummaryData(src_dir,pattern=None,verb=1):

    for xx in [ src_dir]:
        if os.path.exists(xx): continue
        print('Aborting on start, missing  dir:',xx)
        exit(1)

    if verb>0: print('locate summary data src_dir:',src_dir,'pattern:',pattern)

    jobL=os.listdir(src_dir)
    print('locateSummaryData got %d potential jobs, e.g.:'%len(jobL), jobL[0])
    print('sub-dirs',jobL)

    sumL=[]
    for sumF in jobL:
        if '.h5' not in sumF: continue
        if pattern not in sumF: continue
        sumL.append(sumF)
        
    if verb>0: print('found %d sum-files'%len(sumL))
    return sorted(sumL)

#=================================
#=================================
#  M A I N 
#=================================
#=================================
if __name__ == '__main__':
    args=get_parser()
   
    #anaPath='/dataVault/dataQuEra_2023juneBellC_qpu/ana'; device='qpu'  # T=[1.9,2.5]
    anaPath='/dataVault/dataQuEra_2023juneBellB_qpu/ana'; device='qpu'  # T=[0.3,1.1]
    sumFL=locateSummaryData( anaPath,pattern='bell_'+device)
    assert len(sumFL) >0
    evolTime=[]
    probsC=[]  # per clust
    probsS=[]  # sum over all clust
    for i,inpF in enumerate(sumFL):        
        expD,expMD=read4_data_hdf5(os.path.join(anaPath,inpF),verb=i==0)
        if i==0: pprint(expMD)
        evolTime.append(float(expMD['payload']['evol_time_us']))
        probsC.append(expD['prob_clust'])
        probsS.append(expD['prob_sum'])

    # convert to numpy
    probsC=np.array(probsC) # shape[ nTime, PAY, clust, NB]
    probsS=np.array(probsS)  # shape[ nTime, PAY,  NB]

    #print('CC',probsC.shape)
    print('SS',probsS.shape)
    bigD={}
    bigD["evolTime"]=np.array(evolTime)
    bigD["probsClust"]=np.swapaxes(probsC,0,1)
    bigD["probsSum"]=np.swapaxes(probsS,0,1)[:,:,0]  # shape[ PAY, nTime,  NB]
    print('M: evolTime/us:',evolTime, bigD["probsClust"].shape, bigD["probsSum"].shape)
    
        
    # ----  just plotting
    args.prjName=expMD['short_name']+'m%d'%expMD['payload']['tot_num_atom']
    plot=Plotter(args)
    if 'a' in args.showPlots:
        plot.bell4states(expMD,bigD,figId=1)
    plot.display_all(png=1)
    

