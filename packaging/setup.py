from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="micropg_lite",
    version="0.0.0",  # Replaced automatically from the release tag by the publish workflow
    author="TimonW-Dev",
    author_email="timon.github@outlook.com",
    description=(
        "A lightweight PostgreSQL database driver for MicroPython, designed for microcontrollers (e.g., ESP8266) with limited RAM."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TimonW-Dev/micropg_lite",
    py_modules=["micropg_lite"],
    classifiers=[
        "Programming Language :: Python :: Implementation :: MicroPython",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Other OS",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Database",
    ],
    python_requires=">=3.4",
    keywords="micropython postgres postgresql esp8266 esp32 database driver",
    project_urls={
        "Bug Tracker": "https://github.com/TimonW-Dev/micropg_lite/issues",
        "Documentation": "https://github.com/TimonW-Dev/micropg_lite/wiki",
        "Source Code": "https://github.com/TimonW-Dev/micropg_lite",
    },
)
