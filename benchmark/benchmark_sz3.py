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

class Compressor(BaseModel):
    name: str
    ext: str
    executable: Path
    compress_params: List[str]
    decompress_params: List[str]

class Dataset(BaseModel):
    name: str
    fileNames: List[str]
    folder: Path

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
log_prefix = f"logs/{current_time.month}-{current_time.day}-{current_time.year}_{current_time.hour}-{current_time.minute}-{current_time.second}"
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


def compression(stats: CompressionStats, dataset: Dataset, compressor: Compressor):
    params = compressor.compress_params
    dataset_files = [str(dataset.folder / filename) for filename in dataset.fileNames]
    dataset_file_param = ' '.join(dataset_files)
    params = [dataset_file_param if param == '$fileNames' else param for param in params]


def benchmark(config, do_compression: bool, do_decompression: bool):
    pass

def main():
    parser = argparse.ArgumentParser(
        description="Benchmarking lossy compression algorithms such as SZ3 and its variants",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="anvil_benchmark_config.yml",
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