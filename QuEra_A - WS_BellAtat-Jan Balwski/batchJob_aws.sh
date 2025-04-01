#!/bin/bash
set -u ;  # exit  if you try to use an uninitialized variable
#set -x ;  # print out the statements as they are being executed
set -e ;  #  bash exits if any statement returns a non-true return value
#set -o errexit ;  # exit if any statement returns a non-true return value


dist=11
shots=1000 ; nAtom=8 ; backN=cpu   # CPU emulator
shots=10 ; nAtom=16; backN=qpu   # real HW

basePath=/dataVault/dataQuEra_2023juneBellB_$backN

if [ ! -d "$basePath" ]; then
    echo create $basePath
    mkdir $basePath
    cd $basePath
    mkdir ana  jobs  meas
    cd -
fi
    
k=0

#for i in {0..120}; do  # CPU  
#    t_us=`python3 -c "print('%.2f'%(0.3 + $i * 0.03))"`  # CPU , full range

#for i in {0..29}; do  #QPU-Bell
#    t_us=`python3 -c "print('%.2f'%(1.6 + $i * 0.05))"`  # QPU - Bell, course
        
#for i in {0..11}; do  #QPU-Bell
#    shots=30 ;t_us=`python3 -c "print('%.2f'%(1.9 + $i * 0.05))"`  # QPU - Bell, zoom-in
        
for i in {0..24}; do  #QPU-Bell
    t_us=`python3 -c "print('%.2f'%(0.3 + $i * 0.03))"`  # QPU - 2H, fine
        
    k=$[ $k +1 ]
    expN=bell_${backN}_t$t_us
    
    echo $k  expN=$expN
    #continue
    
    #time ./submit_BellState_job.py  --numShots ${shots} --backendName ${backN}  --expName ${expN} --basePath ${basePath}  --tot_num_atom $nAtom  --atom_dist_um $dist   --rabi_omega_MHz 1.8 --evol_time_us $t_us -E  >& out/Ls.$expN
    
    ./retrieve_awsQuEra_job.py  --expName ${expN} --basePath ${basePath} 
    ./ana_BellState.py  --expName ${expN} --basePath ${basePath}  -X >& out/La.$expN
    #break
done



