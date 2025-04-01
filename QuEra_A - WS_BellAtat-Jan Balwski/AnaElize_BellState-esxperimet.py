#!/usr/bin/env python3
__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"

'''
Analyze   ProblemBellState  experiment
Graphics optional
'''

import os
from pprint import pprint
import numpy as np
import json 

from toolbox.Util_H5io4 import  write4_data_hdf5, read4_data_hdf5
from toolbox.Util_H5io4 import  write4_data_hdf5, read4_data_hdf5
from toolbox.PlotterBackbone import PlotterBackbone

from ProblemBellState import ProblemBellState

import argparse
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbosity",type=int,choices=[0, 1, 2, 3,4],  help="increase output verbosity", default=1, dest='verb')
         
    parser.add_argument("--basePath",default='env',help="head dir for set of experiments, or env--> $QuEra_dataVault")

    parser.add_argument('-e',"--expName",  default='exp_62a15b',help='AWS-QuEra experiment name assigned during submission')

    # plotting
    parser.add_argument("-p", "--showPlots",  default='ab', nargs='+',help="abc-string listing shown plots")
    parser.add_argument( "-X","--noXterm", dest='noXterm',  action='store_true', default=False, help="disable X-term for batch mode")

    args = parser.parse_args()
    # make arguments  more flexible
    if 'env'==args.basePath: args.basePath= os.environ['QuEra_dataVault']
    args.dataPath=os.path.join(args.basePath,'meas')
    args.outPath=os.path.join(args.basePath,'ana')
    args.showPlots=''.join(args.showPlots)
    
    print( 'myArg-program:',parser.prog)
    for arg in vars(args):  print( 'myArg:',arg, getattr(args, arg))
    
    assert os.path.exists(args.dataPath)
    assert os.path.exists(args.outPath)
    return args


#............................
#............................
#............................
class Plotter(PlotterBackbone):
    def __init__(self, args):
        PlotterBackbone.__init__(self,args)

    #...!...!....................
    def show_register(self,md,figId=1,
                      blockade_radius: float=None,
                      what_to_draw: str="bond",
                      show_atom_index:bool=True):
        """Plot the given register extracted from meta-data

        Args:
            blockade_radius (float): None=use md,  The blockade radius for the register.
        what_to_draw (str): Default is "bond". Either "bond" or "circle" to indicate the blockade region. 
            show_atom_index (bool): Default is True. Choose if each atom's index is displayed over the atom itself in the resulting figure. 
           
        """

        figId=self.smart_append(figId)
        nrow,ncol=1,1

        fig=self.plt.figure(figId,facecolor='white', figsize=(6,5))
        ax = self.plt.subplot(nrow,ncol,1)
        
        um=1e-6 # conversion from m to um
        progD=json.loads( expD['program_org.JSON'][0])
        registerD=progD['setup']['ahs_register']

        # ......  Aquila FOV ......
        fov=md['payload']['aquila_area']
        fovX= float(fov['width'])/um
        fovY= float(fov['height'])/um
        nominal_Rb= md['payload']['nominal_Rb_um']

        ax.grid(ls=':')
        ax.set_aspect(1.)
        mm=10
        ax.set_xlim(-mm,fovX+10);        ax.set_ylim(-mm,fovY+10)        
        ax.add_patch( self.plt.Rectangle([0,0],fovX,fovY, color="g", alpha=0.3, fc="none", ls='--') )

        ax.plot([fovX,fovX+3],[fovY,fovY+3],color='g',ls='--')
        ax.text(fovX+3,fovY+3,'FOV',color='g',va='bottom')
        
        tit='BellState job=%s'%(md['short_name'])
        ax.set(xlabel='X position (um)',ylabel='Y position (um)',title=tit)

        #.... misc text
        txt1='back: '+md['submit']['backend']
        txt1+=', tot atoms: %d'%md['payload']['tot_num_atom']
        txt1+=', omega: %.2f MHz'%md['payload']['rabi_omega_MHz']
        txt1+=', Rb: %.1f um'%nominal_Rb
        ax.text(0.0,fovY+7,txt1,color='g')
        
        # ....  Atoms  ............
        atoms=[ ]; voids=[]
        for [cx,cy],f in zip( registerD['sites'], registerD['filling']):
            xy=[float(cx)/um,float(cy)/um]
            if f:
                atoms.append(xy )
            else:
                voids.append( xy)
                
        atoms=np.array(atoms)
        voids=np.array(voids)
        #print('atoms:',atoms,atoms.size)

        if atoms.size>0: # filled_sites
            ax.plot(atoms[:,0], atoms[:,1], 'r.', ms=15, label='filled')
        if voids.size>0: # empty_sites
            ax.plot(voids[:,0], voids[:,1],  'k.', ms=5, label='empty')

        
        nA=atoms.shape[0]
    
        if what_to_draw=="circle":
            for i in range(nA):
                x,y=atoms[i]
                #  Rb radii
                ax.add_patch( self.plt.Circle((x,y), nominal_Rb/2, color="b", alpha=0.3) )
                ax.add_patch( self.plt.Circle((x,y), nominal_Rb, color="b", alpha=0.1) )
                ax.add_patch( self.plt.Circle((x,y), nominal_Rb*2, color="b", alpha=0.03) )
                # add label atoms
                ax.text(x+0.5,y+1,'%d'%i,color='k',va='center')

        if what_to_draw=="bond":            
            for i in range(nA):
                for j in range(i+1, nA):
                    A=atoms[i]; B=atoms[j]
                    dist = np.linalg.norm(A-B)
                    if dist > nominal_Rb: continue
                    ax.plot([A[0],B[0]], [A[1],B[1]], 'b')
                    
        return atoms, ax
    
    #...!...!....................
    def counts(self,ax,atoms,md,expD):
        counts=expD['counts_clust']
        shots=md['submit']['num_shots']
        pd=md['payload']
        nClust=pd['num_clust']
        nAtom= pd['atom_in_clust']
        fov=pd['aquila_area']
        um=1e-6 # conversion from m to um
        fovX= float(fov['width'])/um
        fovY= float(fov['height'])/um
        #print('cnt',counts)
        
        for j in range(nClust):
            ngg,ngr,nrg,nrr=counts[j]
            #print(j,ng,nr)
            ne=shots-ngg-ngr-nrg-nrr
            txt='%d:%d:%d:%d'%(ngg,ngr,nrg,nrr)             
            if ne>0: txt+=' e%d'%ne
            x,y=atoms[j*nAtom]  # pick atom to print counts
            _,y2=atoms[j*nAtom+1]
            y=(y+y2)/2# um, move up a bit
            #print(j,x,y,txt)
            ax.text(x-8,y,txt,color='b',va='center')
        txt1='shots: %d'%shots
        txt1+=', exec:'+md['job_qa']['exec_date']
        ax.text(0.02,fovY+3.5,txt1,color='b')

        rgSL=md['analyzis']['rg_states_list']
        txt1='counts\n %s (e)'%':'.join(rgSL)
        ax.text(fovX-10,fovY-8,txt1,color='b')

#=================================
#=================================
#  M A I N 
#=================================
#=================================
if __name__=="__main__":
    args=get_parser()
    np.set_printoptions(precision=2)
                    
    inpF=args.expName+'.h5'
    expD,expMD=read4_data_hdf5(os.path.join(args.dataPath,inpF))

    if 0: # patch June1 data
        from decimal import Decimal
        expMD['payload']['evol_time_ramp_us']=Decimal('0.1') 

        
    if args.verb>=2:
        print('M:expMD:');  pprint(expMD)
        if args.verb>=3:
            for x in  expD:
                if 'qasm3' in x : continue
                print(x,expD[x])
  
        stop3

        
    task= ProblemBellState(args,expMD,expD)

    task.analyzeExperiment()
    
    #...... WRITE  OUTPUT
    outF=os.path.join(args.outPath,expMD['short_name']+'.ags.h5')
    write4_data_hdf5(task.expD,outF,expMD)

    # ----  just plotting
    args.prjName=expMD['short_name']
    plot=Plotter(args)
    
    if 'a' in args.showPlots:
        plot.show_register(expMD, what_to_draw="circle",figId=1)
    if 'b' in args.showPlots:
        atoms_um,ax=plot.show_register(expMD, what_to_draw="bond",figId=2)
        plot.counts(ax,atoms_um,expMD,expD)
    plot.display_all(png=1)

    print('M:done')


