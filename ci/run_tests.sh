#!/bin/bash
set +x
set +e

# Pep8 tests
if [[ "$PEP8_CAUSE_FAILLURE" == "true" ]]; then
  set -e
  cat setup.cfg
  flake8 --statistics --count .
# Else unit and integration tests
else
    set -e

    # Changing dir to avoid loading local files
    mkdir ci-tests
    pushd ci-tests
        python --version
        pip --version
        echo "Pypot path"
        python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../.."))); import pypot'
        python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../.."))); import pypot.robot'
        python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../.."))); import pypot.dynamixel'
        python -c 'import sys;import os;import pypot;sys.stdout.write(os.path.abspath(os.path.join(pypot.__file__, "../.."))); from pypot.dynamixel import Dxl320IO'

        # Vrep start test
        echo "Starting a notebook Controlling a Poppy humanoid in V-REP using pypot.ipynb"
        if [[ -n "$SSH_VREP_SERVER"  ]]; then
            pip install --pre poppy-humanoid
            # Download a PoppyHumanoid ipython notebook
            curl -l -o nb.py https://gist.githubusercontent.com/pierre-rouanet/e6b89340a7ec781c5355/raw/6087117c4d0cc53b54269e1fb0d9c2fc17ef11a8/nb.py
            python nb.py

            pip uninstall -y poppy-humanoid
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

    pushd tests
        pip install coverage requests
        pip install --pre poppy-ergo-jr
        python -m unittest discover
    popd
fi

set +x
set +e
