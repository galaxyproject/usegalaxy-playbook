##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

BLACKLIGHT_NORMAL_DESTINATION = 'pulsar_blacklight_normal'
BLACKLIGHT_NORMAL_DESTINATIONS = (
        'pulsar_blacklight_normal16',
        'pulsar_blacklight_normal64',
        'pulsar_blacklight_normal128',
        'pulsar_blacklight_normal256')
BLACKLIGHT_DEVELOPMENT_DESTINATION = 'pulsar_blacklight_development'
BLACKLIGHT_DESTINATIONS = BLACKLIGHT_NORMAL_DESTINATIONS + (BLACKLIGHT_DEVELOPMENT_DESTINATION,)
VALID_DESTINATIONS = BLACKLIGHT_DESTINATIONS
RESOURCE_KEYS = ('blacklight_compute_resource',)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

def dynamic_blacklight_select( app, tool, job, user_email ):
    destination = None
    tool_id = tool.id
    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )
    
    if '__job_resource' in param_dict and param_dict['__job_resource']['__job_resource__select'] == 'yes':
        resource_key = None
        for resource_key in param_dict['__job_resource'].keys():
            if resource_key in RESOURCE_KEYS:
                break
        else:
            log.warning('(%s) Blacklight dynamic plugin did not find a valid resource key, keys were: %s', job.id, param_dict['__job_resource'].keys())
            raise JobMappingException( FAILURE_MESSAGE )

        destination_id = param_dict['__job_resource'][resource_key]
        if destination_id not in VALID_DESTINATIONS:
            log.warning('(%s) Blacklight dynamic plugin got an invalid destination: %s', job.id, destination_id)
            raise JobMappingException( FAILURE_MESSAGE )

        if destination_id in BLACKLIGHT_NORMAL_DESTINATIONS:
            cpus = destination_id[len(BLACKLIGHT_NORMAL_DESTINATION):]
            if int(cpus) >= 128:
                walltime = '72:00:00'
            else:
                walltime = '48:00:00'
            destination = app.job_config.get_destination(BLACKLIGHT_NORMAL_DESTINATION)
            destination.params['submit_native_specification'] += '-l walltime=%s -l ncpus=%s' % (walltime, cpus)
        elif destination_id == BLACKLIGHT_DEVELOPMENT_DESTINATION:
            destination = app.job_config.get_destination( BLACKLIGHT_DEVELOPMENT_DESTINATION )
    else:
        # default to 16 cpus in the regular queue
        destination = app.job_config.get_destination(BLACKLIGHT_NORMAL_DESTINATION)
        destination.params['submit_native_specification'] += ' -l ncpus=16'

    if destination is None:
        log.error('"(%s) blacklight_select dynamic plugin did not set a destination', job.id)
        raise JobMappingException( FAILURE_MESSAGE )

    log.debug("(%s) blacklight_select dynamic plugin returning '%s' destination", job.id, destination.id)
    log.debug("     submit_native_specification is: %s", destination.params['submit_native_specification'])
    return destination
