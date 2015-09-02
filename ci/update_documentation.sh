#!/bin/bash
set -e

# TODO parse online doc to see if it is the last version or not
pypot_src_version=$(python -c "import pypot; print (pypot.__version__)")
pypi_package_version=$(python ci/get_pypi_last_version.py pypot)
last_commit_sha=$(git rev-parse --short HEAD)
echo "Pypi version: "$pypi_package_version
echo "Source version: "$pypot_src_version

git config --global user.email $GIT_EMAIL
git config --global user.name $GIT_NAME
git_url=https://$GH_TOKEN@github.com/$GH_USERNAME/$GH_REPO.git
# Configure Git to push with GitHub Oauth token
# git remote set-url origin $git_url

# gevent is not python3 compatible, and apparently needed in osx zmq
# if [[ "$TRAVIS_OS_NAME" == "osx" ]] && [[ "$TRAVIS_PYTHON_VERSION" == "3.4" ]]; then
#     echo "Gevent bug, not possible to build zmq with"

# Install Sphinx
pip install -q Sphinx sphinxjp.themes.basicstrap bottle zerorpc

# Build the doc
pushd ..
    doc_src=./"$GH_REPO"/doc
    tmp_repo=/tmp/$GH_REPO-doc

    make -C $doc_src clean
    make -C $doc_src html
    make -C $doc_src latex
    if [ -d $tmp_repo ]; then
       rm -rf $tmp_repo/
    fi
    mkdir $tmp_repo
    git clone -b gh-pages $git_url $tmp_repo 
    cp -r $doc_src/_build/html/* $tmp_repo

    if [[ "TRAVIS_OS_NAME" == "linux" ]]; then
        # Using pdflatex to build the .tex files to pdf
        make -C $doc_src latexpdf
        cp $doc_src/_build/latex/Pypot.pdf $tmp_repo
    fi
    # Test http external links
    set +e
    make -C $doc_src linkcheck

    # Exit if commit is untrusted
    if [[ "$TRAVIS" == "true" ]]; then
        if [ "$TRAVIS_PULL_REQUEST" != "false" -o "$TRAVIS_BRANCH" != "master" ]; then
            echo "This is an untrusted commit. No deployment will be done."
        # elif [[ "$pypi_package_version" == "$pypot_src_version" ]]; then
        #     echo "Pypi version == source version, the doc won't be commited"
        else
            # If there is nothing to commit, it won't be considered as an error
            set +e
            # Push the new documentation only if it is not a pull request and we are on master
            pushd $tmp_repo
                git add -A
                git commit -m "Doc generated after commit $last_commit_sha (travis build #$TRAVIS_BUILD_NUMBER)"
                git push origin gh-pages --quiet
            popd
        fi
    fi
popd
