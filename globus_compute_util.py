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

def run_command(command):
    import subprocess
    return subprocess.check_output(command, shell=True).decode().strip()


def get_preview_data(dimension: str, data_file: str):
    import matplotlib
    matplotlib.use('agg')
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib import pyplot as plt
    plt.switch_backend('agg')
    from io import BytesIO
    dimension = [int(dim) for dim in dimension.split()]

    with open(data_file, 'rb') as f:
        data = np.fromfile(f,dtype=np.float32)
        data = np.reshape(data, dimension)

    fig = Figure(dpi=100)
    fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
    ax = fig.add_subplot(111)
    data_min, data_max = np.min(data), np.max(data)
    ax.imshow(data, cmap=plt.get_cmap('rainbow'), norm=plt.Normalize(vmin=data_min, vmax=data_max), aspect='auto')
    buf = BytesIO()
    fig.savefig(buf, format='png')

    return (buf, data_min, data_max)