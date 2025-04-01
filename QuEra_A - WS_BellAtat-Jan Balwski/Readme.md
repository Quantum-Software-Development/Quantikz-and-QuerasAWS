<b> Python/Braket Pipeline for AWS-Based QuEra Job Submission and Retrieval </b>

The Python/Braket pipeline is designed to seamlessly interact with AWS to submit and retrieve QuEra jobs. The pipeline incorporates a key feature where all information related to a specific task is stored and accessed from a single HDF5 file. This file is continuously updated as the analysis progresses. Unlike the complex and less human-readable ARN job ID, users have the flexibility to define a concise and easily understandable name for this file.

One of the core advantages of this pipeline is the decoupling of post-processing and plotting from the AWS interaction. Users only need to read a local HDF5 file to perform post-processing tasks. Additionally, multiple jobs can be submitted using a convenient bash script (batchJob_aws.sh). The results from these multiple jobs can be effortlessly combined by utilizing post-processing techniques on Numpy arrays stored in HDF5 (pl_summaryBellState.py).

See Readme.txt for an example sequence of commands. The dataQuEra_2023june.tgz contains all outputs.


![Image](submit+retriev_QuEra_AWS_job.svg)

