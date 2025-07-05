Setup:
*) create dir tree for processing pipeline
mkdir dataQuEra_2023june; cd dataQuEra_2023june; mkdir ana  jobs  meas calib

*) set env
export QuEra_dataVault=/dataVault/dataQuEra_2023june
export AWS_ACCESS_KEY_ID=$QUERA_AWS_ACCESS_KEY_ID 
export AWS_SECRET_ACCESS_KEY="$QUERA_AWS_SECRET_ACCESS_KEY" 
export AWS_DEFAULT_REGION=$QUERA_AWS_REGION


*) submit 1 job to evolve 2-qubit hamiltonian for 2.05 us, with atoms sepcaed by 11 um, place 4 clusters of such atoms on a 2x4 grid. Use 50 shots for this job to get 400 shots per problem.

- - - -   EMULATOR job run locally - - - - - 
 ./submit_BellState_job.py   --numShots 50   --expName bell_cpu   --tot_num_atom 8  --atom_dist_um 11   --rabi_omega_MHz 1.8 --evol_time_us 2.05  -E  --backendName cpu

saving data as hdf5: /dataVault/dataQuEra_2023june/meas/bell_abc.h5
h5-write : atom_xy.JSON as string (1,) object
h5-write : program_org.JSON as string (1,) object
h5-write : counts_raw.JSON as string (1,) object
h5-write : meta.JSON as string (1,) object
closed  hdf5: /dataVault/dataQuEra_2023june/meas/bell_abc.h5  size=0.01 MB, elaT=0.0 sec

   ./ana_BellState.py --expName   bell_abc   -X  -pab


*) analyse results  & plot
 ./ana_BellState.py --expName   bell_cpu  --showPlots a b

Counts per cluster as dictionary
jj 0 {'gg': 19, 'gr': 0, 'rg': 1, 'rr': 30, 'e': 0}
jj 1 {'gg': 19, 'gr': 0, 'rg': 0, 'rr': 31, 'e': 0}
jj 2 {'gg': 15, 'gr': 0, 'rg': 1, 'rr': 34, 'e': 0}
jj 3 {'gg': 20, 'gr': 1, 'rg': 0, 'rr': 29, 'e': 0}

counts per cluster as Numpy array
[[19  0  1 30]
 [19  0  0 31]
 [15  0  1 34]
 [20  1  0 29]]

creates:
saving data as hdf5: /dataVault/dataQuEra_2023june/ana/bell_cpu.ags.h5
h5-write : atom_xy.JSON (1,) object
h5-write : program_org.JSON (1,) object
h5-write : counts_clust (4, 4) int32
h5-write : prob_clust (3, 4, 4) float32
h5-write : counts_sum (1, 4) int32
h5-write : prob_sum (3, 1, 4) float32
h5-write : meta.JSON as string (1,) object
closed  hdf5: /dataVault/dataQuEra_2023june/ana/bell_abc.ags.h5  size=0.01 MB, elaT=0.0 sec

Graphics saving to  /dataVault/dataQuEra_2023june/ana/bell_abc_f1.png
Graphics saving to  /dataVault/dataQuEra_2023june/ana/bell_abc_f2.png

- - - -   QuEra job run on AWS:  - - - - -
Changes: cpu --> qpu, 8 --> 16 , bell_cpu --> bell_qpu
*) submit:
./submit_BellState_job.py   --numShots 50   --expName bell_qpu   --tot_num_atom 16  --atom_dist_um 11   --rabi_omega_MHz 1.8 --evol_time_us 2.05  -E  --backendName qpu

{'analyzis': {'ana_code': 'ana_BellState.py'},
 'hash': '6e0c9a',
 'payload': {'aquila_area': {'height': Decimal('0.000076'),  'width': Decimal('0.000075')},
             'atom_dist_um': Decimal('11'),
             'atom_in_ghz': 2,
             'class_name': 'ProblemBellState',
             'evol_time_ramp_us': Decimal('0.1'),
             'evol_time_us': Decimal('2.05'),
             'nominal_Rb_um': 7.881194468427195,
             'num_clust': 8,
             'rabi_omega_MHz': 1.8,
             'tot_num_atom': 16},
 'short_name': 'bell_qpu',
 'submit': {'backend': 'aquila',
            'createdAt': '2023-06-08 14:30:17.645000+00:00',
            'date': '20230608_073017_PDT',
            'deviceArn': 'arn:aws:braket:us-east-1::device/qpu/quera/Aquila',
            'num_shots': 50,
            'status': 'CREATED',
            'task_arn': 'arn:aws:braket:us-east-1:765483381942:quantum-task/f9c8b95a-c57a-4905-aeb5-71ef8ddb7e4f',
            'unix_time': 1686234617}}

*) retrieve:
./retrieve_awsQuEra_job.py --expName   bell_qpu

 'job_qa': {'endedAt': '2023-06-08 16:09:18.256000+00:00',
            'exec_date': '20230608_090918_PDT',
            'status': 'COMPLETED',
            'success': True},

*) Analysis, as before
./ana_BellState.py  --expName   bell_qpu 
cl= 0 {'gg': 16, 'gr': 9, 'rg': 3, 'rr': 22, 'e': 0}
cl= 1 {'gg': 19, 'gr': 4, 'rg': 3, 'rr': 24, 'e': 0}
cl= 2 {'gg': 23, 'gr': 3, 'rg': 5, 'rr': 18, 'e': 1}
cl= 3 {'gg': 18, 'gr': 3, 'rg': 5, 'rr': 23, 'e': 1}
cl= 4 {'gg': 29, 'gr': 7, 'rg': 4, 'rr': 10, 'e': 0}
cl= 5 {'gg': 21, 'gr': 4, 'rg': 2, 'rr': 21, 'e': 2}
cl= 6 {'gg': 19, 'gr': 9, 'rg': 2, 'rr': 20, 'e': 0}
cl= 7 {'gg': 26, 'gr': 3, 'rg': 3, 'rr': 18, 'e': 0}
counts per cluster
 [[16  9  3 22]
 [19  4  3 24]
 [23  3  5 18]
 [18  3  5 23]
 [29  7  4 10]
 [21  4  2 21]
 [19  9  2 20]
 [26  3  3 18]]

probabilities averaged, states:[00,01,10,11] x [value, error, counts]
 [[[4.32e-01 1.06e-01 6.82e-02 3.94e-01]]
 [[2.49e-02 1.55e-02 1.27e-02 2.46e-02]]
 [[1.71e+02 4.20e+01 2.70e+01 1.56e+02]]]
