# Ocelot 2.0

Ocelot is a lossy compression and transfer framework for floating-point scientific data. The data files are usually planar (e.g. [CESM dataset](https://climatedata.ibs.re.kr/data/cesm2-lens) 1800x3600) or cubic (e.g. [Nyx dataset](https://ieee-dataport.org/open-access/nyx-cosmological-simulation-dataset) 512x512x512). Some extremely large single file can be over 900 GB (e.g. [Turbulent Channel Flow](https://klacansky.com/open-scivis-datasets/category-simulation.html) 10240x7680x1536). Other datasets may contain thousands of smaller files. The goal of this project is to provide a friendly user-interface for users to compress, transfer and store these huge datasets.

## New Features

- Support compression of extremely large single file.
- Continuous collection of compression and transfer data while using the app to make better predictions in the future.
- Install the compression pacakages automatically on desired machines.
- PyQt5 user interface

## Ocelot 1.0 Features

- Basic user interface with tkinter
- Support compression (on Machine A) + transfer (via Globus) + decompression (on Machine B) workflow.
- SZ3-specific feature extraction
- Prediction of compression ratio and time with Machine Learning models

### Publication:

Yuanjian Liu, Sheng Di, Kyle Chard, Ian Foster, Franck Cappello, "Optimizing Scientific Data Transfer on Globus with Error-bounded Lossy Compression", in 43rd IEEE International Conference on Distributed Computing Systems (IEEE ICDCS2023), 2023.

**BibTex Citation**

```bibtex
@inproceedings{inproceedings,
author = {Liu, Yuanjian and Di, Sheng and Chard, Kyle and Foster, Ian and Cappello, Franck},
year = {2023},
month = {07},
pages = {703-713},
title = {Optimizing Scientific Data Transfer on Globus with Error-Bounded Lossy Compression},
doi = {10.1109/ICDCS57875.2023.00064}
}
```

