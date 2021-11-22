#!/bin/bash -xe

python3 --version
py.test --version
python3 -mpycodestyle --version

# Target directory for all build files
BUILD=${1:-ci-build}
rm -rf ${BUILD}/
mkdir -p $BUILD

python3 -mpycodestyle i3pystatus tests

# Check that the setup.py script works
rm -rf ${BUILD}/test-install{,-bin}
mkdir ${BUILD}/test-install{,-bin}
python3 setup.py install --quiet --install-lib ${BUILD}/test-install --install-scripts ${BUILD}/test-install-bin

test -f ${BUILD}/test-install-bin/i3pystatus
test -f ${BUILD}/test-install-bin/i3pystatus-setting-util

PYTHONPATH="$(echo ${BUILD}/test-install/i3pystatus-*.egg)" py.test -q --junitxml ${BUILD}/testlog.xml tests

# Check that the docs build w/o warnings (-W flag)
sphinx-build -Nq -b html -W docs ${BUILD}/docs/
