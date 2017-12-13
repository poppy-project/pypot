#!/bin/bash
set -e
set -x
echo "Running after_success_release.sh on $TRAVIS_OS_NAME"

echo "Installing wheel..."
pip install -q wheel || exit
echo "Installing twine..."
pip install -q twine || exit

echo "Creating distribution files..."
if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then

  python setup.py -q sdist bdist_wheel

  echo "Created the following distribution files:"
  ls -l dist

  # Test dist files
  for f in dist/*; do
    pip install "$f"
  done


elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
  python setup.py bdist_wheel || exit
  echo "Created the following distribution files:"
  ls -l dist

  # Test dist files
  for f in dist/*; do
    pip install "$f"
  done

fi

if [[ "$TRAVIS" == "true" ]]; then
  if [ "$TRAVIS_PULL_REQUEST" != "false" ] || [ "$TRAVIS_BRANCH" != "master" ]; then
    echo "This is an untrusted commit. No deployment will be done."
  else
    echo "Attempting to upload all distribution files to PyPi..."
    set +x
    set +e
    twine upload dist/* -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
  fi
fi
