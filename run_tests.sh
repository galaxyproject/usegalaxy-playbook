#!/bin/bash
set -euo pipefail

function trap_handler() {
    rc=$?
    [ -f ${GITHUB_WORKSPACE}/ansible.cfg.test-$$ ] && mv ${GITHUB_WORKSPACE}/ansible.cfg.test-$$ ${GITHUB_WORKSPACE}/ansible.cfg
    exit $rc
}
trap "trap_handler" SIGTERM SIGINT ERR EXIT

GALAXY_VERSION=release_20.09

if [ -z "${GITHUB_WORKSPACE:-}" ]; then
    cd $(dirname $0)
    GITHUB_WORKSPACE=$PWD
fi
GALAXY_DIR=${GITHUB_WORKSPACE}/galaxy-${GALAXY_VERSION}

function setup_tests() {

    mv ${GITHUB_WORKSPACE}/ansible.cfg ${GITHUB_WORKSPACE}/ansible.cfg.test-$$
    [ ! -d ${GITHUB_WORKSPACE}/.ansible-venv ] && python3 -m venv ${GITHUB_WORKSPACE}/.ansible-venv
    [ ! -f ${GITHUB_WORKSPACE}/.ansible-venv/bin/ansible ] && ${GITHUB_WORKSPACE}/.ansible-venv/bin/pip install ansible

    ${GITHUB_WORKSPACE}/.ansible-venv/bin/ansible -i localhost, localhost -c local -m template \
        -a "src=${GITHUB_WORKSPACE}/env/common/templates/galaxy/config/job_router_conf.yml.j2 dest=${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/test/unit/job_router_conf.yml" \
        --extra-vars=@${GITHUB_WORKSPACE}/env/main/group_vars/galaxyservers/tools_conf.yml 
    ${GITHUB_WORKSPACE}/.ansible-venv/bin/ansible -i localhost, localhost -c local -m template \
        -a "src=${GITHUB_WORKSPACE}/env/common/templates/galaxy/config/job_conf.yml.j2 dest=${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/test/unit/job_conf.yml" \
        --extra-vars=@${GITHUB_WORKSPACE}/env/main/group_vars/galaxyservers/tools_conf.yml \
        --extra-vars=@${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/test/unit/mock_vars.yml
    cp ${GITHUB_WORKSPACE}/env/common/files/galaxy/config/job_resource_params_conf.xml ${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/test/unit

    if [ ! -d ${GITHUB_WORKSPACE}/galaxy-${GALAXY_VERSION} ]; then
        wget https://github.com/galaxyproject/galaxy/archive/${GALAXY_VERSION}.tar.gz
        tar xvzf ${GALAXY_VERSION}.tar.gz | tail
        cd ${GALAXY_DIR}
        export GALAXY_SKIP_CLIENT_BUILD=1
        sh scripts/common_startup.sh
        cd ${GITHUB_WORKSPACE}
    fi

    [ ! -d ${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/lib ] && mv ${GALAXY_DIR}/lib ${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/

    [ ! -f ${GALAXY_DIR}/.venv/bin/pytest ] && ${GALAXY_DIR}/.venv/bin/pip install mock pytest

}

function run_tests() {

    export PYTHONPATH=${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/lib/
    cd ${GITHUB_WORKSPACE}/env/common/files/galaxy/dynamic_rules/test/

    ${GALAXY_DIR}/.venv/bin/pytest -v  -s --log-level=debug

}


case "${1:-}" in
    setup)
        setup_tests
        ;;
    run)
        run_tests
        ;;
    '')
        setup_tests
        run_tests
        ;;
    *)
        echo "usage: run_tests.sh [setup|run]" >&2
        exit 1
        ;;
esac
