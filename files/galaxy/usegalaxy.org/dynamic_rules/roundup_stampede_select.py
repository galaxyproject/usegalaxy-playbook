##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

ROUNDUP_DESTINATION = 'roundup_multi'
ROUNDUP_DEVELOPMENT_DESTINATION = 'roundup_single_development'
STAMPEDE_DESTINATION = 'pulsar_stampede'
STAMPEDE_DEVELOPMENT_DESTINATION = 'pulsar_stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
VALID_DESTINATIONS = STAMPEDE_DESTINATIONS + (ROUNDUP_DESTINATION, ROUNDUP_DEVELOPMENT_DESTINATION) # WHY ARE WE SHOUTING
RESOURCE_KEYS = ('tacc_compute_resource',)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

def roundup_stampede_select( app, tool, job, user_email ):
    destination = None
    destination_id = ROUNDUP_DESTINATION

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )

    # Explcitly set the destination if the user has chosen to do so with the resource selector
    if '__job_resource' in param_dict and param_dict['__job_resource']['__job_resource__select'] == 'yes':
        resource_key = None
        for resource_key in param_dict['__job_resource'].keys():
            if resource_key in RESOURCE_KEYS:
                break
        else:
            log.warning('(%s) Stampede dynamic plugin did not find a valid resource key, keys were: %s', job.id, param_dict['__job_resource'].keys())
            raise JobMappingException( FAILURE_MESSAGE )

        destination_id = param_dict['__job_resource'][resource_key]
        if destination_id not in VALID_DESTINATIONS:
            log.warning('(%s) Stampede dynamic plugin got an invalid destination: %s', job.id, destination_id)
            raise JobMappingException( FAILURE_MESSAGE )

    log.debug("(%s) roundup_stampede_select dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id
