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