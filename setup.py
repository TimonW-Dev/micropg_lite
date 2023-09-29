from setuptools import setup, find_packages

with open("pypi-README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="micropg_lite", 
    version="2.1.0",
    author="TimonW-Dev",
    author_email="timon-github@outlook.com",
    description="A lightweight micropython PostgreSQL driver made for ESP8266 and other microchips with less ram",
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