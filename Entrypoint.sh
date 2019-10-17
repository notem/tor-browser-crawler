#!/bin/bash

# configures and runs a crawl (inside a docker container)
# IMPORTANT: If this file is changed, docker container needs to be rebuilt

# globals
PYTHON_VERSION='python2.7'
PYTHON_PATH=`which $PYTHON_VERSION`
BASE='/home/docker/tbcrawl'

# set offloads
ifconfig $2 mtu 1500
ethtool -K $2 tx off rx off tso off gso off gro off lro off

# install python requirements
pushd ${BASE}
pip install -U -r requirements.txt

# copy tor browser bundle
rm -rf tor-browser_en-US
cp -r /home/docker/tbb_setup/tor-browser_en-US .

# TODO: do other stuff here if you need to

# Run command with params
python $1
