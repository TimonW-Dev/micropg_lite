#!/bin/bash
# This script creates a container for testing including test data and SSL. This script creates the necessary Docker environment for the test_skript.py
# You may have to install docker. Debian example: sudo apt install docker.io
# For a simple container it is sufficient to use the command on the line below and the data can be imported manually if necessary.
# sudo docker run --restart always -itd -p 5432:5432 --name micropg_lite-testing -e POSTGRES_PASSWORD=123456 postgres
sudo docker build -t micropg_lite-fullpostgres .
sudo docker run --restart always -itd -p 5432:5432 --name micropg_lite-testing micropg_lite-fullpostgres