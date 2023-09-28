#!/bin/bash
# This skript creates an example database with docker
# You may have to install docker. Debian example: sudo apt install docker.io
sudo docker run --restart always -itd -p 5432:5432 --name micropg_lite-testing -e POSTGRES_PASSWORD=123456 postgres