#!/bin/bash
# adapted from .travis.yml
set -euo pipefail

function trap_handler() {
    [ -f ${TRAVIS_BUILD_DIR}/ansible.cfg.test-$$ ] && mv ${TRAVIS_BUILD_DIR}/ansible.cfg.test-$$ ${TRAVIS_BUILD_DIR}/ansible.cfg
}
trap "trap_handler" SIGTERM SIGINT ERR EXIT

GALAXY_VERSION=release_20.09

cd $(dirname $0)
TRAVIS_BUILD_DIR=$PWD
GALAXY_DIR=${TRAVIS_BUILD_DIR}/galaxy-${GALAXY_VERSION}

mv ${TRAVIS_BUILD_DIR}/ansible.cfg ${TRAVIS_BUILD_DIR}/ansible.cfg.test-$$
[ ! -d ${TRAVIS_BUILD_DIR}/.ansible-venv ] && python3 -m venv ${TRAVIS_BUILD_DIR}/.ansible-venv
[ ! -f ${TRAVIS_BUILD_DIR}/.ansible-venv/bin/ansible ] && ${TRAVIS_BUILD_DIR}/.ansible-venv/bin/pip install ansible

${TRAVIS_BUILD_DIR}/.ansible-venv/bin/ansible -i localhost, localhost -c local -m template \
    -a "src=${TRAVIS_BUILD_DIR}/env/common/templates/galaxy/config/job_router_conf.yml.j2 dest=${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/test/unit/job_router_conf.yml" \
    --extra-vars=@${TRAVIS_BUILD_DIR}/env/main/group_vars/galaxyservers/tools_conf.yml 
${TRAVIS_BUILD_DIR}/.ansible-venv/bin/ansible -i localhost, localhost -c local -m template \
    -a "src=${TRAVIS_BUILD_DIR}/env/common/templates/galaxy/config/job_conf.yml.j2 dest=${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/test/unit/job_conf.yml" \
    --extra-vars=@${TRAVIS_BUILD_DIR}/env/main/group_vars/galaxyservers/tools_conf.yml \
    --extra-vars=@${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/test/unit/mock_vars.yml
cp ${TRAVIS_BUILD_DIR}/env/common/files/galaxy/config/job_resource_params_conf.xml ${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/test/unit

if [ ! -d ${TRAVIS_BUILD_DIR}/galaxy-${GALAXY_VERSION} ]; then
    wget https://github.com/galaxyproject/galaxy/archive/${GALAXY_VERSION}.tar.gz
    tar xvzf ${GALAXY_VERSION}.tar.gz | tail
    cd ${GALAXY_DIR}
    export GALAXY_SKIP_CLIENT_BUILD=1
    sh scripts/common_startup.sh
    cd ${TRAVIS_BUILD_DIR}
fi

[ ! -d ${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/lib ] && mv ${GALAXY_DIR}/lib ${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/

set +u
source ${GALAXY_DIR}/.venv/bin/activate
set -u
[ ! -f ${GALAXY_DIR}/.venv/bin/pytest ] && pip install mock pytest

export PYTHONPATH=${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/lib/
cd ${TRAVIS_BUILD_DIR}/env/common/files/galaxy/dynamic_rules/test/

pytest -v  -s --log-level=debug
