__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"

from pprint import pprint
import time
import os, hashlib
from braket.aws.aws_quantum_task import AwsQuantumTask
import json # tmp for raw data storing
import numpy as np
import pytz
from datetime import datetime


#...!...!..................
def submit_args_parser(backName,parser=None):
    if parser==None:  parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verb",type=int, help="increase debug verbosity", default=1)
    parser.add_argument("--basePath",default='env',help="head dir for set of experiments, or env--> $QuEra_dataVault")
    parser.add_argument("--expName",  default=None,help='(optional) replaces IBMQ jobID assigned during submission by users choice')
        
    # Braket:
    parser.add_argument('-b','--backendName',default=backName,choices=['cpu','emulator','qpu','aquila'],help="backend for computations " )

    parser.add_argument('-n','--numShots', default=23, type=int, help='num of shots')
    parser.add_argument('--evol_time_us', default='1.2', type=str, help='Hamiltonian evolution time, in usec')
    parser.add_argument( "-E","--executeTask", action='store_true', default=False, help="may take long time, test before use ")
     
    parser.add_argument( "-C","--cancelTask", action='store_true', default=False, help="instant task cancelation, usefull for debugging of the code")
        
    args = parser.parse_args()
    if 'env'==args.basePath: args.basePath= os.environ['QuEra_dataVault']
    args.outPath=os.path.join(args.basePath,'jobs')
        
    if args.backendName=='cpu':  args.backendName='emulator'
    if args.backendName=='qpu':  args.backendName='aquila'
    
    for arg in vars(args):
        print( 'myArgs:',arg, getattr(args, arg))

    assert os.path.exists(args.outPath)
    return args

#...!...!....................
def access_quera_device( backName,verb=1):
    if backName=='emulator':
         from braket.devices import LocalSimulator
         device = LocalSimulator("braket_ahs")
    if backName=='aquila':
        from braket.aws import AwsDevice
        device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/quera/Aquila")
        
    return device
   

#...!...!.................... 
def harvest_submitInfo(job,md,taskName='exp'):
    sd=md['submit']
  
    jobMD=job.metadata()
    if jobMD!=None:   # real HW
        sd['task_arn']=job.id
        for x in [ 'deviceArn', 'status']:
            sd[x]=jobMD[x]
        x='createdAt'
        sd[x]=str(jobMD[x])
    else:  # emulator
        sd['task_arn']='quantum-task/emulator-'+hashlib.md5(os.urandom(32)).hexdigest()[:6]
        sd['deviceArn']='local-emulator'    
     
    t1=time.localtime()
    sd['date']=dateT2Str(t1)
    sd['unix_time']=int(time.time())
    
    if md['short_name']==None :
        # the  6 chars in job id , as handy job identiffier
        md['hash']=sd['task_arn'].replace('-','')[-6:] # those are still visible on the IBMQ-web
        name=taskName+'_'+md['hash']
        md['short_name']=name
    else:  # name provided or emulator
        myHN=hashlib.md5(os.urandom(32)).hexdigest()[:6]
        md['hash']=myHN

                
#...!...!.................... 
def harvest_retrievInfo(jobMD,md):
    # collect job performance info    
    qaD={}
    qaD['success']=True
    if jobMD==None:  # emulator
        qaD['status']='COMPLETED'
        t1=time.localtime()
        qaD['exec_date']=dateT2Str(t1)
    else:
        qaD['status']=jobMD['status']
        qaD['endedAt']=str(jobMD['endedAt'])
        assert md['submit']['task_arn'] == jobMD['quantumTaskArn'], 'messed up job ID'
        #1print('aa1',md['submit']['task_arn'])
        #1print('aa2',jobMD['quantumTaskArn']) #; pprint(jobMD)
        
        xS=qaD['endedAt']
        tOb = datetime.fromisoformat(xS)
        #print('tOb',tOb)
        #tS=tOb.strftime("%Y%m%d_%H%M%S_%Z")
        #print('tS UTC',tS)
    
        # Convert the datetime object to the Pacific Daylight Time (PDT) timezone
        pdt_timezone = pytz.timezone('US/Pacific')
        tOb2 = tOb.astimezone(pdt_timezone)
        tS2=tOb2.strftime("%Y%m%d_%H%M%S_%Z")
        
        qaD['exec_date']=tS2
        
    print('job QA',qaD, 'backend=',md['submit']['backend'])
    md['job_qa']=qaD



#...!...!....................
def retrieve_aws_job( task_arn, verb=1):  # AWS-QuEra job retrieval
    #print('\nretrieve_job search for ARN',task_arn)

    job=None
    try:
        job = AwsQuantumTask(arn=task_arn, poll_timeout_seconds=30)
    except:
        print('job NOT found, quit\n ARN=',task_arn)
        exit(99)

    print('job IS found, state=%s, %s  retriving ...'%(job.state(),task_arn))    
    startT = time.time()
    
    while job.state()!='COMPLETED':        
        if job.state() in ['CANCELLING', 'CANCELLED', 'FAILED']:
            print('retrieval ABORTED for ARN:%s\n'%task_arn)
            exit(0)

        print('State  %s,    mytime =%d, wait ... ' %(job.state(),time.time()-startT))
        time.sleep(30)
        
    print('final job status:',job.state())
        
    return  job 


"""Aggregate state counts from AHS shot results.

        Returns:
            Dict[str, int]: number of times each state configuration is measured.
            Returns None if none of shot measurements are successful.
            Only succesful shots contribute to the state count.

        Notes: We use the following convention to denote the state of an atom (site):
            e: empty site
            r: Rydberg state atom
            g: ground state atom
"""

#...!...!..................
def postprocess_job_results(rawCounts,md,expD,backend=None):
    # for now just save Dict[str, int] as JSON    
    expD['counts_raw.JSON']=json.dumps(rawCounts)


#...!...!..................
def compute_nominal_rb(Omega, Delta):  # both in rad/usec
    # Compute the Rydberg blockade radius #
    C6 = 2*np.pi* 862690 
    return (C6 / np.sqrt((2*Omega)**2 + Delta**2))**(1/6)

from decimal import Decimal
#...!...!..................
def dictTransform_decimal(X,toString=True):
    print('\n\n===================================\n')
    print('start dictTransform_decimal2string().keys:',X.keys())

    def dec2str(v): return  'Decimal:'+str(v)

    D=X['payload']['program']['hamiltonian']['drivingFields']
    pprint(D)
    for K in D:
        wave=K.pop()['time_series']
        print(wave)

    ok99
    iterdict(X)
    print('\n\n................\n')
    pprint(X)
    ok1
    

        
''' - - - - - - - - -
time-zone aware time, usage:

*) get current date:
t1=time.localtime()   <type 'time.struct_time'>

*) convert to string:
timeStr=dateT2Str(t1)

*) revert to struct_time
t2=dateStr2T(timeStr)

*) compute difference in sec:
t3=time.localtime()
delT=time.mktime(t3) - time.mktime(t1)
delSec=delT.total_seconds()
or delT is already in seconds
'''

#...!...!..................
def dateT2Str(xT):  # --> string
    nowStr=time.strftime("%Y%m%d_%H%M%S_%Z",xT)
    return nowStr

#...!...!..................
def dateStr2T(xS):  #  --> datetime
    yT = time.strptime(xS,"%Y%m%d_%H%M%S_%Z")
    return yT

   
