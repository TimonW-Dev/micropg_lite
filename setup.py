from setuptools import setup, find_packages

with open("pypi-README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="micropg_lite", 
    version="2.1.0",
    author="TimonW-Dev",
    author_email="timon-github@outlook.com",
    description="A MicroPython PostgreSQL database driver made for microcontrollers (specifically for ESP8266) that are low on RAM.",
    long_description=long_description,
    long_description_content_type="text/markdown",  
    url="https://github.com/TimonW-Dev/micropg_lite",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=["micropg_lite"],
    package_dir={'':'.'},
)