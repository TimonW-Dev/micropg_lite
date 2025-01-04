#!/bin/bash
# This script creates a PostgreSQL container in Docker, where the exmapleDatabase.sql can then be imported using a tool such as PgAdmin4.
# You may have to install docker. Debian example: sudo apt install docker.io
sudo docker run --restart always -itd -p 5432:5432 --name micropg_lite-testing -e POSTGRES_PASSWORD=123456 postgres