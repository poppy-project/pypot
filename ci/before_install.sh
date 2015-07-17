 #!/bin/bash
set -x
set -e
echo "Running before_install.sh on $TRAVIS_OS_NAME"

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
    # Display os with more verbose than $TRAVIS_OS_NAME
    lsb_release -a

    # Download V-REP
    wget http://coppeliarobotics.com/V-REP_PRO_EDU_V${VREP_VERSION}_64_Linux.tar.gz
    tar -xzf V-REP_PRO_EDU_V${VREP_VERSION}_64_Linux.tar.gz
    mv ./V-REP_PRO_EDU_V${VREP_VERSION}_64_Linux $VREP_ROOT_DIR

    # Use miniconda python (provide binaries for scipy and numpy on Linux)
    if [[ "$PYTHON_VERSION" == "2.7" ]]; then
        curl -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh 
        export PATH=$HOME/miniconda/bin:$PATH

    else
        curl -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh 
        export PATH=/$HOME/miniconda3/bin:$PATH
    fi
elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then

    # Download V-REP
    wget http://coppeliarobotics.com/V-REP_PRO_EDU_V${VREP_VERSION}_Mac.zip
    unzip V-REP_PRO_EDU_V${VREP_VERSION}_Mac.zip
    mv ./V-REP_PRO_EDU_V${VREP_VERSION}_Mac $VREP_ROOT_DIR


    # Use miniconda python (provide binaries for scipy and numpy on Linux)
    if [[ "$PYTHON_VERSION" == "2.7" ]]; then
        curl -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda-latest-MacOSX-x86_64.sh
        export PATH=$HOME/miniconda/bin:$PATH
    else
        curl -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
        export PATH=$HOME/miniconda3/bin:$PATH
    fi
fi


chmod +x miniconda.sh
./miniconda.sh -b
conda update --yes -q conda
# conda create
# source activate condaenv
conda install --yes pip python=$PYTHON_VERSION numpy scipy matplotlib pyzmq flake8

# Upgrade pip
pip install pip --upgrade

# Show config
which python
which pip

# Remove useless outputs in STDOUT
set +x
