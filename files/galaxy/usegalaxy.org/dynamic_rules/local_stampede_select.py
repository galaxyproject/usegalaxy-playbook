##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

# bwa_wrapper           params['genomeSource']['refGenomeSource']   'indexed'
# bowtie2               params['reference_genome']['source']        'indexed'
# bowtie_wrapper        params['refGenomeSource']['genomeSource']   'indexed'
# tophat                params['refGenomeSource']['genomeSource']   'indexed'
# tophat2               params['refGenomeSource']['genomeSource']   'indexed'
# lastz_wrapper_2       params['source']['ref_source']              'cached'
# megablast_wrapper     no option, always cached

PUNT_TOOLS = ( 'bwa_wrapper', 'bowtie2', 'bowtie_wrapper', 'tophat', 'tophat2', 'lastz_wrapper_2' )
GENOME_SOURCE_PARAMS = ( 'genomeSource.refGenomeSource', 'reference_genome.source', 'refGenomeSource.genomeSource', 'source.ref_source' )
GENOME_SOURCE_VALUES = ( 'indexed', 'cached' )

LOCAL_DESTINATION = 'slurm_multi'
LOCAL_DEVELOPMENT_DESTINATION = 'slurm_multi_development'
STAMPEDE_DESTINATION = 'pulsar_stampede'
STAMPEDE_DEVELOPMENT_DESTINATION = 'pulsar_stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
VALID_DESTINATIONS = STAMPEDE_DESTINATIONS + (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION) # WHY ARE WE SHOUTING
RESOURCE_KEYS = ('tacc_compute_resource',)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

RESERVED_USERS = (
    'usinggalaxy2@gmail.com',
)
RESERVED_DESTINATION = 'reserved_multi'

def dynamic_local_stampede_select( app, tool, job, user_email ):
    destination = None
    destination_id = LOCAL_DESTINATION
    tool_id = tool.id

    if user_email in RESERVED_USERS:
        return RESERVED_DESTINATION

    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

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

    # Only allow stampede if a cached reference is selected
    if destination_id in STAMPEDE_DESTINATIONS and tool_id in PUNT_TOOLS:
        for p in GENOME_SOURCE_PARAMS:
            subpd = param_dict.copy()
            # walk the param dict
            try:
                for i in p.split('.'):
                    subpd = subpd[i]
                assert subpd in GENOME_SOURCE_VALUES
                log.info('(%s) Stampede dynamic plugin detected indexed reference selected, job will be sent to Stampede', job.id)
                break
            except:
                pass
        else:
            log.info('(%s) User requested Stampede but Stampede dynamic plugin did not detect selection of an indexed reference, job will be sent to Roundup instead', job.id)
            if destination_id == STAMPEDE_DEVELOPMENT_DESTINATION:
                destination_id = LOCAL_DEVELOPMENT_DESTINATION
            else:
                destination_id = LOCAL_DESTINATION

    log.debug("(%s) dynamic_local_stampede_select dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id
