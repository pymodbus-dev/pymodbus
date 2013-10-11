#!/bin/bash
# ------------------------------------------------------------------ #
# This script is used to test that we can create a virtual
# environment and install the latest version of the given package
# from pypi.
# ------------------------------------------------------------------ #
ENVIRONMENT="example"
PACKAGE="pymodbus"

# ------------------------------------------------------------------ #
# preflight tests
# ------------------------------------------------------------------ #
if [[ "`which pip`" != "" ]]; then
    INSTALL="pip install -qU"
elif [[ "`which easy_install`" != "" ]]; then
    INSTALL="easy_install -qU"
else
    echo -e "\E[31m"
    echo "\E[31mPlease install distutils before continuing"
    echo "wget http://peak.telecommunity.com/dist/ez_setup.py | sudo python"
    echo -e "\E[0m"
    exit -1
fi

if [[ "`which virtualenv`" == "" ]]; then
    echo -e "\E[31m"
    echo "Please install virtualenv before continuing"
    echo "sudo easy_install virtualenv"
    echo -e "\E[0m"
    exit -1
fi

# ------------------------------------------------------------------ #
# setup test
# ------------------------------------------------------------------ #
echo -n "Setting up test..."
virtualenv -q --no-site-packages --distribute ${ENVIRONMENT}
source ${ENVIRONMENT}/bin/activate
echo -e "\E[32mPassed\E[0m"

# ------------------------------------------------------------------ #
# install test
# ------------------------------------------------------------------ #
echo -n "Testing package installation..."
${INSTALL} ${PACKAGE}
if [[ "$?" == "0" ]]; then
    echo -e "\E[32mPassed\E[0m"
else
    echo -e "\E[31mPassed\E[0m"
fi

# ------------------------------------------------------------------ #
# library test
# ------------------------------------------------------------------ #
echo -n "Testing python version..."
python -c "import pymodbus;print pymodbus.version.version"
if [[ "$?" == "0" ]]; then
    echo -e "\E[32mPassed\E[0m"
else
    echo -e "\E[31mPassed\E[0m"
fi

# ------------------------------------------------------------------ #
# cleanup test
# ------------------------------------------------------------------ #
echo -n "Tearing down test..."
deactivate
rm -rf ${ENVIRONMENT}
echo -e "\E[32mPassed\E[0m"
