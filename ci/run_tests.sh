#!/bin/bash
set +x
set +e

# Pep8 tests
if [[ "$PEP8_CAUSE_FAILLURE" == "true" ]]; then
  set -e
  cat setup.cfg
fi
flake8 --statistics --count .

set -e

# Changing dir to avoid loading local files
mkdir ci-tests
pushd ci-tests
    python --version
    pip --version
    echo "Pypot path"
    python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../..")))'
    python -c 'import pypot;import pypot.robot;import pypot.dynamixel'

    # Vrep start test
    echo "Starting a notebook Controlling a Poppy humanoid in V-REP using pypot.ipynb"
    if [[ -n "$SSH_VREP_SERVER"  ]]; then
        pip -qq install poppy-humanoid
        # Download a PoppyHumanoid ipython notebook
        curl -o nb.ipynb https://raw.githubusercontent.com/poppy-project/poppy-humanoid/master/software/samples/notebooks/Controlling%20a%20Poppy%20humanoid%20in%20V-REP%20using%20pypot.ipynb
        runipy -o nb.ipynb
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
popd


set +x
set +e



