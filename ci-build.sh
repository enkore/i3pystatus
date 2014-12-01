#!/bin/bash -xe

# Target directory for all build files
BUILD=${1:-ci-build}
mkdir -p $BUILD

pep8 --ignore E501 i3pystatus tests

PYTHONPATH=. py.test --junitxml ${BUILD}/testlog.xml tests

# Check that the setup.py script works
rm -rf ${BUILD}/test-install ${BUILD}/test-install-bin
mkdir ${BUILD}/test-install ${BUILD}/test-install-bin
PYTHONPATH=${BUILD}/test-install python setup.py --quiet install --install-lib ${BUILD}/test-install --install-scripts ${BUILD}/test-install-bin

test -f ${BUILD}/test-install-bin/i3pystatus

# Check that the docs build w/o warnings (-W flag)
sphinx-build -b html -W docs ${BUILD}/docs/


