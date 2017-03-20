#!/bin/sh

GALAXY_INSTANCE=main

. /cvmfs/${GALAXY_INSTANCE}.galaxyproject.org/venv/bin/activate
cd /cvmfs/${GALAXY_INSTANCE}.galaxyproject.org/galaxy
python ./scripts/paster.py serve /srv/galaxy/${GALAXY_INSTANCE}/config/galaxy.ini --server-name=${GALAXY_INSTANCE}_installer
