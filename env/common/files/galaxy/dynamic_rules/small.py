##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##
from __future__ import absolute_import

from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)
# fix for until we switch to yaml config
log.setLevel(logging.DEBUG)


RESOURCE_KEY = 'small_resource'
RESOURCES = {
    'roundup': None,
    'jetstream': None,
}
NATIVE_SPEC_PARAMS = None
TEST_SCRIPT = '/usr/bin/ldd'


def __resource(params, key, valid):
    # resource_params is guaranteed to be a dict
    resource = params.get(key)
    if resource and resource not in valid:
        log.warning('(%s) dynamic rule got an invalid resource: %s', job.id, resource)
        raise JobMappingException('An invalid resource was selected')
    return resource


def __native_param_name(app, name):
    if NATIVE_SPEC_PARAMS is None:
        global NATIVE_SPEC_PARAMS
        NATIVE_SPEC_PARAMS = {}
        for runner in app.job_config.runner_plugins:
            NATIVE_SPEC_PARAMS[runner['id']] = (
                'native_specification' if runner['load'].startswith('galaxy.jobs.runners.pulsar')
                                       else 'nativeSpecification'
            )
    return NATIVE_SPEC_PARAMS[name]['load']


def dynamic_small(app, job, resource_params):
    param_dict = job.get_param_values(app)

    # Explcitly set the destination if the user has chosen to do so with the resource selector
    resource = __resource(resource_params, RESOURCE_KEY, RESOURCES.keys())
    explicit = resource is not None

    # roundup: --partition=normal --nodes=1 --ntasks=1 --mem=4096 --time=...
    # jetstream: --partition=small --time=...

    native = app.job_config.get_destination(test_destination_id).params.get('native_specification', '')
    sbatch_test_cmd = ['sbatch', '--test-only', '--clusters=%s' % clusters] + native.split() + [TEST_SCRIPT]

    '''
    else:
        # if __job_resource is not passed or __job_resource_select is not set to a "yes-like" value, resource_params is an empty dict
        if user_email.lower() in NORM_RESERVED_USERS:
            log.info("(%s) Destination/walltime dynamic plugin returning default reserved destination for '%s'", job.id, user_email)
            #return RESERVED_DESTINATION
            destination_id = RESERVED_DESTINATION
            explicit_destination = True
    '''

