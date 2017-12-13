#!/bin/bash
set +x
set +e

# Pep8 tests
if [[ "$PEP8_CAUSE_FAILLURE" == "true" ]]; then
  set -e
  pip install flake8
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
            pip install poppy-humanoid
            # Download a PoppyHumanoid ipython notebook
            curl -l -o nb.py https://gist.githubusercontent.com/pierre-rouanet/e6b89340a7ec781c5355/raw/64bb25ba01e077160e7b04e485d78164ac53fdf6/nb.py
            python nb.py

            pip uninstall -y poppy-creature poppy-humanoid
        fi
        
    popd

    pushd tests
        pip install --pre poppy-ergo-jr
        pip install -e ..[tests]
        python -m unittest discover
    popd
fi

set +x
set +e
