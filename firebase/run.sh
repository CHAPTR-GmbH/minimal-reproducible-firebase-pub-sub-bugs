#!/bin/bash
# py
cd /home/node/functions/python

# Apple M1 silicon hack
export GRPC_BUILD_WITH_BORING_SSL_ASM="" 
export GRPC_PYTHON_BUILD_SYSTEM_RE2=true 
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=true 
export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=true 


# Chown the cache directory to root to avoid permission issues
chown -R root:root /home/node/.cache

# TODO: Build the venv directory using poetry
python3.12 -m pip install poetry
python3.12 -m poetry install
python3.12 -m poetry export -f requirements.txt --output requirements.txt --without-hashes

# Fallback until that is fixed. For now, we build the requirements.txt manually
python3.12 -m venv venv
. "/home/node/functions/python/venv/bin/activate"
python3.12 -m pip install -r requirements.txt

cd ../..

sleep 10

# Run firebase
export FUNCTIONS_DISCOVERY_TIMEOUT=200
firebase emulators:start --project demo-local-development --import /home/node/emulator-data/firestore-data/latest/ --export-on-exit --log-verbosity DEBUG