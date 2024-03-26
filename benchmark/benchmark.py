import yaml
import argparse
import logging
import time
import os
import sys
import pandas as pd
import psutil
import threading
import time

from tabulate import tabulate
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
from pydantic import BaseModel
from typing import List

class Reference(BaseModel):
    name: str
    location: Path

class Compressor(BaseModel):
    name: str
    ext: str
    executable: Path
    compress_params: List[str]
    decompress_params: List[str]

class Dataset(BaseModel):
    name: str
    fileNames: List[str]
    url: str
    folder: Path
    reference: str

class CompressionStats():
    compressor_name: str = ""
    dataset_name: str = ""
    compress_wall_time: float = 0
    compress_cpu_time: float = 0
    compressed_size: int = 0
    original_size: int = 0
    compression_ratio: float = 0
    decompress_wall_time: float = 0
    decompress_cpu_time: float = 0

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)     
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

current_time = datetime.now()
log_prefix = f"{current_time.month}-{current_time.day}-{current_time.year}_{current_time.hour}-{current_time.minute}-{current_time.second}"
os.makedirs(log_prefix)

logger = setup_logger('app_logger', f'{log_prefix}/app.log')
verboseLogger = setup_logger('verbose_logger', f'{log_prefix}/verbose.log', logging.DEBUG)


class ResourceUsage(threading.Thread):
    def __init__(self, pid, filename, earlyStop=False):
        threading.Thread.__init__(self)
        self.p = psutil.Process(pid)
        self.memory_percents_list = []
        self.cpu_percents_list = []
        self.time_counts = []
        self.filename = filename
        self.earlyStop = earlyStop
    
    def run(self):
        time_count = 0
        df = pd.DataFrame({"time_count" : [0],
                           "memory_percents" : [0],
                           "cpu_percents": [0]})
        df.to_csv(self.filename, index=False)
        counter = 0
        while self.p.is_running():
            self.cpu_percents_list.append(psutil.cpu_percent())
            self.memory_percents_list.append(psutil.virtual_memory().percent)
            self.time_counts.append(time_count)

            if counter >= 3:
                df = pd.DataFrame({"time_count" : self.time_counts,
                                        "memory_percents" : self.memory_percents_list,
                                        "cpu_percents": self.cpu_percents_list})
                df.to_csv(self.filename, mode='a', index=False, header=False)
                self.cpu_percents_list = []
                self.memory_percents_list = []
                self.time_counts = []
                counter = 0
            if self.earlyStop and time_count >= 500: # exit early for only 500s
                break
            time_count += 5
            counter += 1
            time.sleep(5)
            
        if len(self.cpu_percents_list) > 0:
            df = pd.DataFrame({"time_count" : self.time_counts,
                               "memory_percents" : self.memory_percents_list,
                               "cpu_percents": self.cpu_percents_list})
            df.to_csv(self.filename, mode='a', index=False, header=False)

        print("<ResourceUsage> Memory and CPU usage collection finished!")
        logger.info(f"<ResourceUsage> Memory and CPU usage collection finished! Data saved to {self.filename}")



def compression(stats: CompressionStats, dataset, compressor, references, compressed_file):
    params = compressor.compress_params
    dataset_files = [str(dataset.folder / filename) for filename in dataset.fileNames]
    dataset_file_param = ' '.join(dataset_files)
    params = [str(references[dataset.reference].location) if param == '$reference' else param for param in params]
    params = [dataset_file_param if param == '$fileNames' else param for param in params]
    
    if compressor.name.startswith('fastqzip'):
        # collect global_stats and chunk_stats
        global_stats_file = Path(log_prefix) /(dataset.name + '-' + compressor.name + '-global_stats.csv')
        chunk_stats_file = Path(log_prefix) / (dataset.name + '-' + compressor.name + '-chunk_stats.csv')
        command_line_param = [str(compressor.executable)] + params + ["--output", compressed_file]
        command_line_param += ['--global_stats', str(global_stats_file), '--chunk_stats', str(chunk_stats_file)]
    elif compressor.name.startswith('genozip'):
        if len(dataset_files) == 2:
            params = ["--pair"] + params
        command_line_param = [str(Path(compressor.executable) / 'genozip')] + params + ["--output", compressed_file]
    elif compressor.name.startswith('FQSqueezer'):
        if len(dataset_files) == 2:
            params[1] = "-p"
        params = [compressed_file if param == '$compressedFileName' else param for param in params]
        command_line_param = [str(compressor.executable)] + params
    elif compressor.name.startswith('GTX'):
        command_line_param = [str(compressor.executable)] + params + ["-o", compressed_file]

    command_line_param_str = ' '.join(command_line_param)
    # execute the compress command
    print("compress param: ", command_line_param_str)
    logger.info(f"compress_param: {command_line_param_str}")
    logger.info(f"start running compression for dataset <{dataset.name}> with compressor <{compressor.name}>")
    start = time.perf_counter()
    process = Popen(' '.join(["time", command_line_param_str]), shell=True, stdout = PIPE, stderr=PIPE, text=True, executable='/bin/bash')
    resource_thread = ResourceUsage(pid=process.pid,
                                    filename=str(Path(log_prefix) / f"{dataset.name}-{compressor.name}-compress-resources.csv"))
    resource_thread.start()
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            verboseLogger.debug(f"[compress]<{dataset.name}><{compressor.name}> {output.strip()}")
    process.wait()
    resource_thread.join()
    stdout, stderr = process.communicate()
    print("stdout:", stdout)
    print("stderr: ", stderr)
    logger.error(f"[compress]<{dataset.name}><{compressor.name}> {stderr.strip()}")
    end = time.perf_counter()
    elapsed_time = end - start
    cpu_times = stderr.strip().split('\n')[-3:]  # real_time, user_time, sys_time
    real_time = cpu_times[1].split()[1]
    logger.info(f"finished running compression for dataset <{dataset.name}> with compressor <{compressor.name}>")
    print(f"finished running compression for dataset <{dataset.name}> with compressor <{compressor.name}>")
    # collect stats
    try:
        stats.compress_wall_time = elapsed_time
        stats.compress_cpu_time = real_time
        stats.compressed_size = os.path.getsize(compressed_file)
        stats.original_size = sum([os.path.getsize(dataset_file) for dataset_file in dataset_files])
        stats.compression_ratio = stats.original_size / stats.compressed_size
    except Exception as error:
        logger.error("Cannot finish collecting the stats for compression!")
        logger.error(error)


def decompression(stats: CompressionStats, dataset, compressor, references, compressed_file, decompress_output_folder):
    params = compressor.decompress_params
    params = [compressed_file if param == '$compressedFileName' else param for param in params]
    if compressor.name.startswith('fastqzip'):
        params = [str(references[dataset.reference].location) if param == '$reference' else param for param in params]
        command_line_param = [str(compressor.executable)] + params + ["--output", decompress_output_folder]
    elif compressor.name.startswith('genozip'):
        ref_file = str(references[dataset.reference].location).split('.')[0] + '.ref.genozip'
        params = [ ref_file if param == '$reference' else param for param in params]
        command_line_param = [str(Path(compressor.executable) / "genounzip")] + params + ["--output", decompress_output_folder]
    elif compressor.name.startswith('FQSqueezer'):
        params = params + ["-out", str(Path(decompress_output_folder) / f"{dataset.name}-{compressor.name}-R1.fq"),
                           "-out2", str(Path(decompress_output_folder)/ f"{dataset.name}-{compressor.name}-R2.fq")]
        command_line_param = [str(compressor.executable)] + params + [compressed_file]
    elif compressor.name.startswith('GTX'):
        command_line_param = [str(compressor.executable)] + params + ["-O", decompress_output_folder]
    
    command_line_param_str = ' '.join(command_line_param)
    # execute the decompress command
    print("decompress param: ", command_line_param_str)
    logger.info(f"decompress param: {command_line_param_str}")
    logger.info(f"start running decompression for dataset <{dataset.name}> with compressor <{compressor.name}>")
    start = time.perf_counter()
    process = Popen(' '.join(["time", command_line_param_str]), shell=True, stdout = PIPE, stderr=PIPE, text=True, executable='/bin/bash')
    resource_thread = ResourceUsage(pid=process.pid,
                                    filename=str(Path(log_prefix) / f"{dataset.name}-{compressor.name}-decompress-resources.csv"))
    resource_thread.start()
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            verboseLogger.debug(f"[decompress]<{dataset.name}><{compressor.name}> {output.strip()}")
    process.wait()
    resource_thread.join()
    _, stderr = process.communicate()
    logger.error(f"[decompress]<{dataset.name}><{compressor.name}> {stderr.strip()}")
    end = time.perf_counter()
    elapsed_time = end - start
    print("stderr splited: ", stderr.strip().split('\n'))
    cpu_times = stderr.strip().split('\n')[-3:]  # real_time, user_time, sys_time
    real_time = cpu_times[1].split()[1]
    stats.decompress_wall_time = elapsed_time
    stats.decompress_cpu_time = real_time


def benchmark(config, do_compression: bool, do_decompression: bool):
    # parse config to pydantic objects
    references = {reference["name"] : Reference(**reference) for reference in config["references"]}
    datasets = [Dataset(**dataset) for dataset in config["datasets"]]
    compressors = [Compressor(**compressor) for compressor in config["compressors"]]
    stats_file_path = f"{log_prefix}/{log_prefix}_stats.csv"
    global_stats = {
        "compressor_name": [],
        "dataset_name": [],
        "compress_wall_time": [],
        "compress_cpu_time": [],
        "compressed_size": [],
        "original_size": [],
        "compression_ratio": [],
        "decompress_wall_time": [],
        "decompress_cpu_time": []
    }
    # for each compressor, run all datasets
    logger.info(f"start running benchmark on #{len(datasets)} datasets with #{len(compressors)} compressors!")
    for compressor in compressors:
        for dataset in datasets:
            stats = CompressionStats()
            stats.compressor_name = compressor.name
            stats.dataset_name = dataset.name
            compressed_file = str(Path(config["global"]["output_folder"]) / (dataset.name + '-' + compressor.name + compressor.ext))
            # do the compression
            if(do_compression):
                try:
                    compression(stats, dataset, compressor, references, compressed_file)
                except Exception as error:
                    logger.error(error)
                    sys.exit(1)
            # do the decompression
            decompress_output_folder = str(Path(config["global"]["output_folder"]))
            if(do_decompression):
                try:
                    decompression(stats, dataset, compressor, references, compressed_file, decompress_output_folder)
                except Exception as error:
                    logger.error(error)
                    sys.exit(2)

            # finished benchmarking a dataset, saving data
            logger.info(f"finished benchmarking dataset <{dataset.name}> with compressor <{compressor.name}>")
            for key in global_stats.keys():
                global_stats[key].append(getattr(stats, key))
            print(global_stats)
            tmp_df = pd.DataFrame(global_stats)
            print(tabulate(tmp_df, headers='keys', tablefmt='psql'))
            logger.info(f"Tabulated partial results\n{tabulate(tmp_df, headers='keys', tablefmt='psql')}")
            tmp_df.to_csv(stats_file_path, index=False)



def main():
    parser = argparse.ArgumentParser(
        description="Benchmarking genome sequence compression algorihtms",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="The config file for benchmarking"
    )

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="benchmark",
        help="There are three modes: benchmark, compress, decompress. `benchmark` mode will do compression and decopmression and collect all data, while the other two only collects partial data."
    )

    args = parser.parse_args()

    do_compression = True
    do_decompression = True
    if(args.mode == 'compress'):
        do_decompression = False
        logger.info("This program does compression ONLY and collects partial data")
    elif(args.mode == 'decompress'):
        do_compression = False
        logger.info("This program does decompression ONLY and collects partial data")
    else:
        logger.info("This program does full compression/decompression and will collect all data")


    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    logger.info("finished loading YAML config, ready for benchmarking!")
    benchmark(config, do_compression, do_decompression)
    logger.info("Congratulations! You have finished all benchmarking!")

if __name__ == '__main__':
    main()