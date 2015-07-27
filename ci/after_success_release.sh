#!/bin/bash
set -e
set -x
echo "Running after_success_release.sh on $TRAVIS_OS_NAME"

# Exit if commit is untrusted
if [[ "$TRAVIS" == "true" ]]; then
    if [ "$TRAVIS_PULL_REQUEST" != "false" -o "$TRAVIS_BRANCH" != "master" ]; then
        echo "This is an untrusted commit. No deployment will be done."
    else
        echo "Installing wheel..."
        pip install -q wheel --user || exit
        echo "Installing twine..."
        pip install -q twine --user || exit

        echo "Creating distribution files..."
        if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then

            # remove error on python 3.4
            # ValueError: invalid prefix: filename '/home/travis/miniconda3/lib/python3.4/site-packages/pypot/__init__.py' doesn't start with 'build/bdist.linux-x86_64/dumb'
            if [[ "$TRAVIS_PYTHON_VERSION" == "3.4" ]];then
                set +e
            fi
            # This release build creates the source distribution. All other release builds
            # should not.
            python setup.py -q sdist bdist_egg

            echo "Created the following distribution files:"
            ls -l dist
            # These should get created on linux:
            # ...-cp27-none-linux-x86_64.whl
            # ....linux-x86_64.tar.gz
            # ...-py2.7-linux-x86_64.egg
            # ....tar.gz
            
            set +x
            set +e
            # Test dist files
            for f in dist/*; do 
                pip install $f 
            done
            echo "Uploading Linux egg to PyPi..."
            twine upload dist/*.egg -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
            echo "Uploading source package to PyPi..."
            twine upload dist/*.tar.gz -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"

            # We can't upload the wheel to PyPi because PyPi rejects linux platform wheel
            # files.
            # See: https://bitbucket.org/pypa/pypi-metadata-formats/issue/15/enhance-the-platform-tag-definition-for

        elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
            python setup.py bdist bdist_wheel || exit
            echo "Created the following distribution files:"
            ls -l dist
            set +x
            set +e
            # Test dist files
            for f in dist/*; do 
                pip install $f 
            done
            echo "Uploading OS X egg to PyPi..."
            twine upload dist/*.egg -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
            echo "Uploading OS X Wheel package to PyPi..."
            twine upload dist/*.whl -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"

            echo "Attempting to upload all distribution files to PyPi..."
            twine upload dist/* -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
        fi
    fi
fi

