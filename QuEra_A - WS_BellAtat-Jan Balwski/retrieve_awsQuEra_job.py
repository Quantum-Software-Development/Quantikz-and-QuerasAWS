#!/usr/bin/env python3
__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"

'''

 xx.result()
measD=get_counters_from_result(result)
    pprint(measD)
    pprint(result.task_metadata)


 Retrieve  results of IBMQ job

Required INPUT:
    --expName: exp_j33ab44

Output:  raw  yields + meta data
'''

import time,os,sys
from pprint import pprint
import numpy as np
from toolbox.Util_H5io4 import  read4_data_hdf5, write4_data_hdf5
from toolbox.UAwsQuEra_job import  access_quera_device

import argparse
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verb",type=int, help="increase output verbosity", default=1)
    parser.add_argument("--basePath",default='env',help="head dir for set of experiments, or env--> $QuEra_dataVault")
    parser.add_argument('-e',"--expName",  default='exp_62a15b',help='AWS-QuEra experiment name assigned during submission')       

    args = parser.parse_args()
    if 'env'==args.basePath: args.basePath= os.environ['QuEra_dataVault']
   
    args.inpPath=os.path.join(args.basePath,'jobs')
    args.outPath=os.path.join(args.basePath,'meas')
    
    for arg in vars(args):  print( 'myArg:',arg, getattr(args, arg))
    return args


#=================================
#=================================
#  M A I N
#=================================
#=================================
if __name__ == "__main__":
    args=get_parser()

    inpF=args.expName+'.quera.h5'
    expD,jobMD=read4_data_hdf5(os.path.join(args.inpPath,inpF),verb=args.verb)
     
    if args.verb>1: pprint(jobMD)

    # select Problem-class:
    if 'ProblemAtomGridSystem'==jobMD['payload']['class_name']:
        from ProblemAtomGridSystem import ProblemAtomGridSystem
        task=ProblemAtomGridSystem(args,jobMD,expD)

    if 'ProblemBellState'==jobMD['payload']['class_name']:
        from ProblemBellState import ProblemBellState
        task=ProblemBellState(args,jobMD,expD)

    task.retrieve_job() 
   
    if args.verb>2: pprint(expMD)
    #...... WRITE  OUTPUT .........
    outF=os.path.join(args.outPath,jobMD['short_name']+'.h5')
    write4_data_hdf5(expD,outF,jobMD)

    #..........  helper analysis  programs
    anaCode= jobMD['analyzis']['ana_code']
    baseStr= " --basePath %s "%args.basePath if 'env'!=args.basePath  else ""
    print('\n   ./%s %s --expName   %s   -X \n'%(anaCode,baseStr,jobMD['short_name']))
 
    
       


