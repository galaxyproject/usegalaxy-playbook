#!/bin/bash
set -e

REPO=
BRANCH=
REMOTE=
OWNER=
REF=

OARGS="$@"

while getopts ":b:o:r:" opt; do
    case "$opt" in
        b)
            BRANCH="$OPTARG"
            ;;
        o)
            OWNER="$OPTARG"
            ;;
        r)
            REF="$OPTARG"
            ;;
        :)
            echo "Option missing argument: -$OPTARG" >&2
            exit 1
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

shift $((OPTIND -1))

REPO="$1"
if [ -z "$REPO" -o ! -e "/cvmfs/$REPO" ]; then
    echo "usage: $0 -b branch [-o owner] repo"
    echo "       $0 -r ref [-o owner] repo"
    exit 1
fi

if [ -z "IN_DOCKER" ]; then
    echo Re-executing in Docker with args: "$OARGS"
    exec docker run --rm -v /cvmfs:/cvmfs -v $0:$0:ro --user $(id -un) -e IN_DOCKER=1 galaxy/update $0 "$OARGS"
fi

case "$OWNER" in
    ''|galaxyproject)
        REMOTE=origin
        ;;
    *)
        REMOTE="$OWNER"
        if ! git remote show | grep -q "^$REMOTE\$"; then
            git remote add $OWNER https://github.com/$OWNER/galaxy.git
        fi
        ;;
esac

if [ -z "$BRANCH" -a -z "$REF" ]; then
    echo 'One of -b (branch) or -r (ref) are required'
    exit 1
elif [ -z "$REF" ]; then
    REF="${REMOTE}/${BRANCH}"
fi

cd /cvmfs/${REPO}/galaxy

. /cvmfs/${REPO}/venv/bin/activate
pip install --upgrade pip
git clean -dfx
git checkout -- .
git fetch ${REMOTE}
git checkout ${REF}
# run by Ansible
#/cvmfs/${REPO}/bin/makepyc.py lib
pip install --index-url=https://wheels.galaxyproject.org/simple --extra-index-url=https://pypi.python.org/simple -r requirements.txt
