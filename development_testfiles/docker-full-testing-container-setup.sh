#!/bin/bash
# This script creates a container for testing including test data and SSL. This script creates the necessary Docker environment for the test_skript.py
# You may have to install docker. Debian example: sudo apt install docker.io
sudo docker build -t micropg_lite-testing:v1 .
sudo docker run --restart always -itd -p 5432:5432 --name micropg_lite-testing micropg_lite-testing:v1