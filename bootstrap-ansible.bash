#!/bin/bash

# TODO: Update this to use virtualenv-burrito, which is pretty great.

# If you want completely hands-off installation of Ansible you can use this
# script to bootstrap an environment. Does not require root unless you need
# python headers or a compiler.

VENV_SRC='https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz'

function fetch_virtualenv () {
    echo "Fetching virtualenv" >&2
    tmp=`mktemp -d -t XXXXXXX`
    file=`basename $VENV_SRC`
    dir=`basename $VENV_SRC .tar.gz`
    if type wget &>/dev/null; then
        wget -O $tmp/$file $VENV_SRC >&2 || exit 1
    elif type curl &>/dev/null; then
        curl -o $tmp/$file $VENV_SRC >&2 || exit 1
    else
        echo "Install virtualenv, wget or curl" >&2
        exit 1
    fi
    tar zxf $tmp/$file -C $tmp
    echo "$tmp/$dir/virtualenv.py"
}

function pip_failure () {
    echo ""
    echo "Installing virtualenv or Ansible via pip failed. This script does not try very"
    echo "hard to figure out why, but typically this is due to missing build"
    echo "dependencies. If anything could be determined, it is shown here:"
    echo ""

    case `uname -s` in
        Darwin)
            if ! type gcc &>/dev/null; then
                echo "You do not have a compiler. Install XCode and try again."
            fi
            ;;
        Linux)
            if [ -f /etc/redhat-release -o -f /etc/centos-release ]; then
                if ! rpm -q --quiet python-devel; then
                    echo "You are missing the Python development pacakge, try installing it with:"
                    echo "$ sudo yum install python-devel"
                fi
            elif [ -f /etc/SuSE-release ]; then
                # I have no way to test this
                if ! rpm -q --quiet python-devel; then
                    echo "You are missing the Python development pacakge, try installing it with:"
                    echo "$ sudo zypper install python-devel"
                fi
            elif [ -f /etc/debian_version ]; then
                if ! dpkg --status python-dev &>/dev/null; then
                    echo "You are missing the Python development package, try installing it with:"
                    echo "$ sudo apt-get install python-dev"
                fi
            fi
            ;;
    esac

    exit 1
}

: ${ANSIBLE_VENV:=$HOME/.ansible-venv}

if [ ! -d "$ANSIBLE_VENV" ]; then
    echo "Ansible will be installed in: $ANSIBLE_VENV"
    virtualenv=virtualenv
    if ! type virtualenv &>/dev/null; then
        virtualenv=`fetch_virtualenv`
    fi
    $virtualenv $ANSIBLE_VENV || exit 1
fi

$ANSIBLE_VENV/bin/pip install virtualenv ansible || pip_failure

if [ -f "$ANSIBLE_VENV/bin/ansible" ]; then
    echo 'Ansible is installed. To add it to $PATH, execute:'
    echo "$ source $ANSIBLE_VENV/bin/activate"
fi
