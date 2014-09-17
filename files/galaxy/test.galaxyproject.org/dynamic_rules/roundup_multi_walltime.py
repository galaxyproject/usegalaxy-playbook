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

# On Test, these are always sent to Stampede and thus use the stampede destination directly
# lastz_wrapper_2       params['source']['ref_source']              'cached'
# megablast_wrapper     no option, always cached

PUNT_TOOLS = ( 'bwa_wrapper', 'bowtie2', 'bowtie_wrapper', 'tophat', 'tophat2' )
GENOME_SOURCE_PARAMS = ( 'genomeSource.refGenomeSource', 'reference_genome.source', 'refGenomeSource.genomeSource' )
GENOME_SOURCE_VALUES = ( 'indexed', )

ROUNDUP_DESTINATION = 'roundup_multi'
ROUNDUP_DEVELOPMENT_DESTINATION = 'roundup_single_development'
STAMPEDE_DESTINATION = 'pulsar_stampede'
STAMPEDE_DEVELOPMENT_DESTINATION = 'pulsar_stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
VALID_DESTINATIONS = STAMPEDE_DESTINATIONS + (ROUNDUP_DESTINATION, ROUNDUP_DEVELOPMENT_DESTINATION) # WHY ARE WE SHOUTING
RESOURCE_KEYS = ('tacc_compute_resource', 'stampede_compute_resource')
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

# in minutes
RUNTIMES = {
    'bowtie_wrapper': {'runtime': 19.75, 'stddev': 65.27},
    'bwa_wrapper': {'runtime': 51.47, 'stddev': 157.78},
    'bowtie2': {'runtime': 28.23, 'stddev': 45.48},
    'cuffdiff': {'runtime': 108.27, 'stddev': 258.30},
    'tophat': {'runtime': 152.69, 'stddev': 295.26},
    'tophat2': {'runtime': 165.47, 'stddev': 286.19},
    'cufflinks': {'runtime': 44.73, 'stddev': 157.20},
    'cuffmerge': {'runtime': 35.07, 'stddev': 181.65}
}
DEVS = 0

def roundup_multi_dynamic_walltime( app, tool, job, user_email ):
    destination = None
    destination_id = ROUNDUP_DESTINATION
    tool_id = tool.id
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
                destination_id = ROUNDUP_DEVELOPMENT_DESTINATION
            else:
                destination_id = ROUNDUP_DESTINATION

    # Set a walltime if the roundup_multi is the destination
    if destination_id == ROUNDUP_DESTINATION:
        if tool_id not in RUNTIMES:
            log.error('(%s) Invalid tool for this dynamic rule: %s', job.id, tool_id)
            raise JobMappingException( FAILURE_MESSAGE )

        walltime = datetime.timedelta(seconds=(RUNTIMES[tool_id]['runtime'] + (RUNTIMES[tool_id]['stddev'] * DEVS)) * 60)
        destination = app.job_config.get_destination( ROUNDUP_DESTINATION ) 
        destination.params['nativeSpecification'] += ' --time=%s' % str(walltime).split('.')[0]

    log.debug("(%s) slurm_multi_dynamic_walltime dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id
