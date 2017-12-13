#!/bin/bash
set -x
set -e
echo "Running before_install.sh on $TRAVIS_OS_NAME"
echo "Checking OS : PWD = $PWD, HOME=$HOME"

# Keept for hystory, not used anymore
if [[ -n "$SSH_VREP_SERVER" ]]; then
  set +x
  set -e
  rm -r ~/.ssh
  mkdir ~/.ssh
  # Decrypt ssh private key
  openssl aes-256-cbc -k $id_rsa_encrypted_key -in ci/id_rsa.enc -out ci/id_rsa.out -d -v
  cp ci/known_hosts ~/.ssh/known_hosts
  cp ci/id_rsa.out ~/.ssh/id_rsa
  chmod 700 ~/.ssh/id_rsa
  chmod 700 ci/id_rsa.out
  echo -e "Host *.ci \n ProxyCommand ssh tseg001@ci-ssh.inria.fr \"/usr/bin/nc \`basename %h .ci\` %p\" \n UserKnownHostsFile=/dev/null\n StrictHostKeyChecking=no" > ~/.ssh/config
  echo "Starting SSH proxy daemon"
  ssh -i ci/id_rsa.out -t -t -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -N -L 19997:localhost:19997 ci@"$SSH_VREP_SERVER" &
  sleep 5
  set -x
fi

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
  # Display os with more verbose than $TRAVIS_OS_NAME
  lsb_release -a
  # Travis use automatically virtualenv version of python

  # # Use miniconda python (provide binaries for scipy and numpy on Linux)
  # if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  #     curl -L -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
  # else
  #     curl -L -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
  # fi
elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then

  echo "Removing homebrew from Travis CI to avoid conflicts."
  curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/uninstall > ~/uninstall_homebrew
  chmod +x ~/uninstall_homebrew
  ~/uninstall_homebrew -fq
  rm ~/uninstall_homebrew

  # Use miniconda python (provide binaries for scipy and numpy on Linux)
  if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
    curl -L -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh
  else
    curl -L -o miniconda.sh http://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
  fi


  chmod +x miniconda.sh
  ./miniconda.sh -b -p $HOME/miniconda
  # Install python version corresponding to travis setting
  $HOME/miniconda/bin/conda config --set always_yes yes --set changeps1 no
  $HOME/miniconda/bin/conda create --name=travis python=$TRAVIS_PYTHON_VERSION

  # Use travis conda env as default
  export PATH=$HOME/miniconda/envs/travis/bin:$PATH
  hash -r

  conda update -q conda

  # conda create
  # source activate condaenv
  conda install --yes pip python=$TRAVIS_PYTHON_VERSION

  # Show config
  which python
  which pip

  # Remove useless outputs in STDOUT
  set +x
fi
