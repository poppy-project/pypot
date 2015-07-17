#!/bin/bash
echo "Running install.sh on $TRAVIS_OS_NAME"

# Verify python version
python --version

cd ${SETUP_DIR}
python setup.py install


