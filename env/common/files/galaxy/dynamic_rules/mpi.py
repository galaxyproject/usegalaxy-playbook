##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

DEFAULT_DESTINATION = 'slurm_mpi_multi'
VALID_DESTINATIONS = (
    DEFAULT_DESTINATION,
    'slurm_mpi_multi_development',
    'stampede_mpi_normal',
    'stampede_mpi_skx_normal',
    'stampede_mpi_development',
    'stampede_mpi_skx_development',
)
MAX_WALLTIMES = {
    ''
    }
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'


def __parse_resource_selector(param_dict):
    # handle job resource parameters
    try:
        # validate params
        cores = int(param_dict['__job_resource']['cores'])
        time = int(param_dict['__job_resource']['time'])
        destination_id = param_dict['__job_resource']['tacc_compute_resource_advanced']
        assert destination_id in VALID_DESTINATIONS
        return (cores, time, destination_id)
    except:
        # resource param selector not sent with tool form, job_conf.xml misconfigured
        log.exception('(%s) job resource error, keys were: %s', job.id, param_dict.keys())
        raise JobMappingException(FAILURE_MESSAGE)



def dynamic_mpi(app, job):
    cores = 6
    time = 24
    destination_id = DEFAULT_DESTINATION
    destination = None
    native_spec_param = 'submit_native_specification'

    # build the param dictionary
    param_dict = job.get_param_values(app)

    if param_dict.get('__job_resource', {}).get('__job_resource__select') != 'yes':
        log.debug("Job resource parameters not seleted, using default destination: %s", destination_id)
    else:
        cores, time, destination_id = __parse_resource_selector(param_dict)

    if destination_id.startswith('slurm_mpi_'):
        native_spec_param = 'nativeSpecification'

    if destination_id.startswith('stampede_mpi_skx_'):
        cores = min(cores, 48)
    elif destination_id.startswith('stampede_mpi_'):
        cores = min(cores, 272)
    elif destination_id == 'slurm_mpi_multi_development':
        cores = 1
    else:
        # slurm_mpi_multi
        cores = min(cores, 6)

    if destination_id.endswith('_development'):
        time = min(time, 2)
    elif destination_id == 'slurm_mpi_multi':
        time = min(time, 24)
    else:
        # normal stampede destinations
        time = min(time, 48)

    destination = app.job_config.get_destination(destination_id)

    # stampede_mpi_* dests already contain: --account=TG-MCB140147 --partition=... --nodes=1
    # slurm_mpi_* dests already contains: --partition=... --nodes=1
    params = [
        '--ntasks={}'.format(cores),
        '--time={}:00:00'.format(time),
    ]
    destination.params[native_spec_param] += ' ' + ' '.join(params)

    log.info('(%s) returning destination: %s', job.id, destination_id)
    log.info('(%s) native specification: %s', job.id, destination.params.get(native_spec_param))
    return destination
