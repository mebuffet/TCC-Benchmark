#!/bin/bash

date > 5-128.txt
python3 cloudmarking.py --config-file configuration-5-128.json
sleep 60

date > 15-128.txt
python3 cloudmarking.py --config-file configuration-15-128.json
sleep 60

date > 30-128.txt
python3 cloudmarking.py --config-file configuration-30-128.json
sleep 60

date > 5-256.txt
python3 cloudmarking.py --config-file configuration-5-256.json
sleep 60

date > 15-256.txt
python3 cloudmarking.py --config-file configuration-15-256.json
sleep 60

date > 30-256.txt
python3 cloudmarking.py --config-file configuration-30-256.json
sleep 60

date > 5-512.txt
python3 cloudmarking.py --config-file configuration-5-512.json
sleep 60

date > 15-512.txt
python3 cloudmarking.py --config-file configuration-15-512.json
sleep 60

date > 30-512.txt
python3 cloudmarking.py --config-file configuration-30-512.json
sleep 60
