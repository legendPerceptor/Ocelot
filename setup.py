from setuptools import setup, find_packages

with open("readme.md", 'r') as f:
    long_description = f.read()

setup(
    name="ocelot",
    version="1.0",
    author="Yuanjian Liu",
    author_email="yuanjian@uchicago.edu",
    description="Ocelot is a lossy compression and transfer framework for floating-point scientific data.",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[
        "tabulate>=0.9.0",
        "pydantic>=1.10.14",
        "psutil>=5.9.8",
        "pandas>=2.2.1",
        "PyYAML>=6.0.1",
        "PyQt5>=5.15.10",
        "globus_sdk>=3.37.0",
    ]
)