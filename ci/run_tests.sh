#!/bin/bash
set +x
set +e

# Pep8 tests
if [[ "$PEP8_CAUSE_FAILLURE" == "true" ]]; then
  set -e
fi
flake8 --config=ci/flake8.config --statistics --count .
set -e


# TODO :)
which python
which pip
python --version

python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../..")))'

cat <<EOF | python -
import pypot
import pypot.robot
import pypot.dynamixel
EOF


# Vrep start test
pip install -qq poppy-humanoid
echo "Starting a notebook Controlling a Poppy humanoid in V-REP using pypot.ipynb"
if [[ -n "$SSH_VREP_SERVER"  ]]; then
    # Download a PoppyHumanoid ipython notebook
    pip -qq install runipy
    curl -o nb.ipynb https://raw.githubusercontent.com/poppy-project/poppy-humanoid/master/software/samples/notebooks/Controlling%20a%20Poppy%20humanoid%20in%20V-REP%20using%20pypot.ipynb
    runipy -o nb.ipynb
    python ci/test_vrep.py
fi

# Old test of running VREP localy (network trouble)
#     pushd $VREP_ROOT_DIR/
#         if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
#             xvfb-run --auto-servernum --server-num=1 ./vrep.sh -h  &
#         else
#             ./vrep.app/Contents/MacOS/vrep -h  &
#         fi
#         sleep 10
#     popd
#     python ci/test_vrep.py
    


set +x
set +e



