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
# bwa                   params['reference_source']['reference_source_selector'] 'cached'
# bwa_mem               params['reference_source']['reference_source_selector'] 'cached'

# These are always sent to Stampede
# lastz_wrapper_2       params['source']['ref_source']              'cached'
# megablast_wrapper     no option, always cached
# bowtie_color_wrapper  same as bwa_wrapper
# bwa_color_wrapper     same as bowtie_wrapper

PUNT_TOOLS = ( 'bwa_wrapper', 'bowtie2', 'bowtie_wrapper', 'tophat', 'tophat2', 'bwa', 'bwa_mem' )
GENOME_SOURCE_PARAMS = ( 'genomeSource.refGenomeSource', 'reference_genome.source', 'refGenomeSource.genomeSource', 'reference_source.reference_source_selector' )
GENOME_SOURCE_VALUES = ( 'indexed', 'cached' )

LOCAL_DESTINATION = 'slurm_multi'
LOCAL_WALLTIME_DESTINATION = 'slurm_multi_dynamic_walltime'
LOCAL_DEVELOPMENT_DESTINATION = 'slurm_multi_development'
STAMPEDE_DESTINATION = 'pulsar_stampede_normal'
STAMPEDE_DEVELOPMENT_DESTINATION = 'pulsar_stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
JETSTREAM_DESTINATIONS = ('jetstream_large',)
VALID_DESTINATIONS = (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION) + STAMPEDE_DESTINATIONS + JETSTREAM_DESTINATIONS # WHY ARE WE SHOUTING
RESOURCES = {'tacc_compute_resource':VALID_DESTINATIONS, 'stampede_compute_resource':STAMPEDE_DESTINATIONS}
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

RESERVED_USERS = (
    'outreach@galaxyproject.org',
    'jen@bx.psu.edu',
    'anton@bx.psu.edu',
)
NORM_RESERVED_USERS = [ u.lower() for u in RESERVED_USERS ]
RESERVED_DESTINATION = 'reserved_multi'

TEAM_USERS = (
    'nate@bx.psu.edu',
    'anton@bx.psu.edu'
)
TEAM_DESTINATION = 'reserved_dynamic'

# collected with:
# python runtime_stats.py -c ./galaxy.ini -m 120 -M $((34 * 60 * 60)) --source=metrics --like

# times in minutes
RUNTIMES = {
    'bowtie_wrapper': {'runtime': 20.99, 'stddev': 58.85, 'devs': 2},
    'bowtie2': {'runtime': 31.61, 'stddev': 61.72, 'devs': 2},
    'bwa_wrapper': {'runtime': 69.41, 'stddev': 182.54, 'devs': 2},
    'bwa': {'runtime': 41.13, 'stddev': 90.08, 'devs': 2},
    'bwa_mem': {'runtime': 40.64, 'stddev': 126.94, 'devs': 2},
    'tophat': {'runtime': 141.93, 'stddev': 244.24, 'devs': 2},
    'tophat2': {'runtime': 138.66, 'stddev': 232.86, 'devs': 2},
    'cufflinks': {'runtime': 43.44, 'stddev': 100.78, 'devs': 2},
    'cuffdiff': {'runtime': 101.57, 'stddev': 195.03, 'devs': 2},
    'cuffmerge': {'runtime': 5.36, 'stddev': 15.18, 'devs': 4},
    #'cuffnorm': {'runtime': 44.73, 'stddev': 157.20, 'devs': 2},
    #'cuffquant': {'runtime': 44.73, 'stddev': 157.20, 'devs': 2},
    #'stringtie': {'runtime': 165.47, 'stddev': 286.19, 'devs': 2},
}

def __rule( app, tool, job, user_email, resource ):
    destination = None
    destination_id = LOCAL_DESTINATION
    tool_id = tool.id

    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )
    
    # Explcitly set the destination if the user has chosen to do so with the resource selector
    if '__job_resource' in param_dict:
        if param_dict['__job_resource']['__job_resource__select'] == 'yes':
            resource_key = None
            for resource_key in param_dict['__job_resource'].keys():
                if resource_key == resource:
                    destination_id = param_dict['__job_resource'][resource_key]
                    if destination_id in RESOURCES[resource_key]:
                        break
                    elif destination_id == TEAM_DESTINATION:
                        break
                    else:
                        log.warning('(%s) Destination/walltime dynamic plugin got an invalid destination: %s', job.id, destination_id)
                        raise JobMappingException( FAILURE_MESSAGE )
            else:
                log.warning('(%s) Destination/walltime dynamic plugin got an invalid value for selector: %s', job.id, param_dict['__job_resource']['__job_resource__select'])
                raise JobMappingException( FAILURE_MESSAGE )
        elif param_dict['__job_resource']['__job_resource__select'] == 'no':
            destination_id = RESOURCES[resource][0]
            if user_email.lower() in NORM_RESERVED_USERS:
                log.info("(%s) Destination/walltime dynamic plugin returning default reserved destination for '%s'", job.id, user_email)
                return RESERVED_DESTINATION
        else:
            log.warning('(%s) Destination/walltime dynamic plugin did not find a valid resource key, keys were: %s', job.id, param_dict['__job_resource'].keys())
            raise JobMappingException( FAILURE_MESSAGE )
    else:
        log.warning('(%s) Destination/walltime dynamic plugin did not receive the __job_resource param, keys were: %s', job.id, param_dict.keys())
        raise JobMappingException( FAILURE_MESSAGE )

    if destination_id == TEAM_DESTINATION:
        if user_email in TEAM_USERS:
            destination_id = TEAM_DESTINATION
            destination = app.job_config.get_destination( TEAM_DESTINATION )
            destination.params['nativeSpecification'] += ' --ntasks=%s' % param_dict['__job_resource']['team_cpus']
        else:
            log.warning("(%s) Unauthorized user '%s' selected team development destination", job.id, user_email)
            destination_id = LOCAL_DESTINATION

    # Only allow stampede if a cached reference is selected
    if destination_id in STAMPEDE_DESTINATIONS and tool_id in PUNT_TOOLS:
        for p in GENOME_SOURCE_PARAMS:
            subpd = param_dict.copy()
            # walk the param dict
            try:
                for i in p.split('.'):
                    subpd = subpd[i]
                assert subpd in GENOME_SOURCE_VALUES
                log.info('(%s) Destination/walltime dynamic plugin detected indexed reference selected, job will be sent to Stampede', job.id)
                break
            except:
                pass
        else:
            log.info('(%s) User requested Stampede but destination/walltime dynamic plugin did not detect selection of an indexed reference, job will be sent to local cluster instead', job.id)
            if destination_id == STAMPEDE_DEVELOPMENT_DESTINATION:
                destination_id = LOCAL_DEVELOPMENT_DESTINATION
            else:
                destination_id = LOCAL_DESTINATION

    # Set a walltime if local is the destination and this is a dynamic walltime tool
    if destination_id == LOCAL_DESTINATION and tool_id in RUNTIMES:
        destination_id = LOCAL_WALLTIME_DESTINATION
        #walltime = datetime.timedelta(seconds=(RUNTIMES[tool_id]['runtime'] + (RUNTIMES[tool_id]['stddev'] * RUNTIMES[tool_id]['devs'])) * 60)
        walltime = '36:00:00'
        destination = app.job_config.get_destination( LOCAL_WALLTIME_DESTINATION ) 
        destination.params['nativeSpecification'] += ' --time=%s' % str(walltime).split('.')[0]

    log.debug("(%s) Destination/walltime dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id

def dynamic_local_stampede_select_dynamic_walltime( app, tool, job, user_email ):
    return __rule( app, tool, job, user_email, 'tacc_compute_resource' )

def dynamic_stampede_select( app, tool, job, user_email ):
    return __rule( app, tool, job, user_email, 'stampede_compute_resource' )
