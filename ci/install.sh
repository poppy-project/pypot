#!/bin/bash
echo "Running install.sh on $TRAVIS_OS_NAME"

# Verify python version
python --version

pushd $SETUP_DIR
    python setup.py install
popd