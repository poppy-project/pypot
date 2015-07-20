#!/bin/bash
echo "Running install.sh on $TRAVIS_OS_NAME"

python -c "import sys; print(sys.version_info);print(sys.version_info >= (3,))"

# Verify python version
python --version

cd ${SETUP_DIR}
python setup.py develop

set -x
cat build/lib/pypot/vrep/__init__.py |grep str
cat build/lib/pypot/vrep/__init__.py |grep basestring
set +x
