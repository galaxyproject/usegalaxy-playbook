##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import subprocess
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

# FIXME: reserved users
RESERVED_USERS = (
    'outreach@galaxyproject.org',
    'jen@bx.psu.edu',
    'anton@bx.psu.edu',
)
NORM_RESERVED_USERS = [ u.lower() for u in RESERVED_USERS ]
RESERVED_DESTINATION = 'reserved_multi'

JETSTREAM_DESTINATIONS = {
    'dynamic_jetstream_large': {
        'clusters': ['jetstream-iu', 'jetstream-tacc'],
        'cluster_prefixes': ['jetstream-iu-large', 'jetstream-tacc-large'],
        'partition': 'large',
    },
}

# Just needs to be a shell script, does not matter what it is
TEST_SCRIPT = '/usr/bin/ldd'


def __jetstream_rule(app, job, user_email, rule):
    destination = None
    destination_id = None

    if user_email is None:
        raise JobMappingException('Please log in to use this tool.')

    clusters = ','.join(JETSTREAM_DESTINATIONS[rule]['clusters'])
    native_specification = app.job_config.get_destination(rule).params.get('native_specification', '')
    sbatch_test_cmd = ['sbatch', '--test-only', '--clusters=%s' % clusters] + native_specification.split() + [TEST_SCRIPT]

    try:
        p = subprocess.Popen(sbatch_test_cmd, stderr=subprocess.PIPE)
        stderr = p.stderr.read()
        p.wait()
        assert p.returncode == 0, stderr
    except:
        log.exception('Error running sbatch test')
        raise JobMappingException('An error occurred while trying to schedule this job. Please retry it and if it continues to fail, report it to an administrator using the bug icon.')

    # There is a race condition here, of course. But I don't have a better solution.
    node = stderr.split()[-1]
    for i, prefix in enumerate(JETSTREAM_DESTINATIONS[rule]['cluster_prefixes']):
        if node.startswith(prefix):
            cluster = JETSTREAM_DESTINATIONS[rule]['clusters'][i]
            break
    else:
        log.error("Could not determine the cluster of node '%s', clusters are: '%s'", node, clusters)
        raise JobMappingException( 'An error occurred while trying to schedule this job. Please retry it and if it continues to fail, report it to an administrator using the bug icon.' )

    destination_id = '%s_%s' % (cluster.replace('-', '_'), JETSTREAM_DESTINATIONS[rule]['partition'])
    destination = app.job_config.get_destination(destination_id)

    log.debug("(%s) Jetstream dynamic plugin '%s' returning '%s' destination", job.id, rule, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id


def dynamic_jetstream_large( app, job, user_email ):
    return __jetstream_rule(app, job, user_email, 'dynamic_jetstream_large')
