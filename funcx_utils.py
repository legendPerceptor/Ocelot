import funcx
import pandas as pd

def list_dir(path):
    import os
    return os.listdir(path)

def build_mpi_sbatch_file(job_config, command):
    sbatch_file = f'''#!/bin/bash
#SBATCH --job-name={job_config["name"]}
#SBATCH --time={job_config["time"]}
#SBATCH -p {job_config["partition"]}
#SBATCH -A {job_config["account"]}
#SBATCH --nodes={job_config["nodes"]}
#SBATCH --ntasks-per-node={job_config["ntasks_per_node"]}
#SBATCH --cpus-per-task=1
#SBATCH -o {job_config["name"]}.out
#SBATCH -e {job_config["name"]}.error

module load openmpi/4.0.6
mpirun {command}
'''
    print(sbatch_file)
    return sbatch_file

def mpi_operation(sbatch_file_content, cwd, sbatch_name):
    import os
    import os.path as path
    from subprocess import Popen, PIPE
    batch_file = path.join(cwd, sbatch_name)
    os.system(f'echo "{sbatch_file_content}" > {batch_file}')
    command = f'sbatch {sbatch_name}'
    process = Popen(command, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr

def queue_info(user):
    import os
    from subprocess import Popen, PIPE
    command = f'squeue -u {user}'
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout


def make_dir(path, exist_ok=True):
    import os
    return os.makedirs(path, exist_ok=exist_ok)


def execute(command, cwd, csv_path = None):
    import pandas as pd
    import os
    from subprocess import Popen, PIPE

    process = Popen(command, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if csv_path is None:
        return None, stdout, stderr
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(e)
        return None, stdout, stderr
    return df, stdout, stderr