#!/bin/bash
echo "Running install.sh on $TRAVIS_OS_NAME"

python -c "import sys; print(sys.version_info);print(sys.version_info >= (3,))"

# Verify python version
python --version

pip install -e ./
# pushd $SETUP_DIR
#     python setup.py install
# popd
