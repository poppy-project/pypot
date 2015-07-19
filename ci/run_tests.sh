#!/bin/bash
set +x

# Pep8 tests
set +e
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
echo " Display  poppy.get_object_position('pelvis_visual')"
if [[ "$USE_SSH_FORWARDING" == "true" ]]; then
    if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
        sudo apt-get install -qq --yes proxychains
        proxychains python ci/test_vrep.py
    else
        brew install proxychains-ng
        proxychains4 python ci/test_vrep.py
    fi
# else
#     pushd $VREP_ROOT_DIR/
#         if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
#             xvfb-run --auto-servernum --server-num=1 ./vrep.sh -h  &
#         else
#             ./vrep.app/Contents/MacOS/vrep -h  &
#         fi
#         sleep 10
#     popd
#     python ci/test_vrep.py
    
fi


set +x
set +e



