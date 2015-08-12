#!/bin/bash -xe

python3 --version
py.test-3.4 --version
python3 -mpep8 --version

# Target directory for all build files
BUILD=${1:-ci-build}
rm -rf ${BUILD}/
mkdir -p $BUILD

python3 -mpep8 --ignore E501 i3pystatus tests

# Check that the setup.py script works
rm -rf ${BUILD}/test-install ${BUILD}/test-install-bin
mkdir ${BUILD}/test-install ${BUILD}/test-install-bin
PYTHONPATH=${BUILD}/test-install python3 setup.py --quiet install --install-lib ${BUILD}/test-install --install-scripts ${BUILD}/test-install-bin

test -f ${BUILD}/test-install-bin/i3pystatus
test -f ${BUILD}/test-install-bin/i3pystatus-setting-util

PYTHONPATH=${BUILD}/test-install py.test-3.4 --junitxml ${BUILD}/testlog.xml tests

# Check that the docs build w/o warnings (-W flag)
sphinx-build-3.4 -b html -W docs ${BUILD}/docs/
