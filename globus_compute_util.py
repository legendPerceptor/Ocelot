import globus_compute_sdk

def list_dir(path):
    import os
    return os.listdir(path)

def list_cpu():
    import subprocess
    command = "lscpu"
    return subprocess.check_output(command, shell=True).decode().strip()

def remove_files(files):
    import os
    try:
        for file in files:
            os.remove(file)
    except Exception as e:
        return False
    return True

def save_str_to_file(filepath, content: str):
    with open(filepath, 'w') as f:
        f.write(content)
    return 0

def run_command(command):
    import subprocess
    return subprocess.check_output(command, shell=True).decode().strip()


def build_sbatch_file(job_config, command:str, work_dir:str, module_load:str=""):
    from pathlib import Path
    log_file_prefix = str(Path(work_dir) / job_config["name"])
    sbatch_file = f'''#!/bin/bash
#SBATCH --job-name={job_config["name"]}
#SBATCH --time={job_config["time"]}
#SBATCH -p {job_config["partition"]}
#SBATCH -A {job_config["account"]}
#SBATCH --nodes={job_config["nodes"]}
#SBATCH --ntasks-per-node={job_config["ntasks_per_node"]}
#SBATCH --mem={job_config["memory"]}
#SBATCH -o {log_file_prefix}-%j.out
#SBATCH -e {log_file_prefix}-%j.error

{module_load}
date
{command}
date
'''
    return sbatch_file

def get_partial_preview_data(dimension: str, data_file: str, layer_number: int, is_float64: bool=False):
    import matplotlib
    matplotlib.use('agg')
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib import pyplot as plt
    plt.switch_backend('agg')
    from io import BytesIO
    dimension = [int(dim) for dim in dimension.split()]
    if len(dimension) != 3: 
        # error, this function only deals with 3D tensor
        return (-1, -1, -1)
    
    layer_size = dimension[0] * dimension[1]
    data_type = np.float32 if not is_float64 else np.float64
    
    with open(data_file, 'rb') as f:
        f.seek(layer_number * layer_size * np.dtype(data_type).itemsize)
        layer_data = np.fromfile(f, dtype=data_type, count=layer_size)
        layer_data = layer_data.reshape(dimension[0], dimension[1])

    fig = Figure(dpi=100)
    fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
    ax = fig.add_subplot(111)
    data_min, data_max = np.min(layer_data), np.max(layer_data)
    ax.imshow(layer_data, cmap=plt.get_cmap('rainbow'), norm=plt.Normalize(vmin=data_min, vmax=data_max), aspect='auto')
    buf = BytesIO()
    fig.savefig(buf, format='png')

    return (buf, data_min, data_max)



def get_preview_data(dimension: str, data_file: str, is_float64:bool=False):
    import matplotlib
    matplotlib.use('agg')
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib import pyplot as plt
    plt.switch_backend('agg')
    from io import BytesIO
    dimension = [int(dim) for dim in dimension.split()]
    data_type = np.float32 if not is_float64 else np.float64

    with open(data_file, 'rb') as f:
        data = np.fromfile(f,dtype=data_type)
        data = np.reshape(data, dimension)

    fig = Figure(dpi=100)
    fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
    ax = fig.add_subplot(111)
    data_min, data_max = np.min(data), np.max(data)
    ax.imshow(data, cmap=plt.get_cmap('rainbow'), norm=plt.Normalize(vmin=data_min, vmax=data_max), aspect='auto')
    buf = BytesIO()
    fig.savefig(buf, format='png')

    return (buf, data_min, data_max)