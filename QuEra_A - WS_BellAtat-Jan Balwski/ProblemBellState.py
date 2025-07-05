__author__ = "Jan Balewski"
__email__ = "janstar1122@gmail.com"

import time
from pprint import pprint
import numpy as np
from decimal import Decimal
import json  # for saving program into bigD

from braket.ahs.atom_arrangement import AtomArrangement
from braket.timings.time_series import TimeSeries
from braket.ahs.driving_field import DrivingField
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation

from toolbox.UAwsQuEra_job import harvest_submitInfo , retrieve_aws_job, harvest_retrievInfo, postprocess_job_results, compute_nominal_rb

from toolbox.Util_stats import do_yield_stats

#............................
#............................
#............................
class ProblemBellState():  # (perhaps) extendable to GHZ states  
    def __init__(self, args, jobMD=None, expD=None):
        self.verb=args.verb
        print('Task:',self.__class__.__name__)
        if jobMD==None:
            self._buildSubmitMeta(args)
        else:
            assert jobMD['payload']['class_name']==self.__class__.__name__
            self.meta=jobMD
            
        self.expD={} if expD==None else expD
           
    @property
    def submitMeta(self):
        return self.meta
    @property
    def numCirc(self):
        return len(self.circL)
        
#...!...!....................
    def _buildSubmitMeta(self,args):
        
        smd={'num_shots':args.numShots}
        smd['backend']=args.backendName
        
        # analyzis info
        amd={'ana_code':'ana_BellState.py'}

        pd={}  # payload
        pd['atom_dist_um']=Decimal(args.atom_dist_um)
        pd['evol_time_us']=Decimal(args.evol_time_us)
        pd['evol_time_ramp_us']=Decimal('0.1') 
                
        pd['rabi_omega_MHz']=args.rabi_omega_MHz
        pd['atom_in_clust']=args.atom_in_clust
        pd['tot_num_atom']=args.tot_num_atom
        pd['num_clust']=pd['tot_num_atom']//pd['atom_in_clust']
               
        pd['class_name']=self.__class__.__name__
        #pd['info']='ini theta:%.1f phi:%.1f q:%s'%(pd['theta'],pd['phi'],csd['text_qubits'])
  
        md={ 'payload':pd,'submit':smd,'analyzis':amd}  # 'circ_sum':csd ,##
        md['short_name']=args.expName            

        self.meta=md
        if self.verb>1:
            print('BMD:');pprint(md)

#...!...!....................
    def placeAtoms(self):
        # hardcoded filed-of-view for Aquila
        AQUILA={'area': {'height': Decimal('0.000076'),  'width': Decimal('0.000075')},
                'geometry': {'numberSitesMax': 256,
                             'positionResolution': Decimal('1E-7'),
                             'spacingRadialMin': Decimal('0.000004'),
                             'spacingVerticalMin': Decimal('0.000004')}
                }
        
        M1=1000000
        xy00= 2* AQUILA['geometry'][ 'positionResolution']
        maxX=AQUILA['area']['width']-xy00
        maxY=AQUILA['area']['height']-xy00
        pd=self.meta['payload']
        register = AtomArrangement()
        bellDistY=pd['atom_dist_um']/M1 # in (m)
        gridDistX=Decimal('24e-6') # in M
        gridDistY=Decimal('32e-6')+bellDistY # in M
        nClust=pd['num_clust']
        nAtom= pd['atom_in_clust']
        numY=2  # num clusters per y-grid directions

        assert nAtom==2  # tmp, only BellState
        print('place %d clusters , %d atoms each \ni j  x(m)     y(m)    max X,Y:'%(nClust,nAtom),maxX,maxY) 
        for k in range(nClust):
            i=k//numY ; j=k%numY 
            x=xy00+i*gridDistX ;  y0=xy00+j*gridDistY
            for l in range(nAtom):
                y=y0+l*bellDistY
                if i%2==0 :  # reverse y-dir for even columns
                    y=maxY-y
                assert x>=0 ; assert x<=maxX
                assert y>=0 ; assert y<=maxY
                print(i,j,x,y,x<=maxX, y<maxY)
                register.add([x,y])

        self.register=register

        #... update meta-data
        self.meta['payload']['aquila_area']=AQUILA['area']
        # atoms placement to dataD
        xL=register.coordinate_list(0)
        yL=register.coordinate_list(1)
        xD=[[x,y] for x,y in zip(xL,yL)]
        self.expD['atom_xy.JSON']=json.dumps(xD, default=str) # Decimal --> str
        if self.verb<=1: return

        print('\ndump atoms coordinates')
        for i in range(nAtom):
            x=xL[i]*M1
            y=yL[i]*M1
            print('%d atom : x=%.2f y= %.1f (um)'%(i,x,y))  
    
#...!...!....................
    def buildHamiltonian(self):
        M1=1000000
        pd=self.meta['payload']
        t_max  =pd['evol_time_us']/M1
        t_ramp =pd['evol_time_ramp_us']/M1

        assert t_max>= 2* t_ramp+ t_ramp  # for simpler interpretation
        
        omega_min = 0       
        omega_max = pd['rabi_omega_MHz'] * 2 * np.pi *1e6  # units rad/sec
        delta_max=0           # no detuning
        
        # constant Rabi frequency
       
        t_points = [0, t_ramp, t_max - t_ramp, t_max]
        omega_values = [omega_min, omega_max, omega_max, omega_min]
        Omega = TimeSeries()
        for t,v in zip(t_points,omega_values):
            bb=int(v/400)*Decimal('400')  
            Omega.put(t,bb)
            
        # all-zero phase and detuning Delta
        Phase = TimeSeries().put(0.0, 0.0).put(t_max, 0.0)  # (time [s], value [rad])
        Delta_global = TimeSeries().put(0.0, 0.0).put(t_max, delta_max)  # (time [s], value [rad/s])

        drive = DrivingField(
            amplitude=Omega,
            phase=Phase,
            detuning=Delta_global
        )
        H = Hamiltonian()
        H += drive
        self.H=H
        pd['nominal_Rb_um']=compute_nominal_rb(omega_max/1e6, 0.)
        if self.verb<=1: return

        print('\ndump drive filed Amplitude(time) :\n',drive.amplitude.time_series.times(), drive.amplitude.time_series.values())

#...!...!....................
    def buildProgram(self):
        pd=self.meta['payload']
        ahs_program = AnalogHamiltonianSimulation(
            hamiltonian=self.H,
            register=self.register
        )

        
        # program to dataD
        circD=ahs_program.to_ir().dict()
        self.expD['program_org.JSON']=json.dumps(circD, default=str) # Decimal --> str       

        if  self.verb>1:
            print('\ndump Schrodinger problem:')           
            pprint(circD)
            
        return ahs_program

#...!...!..................
    def postprocess_submit(self,job):        
        harvest_submitInfo(job,self.meta,taskName='bell')
        

#...!...!..................
    def retrieve_job(self,job=None):
        
        isBatch= 'batch_handles' in self.expD  # my flag
        
        if job==None:
            smd=self.meta['submit']  # submit-MD
            arn=smd['task_arn']
            job = retrieve_aws_job( arn, verb=self.verb)
                
            print('retrieved ARN=',arn)
        if self.verb>1: print('job meta:'); pprint( job.metadata())
        result=job.result()
        
        print('res:', type(result))
       
        t1=time.time()    
        harvest_retrievInfo(job.metadata(),self.meta)
        
        if isBatch:
            never_tested22
            jidL=[x.decode("utf-8") for x in expD['batch_handles']]
            print('jjj',jidL)
            jobL = [backend.retrieve_job(jid) for jid in jidL ]
            resultL =[ job.result() for job in jobL]
            jobMD['submit']['cost']*=len(jidL)
        else:
            rawBitstr=job.result().get_counts()
            #print('tt',type(rawBitstr));  #pprint(rawBitstr)
            
        t2=time.time()
        print('retriev job(s)  took %.1f sec'%(t2-t1))

        postprocess_job_results(rawBitstr,self.meta,self.expD)

#...!...!..................
    def analyzeExperiment(self):
        import json # tmp for raw data  unpacking
        rawBitstr=json.loads(self.expD.pop('counts_raw.JSON')[0])
        if len(rawBitstr) <17 :
             print('dump rawBitstr:'); pprint(rawBitstr)
        pd=self.meta['payload']
        # process cluster of atoms independently
        nClust=pd['num_clust']
        nAtom= pd['atom_in_clust']
        t_max=self.meta['payload']['evol_time_us']
        a_dist=self.meta['payload']['atom_dist_um']
        omega_MHz= self.meta['payload']['rabi_omega_MHz']
        
        NB=1<<nAtom  # number of possible bit-strings
        rgStates=[format(i, f'0{nAtom}b').replace('0', 'g').replace('1', 'r') for i in range(NB) ]  # works for any number of atoms in acluster
        
        #.... update meta-data
        amd=self.meta['analyzis']
        amd['num_rg_states']=NB
        amd['rg_states_list']=rgStates  # order as stored in self.expD['prob_clust']        
        #1print('md-keys:',self.meta.keys());   pprint(amd) 
        
        oneCnt={ rg:0 for rg in rgStates}
        oneCnt['e']=0
        cnt={ k:oneCnt.copy()  for k in range(nClust)}        
        #print('cnt0'); pprint(cnt)
        
        for key in rawBitstr:
            val=rawBitstr[key]
            print('key:',key,val)
            # split key into clusters
            for k in range(nClust):
                i=k*nAtom
                s=key[i:i+nAtom]
                if 'e' in s : s="e"
                cnt[k][s]+=val
        print('\nEvolution time=%s us, dist=%s um, Omega=%.2f MHz, job: %s'%(t_max,a_dist,omega_MHz,self.meta['short_name']))
        print('%d atoms:'%nAtom); pprint(cnt)
                    
        def counts2numpy(num_clust,egrCnt):
            # all is data driven because some bit-strings may be absent
            counts=np.zeros((num_clust,NB),dtype=np.int32)
            #print('pp',counts.shape)
            for j in egrCnt:  # loop over clusters which see data
                rec=egrCnt[j]  # all bits strings for given cluster
                print('cl=',j,rec)                
                for key in rec:
                    if key=='e': continue  # skip shot if an atom was missing
                    i=rgStates.index(key)
                    counts[j][i]=rec[key]
            print('counts per cluster\n',counts)
            return counts
        
        dataY=counts2numpy(nClust,cnt)
        dataP=do_yield_stats(dataY)
        
        self.expD['counts_clust']=dataY # shape[nClust,NB]
        self.expD['prob_clust']=dataP

        # sum all atoms
        dataYS=np.sum(dataY,axis=0).reshape(1,-1)
        dataPS=do_yield_stats(dataYS)
        self.expD['counts_sum']=dataYS.astype('int32')
        self.expD['prob_sum']=dataPS
        
        print('probabilities averaged, states:[00,01,10,11] x [value, error, counts]\n',dataPS[:,0,:]) 
       
 
