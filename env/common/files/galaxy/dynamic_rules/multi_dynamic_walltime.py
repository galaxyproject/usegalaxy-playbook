##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import os
import datetime
import logging
import re
import subprocess
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)
# fix for until we switch to yaml config
log.setLevel(logging.DEBUG)

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

JETSTREAM_TOOLS = ( 'bowtie2', 'bwa', 'bwa_mem', 'tophat2', 'cufflinks', 'rna_star' )
PUNT_TOOLS = ( 'bwa_wrapper', 'bowtie2', 'bowtie_wrapper', 'tophat', 'tophat2', 'bwa', 'bwa_mem' )
GENOME_SOURCE_PARAMS = ( 'genomeSource.refGenomeSource', 'reference_genome.source', 'refGenomeSource.genomeSource', 'reference_source.reference_source_selector' )
GENOME_SOURCE_VALUES = ( 'indexed', 'cached' )

LOCAL_DESTINATION = 'slurm_multi'
LOCAL_WALLTIME_DESTINATION = 'slurm_multi_dynamic_walltime'
LOCAL_DEVELOPMENT_DESTINATION = 'slurm_multi_development'
STAMPEDE_DESTINATION = 'stampede_normal'
STAMPEDE_DEVELOPMENT_DESTINATION = 'stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
BRIDGES_DESTINATION = 'bridges_normal'
BRIDGES_DEVELOPMENT_DESTINATION = 'bridges_development'
BRIDGES_DESTINATIONS = (BRIDGES_DESTINATION, BRIDGES_DEVELOPMENT_DESTINATION)
JETSTREAM_DESTINATIONS = ('jetstream_multi',)
VALID_DESTINATIONS = (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION) + STAMPEDE_DESTINATIONS + JETSTREAM_DESTINATIONS # WHY ARE WE SHOUTING
RESOURCES = {
    'tacc_compute_resource': VALID_DESTINATIONS,
    'multi_bridges_compute_resource': (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION) + JETSTREAM_DESTINATIONS + BRIDGES_DESTINATIONS,
    'stampede_compute_resource': STAMPEDE_DESTINATIONS,
}
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

JETSTREAM_DESTINATION_MAPS = {
    LOCAL_DESTINATION: {
        'clusters': ['jetstream-iu', 'jetstream-tacc', 'roundup'],
        'cluster_prefixes': ['jetstream-iu-large', 'jetstream-tacc-large', 'roundup'],
        'destination_prefixes': ['jetstream_iu', 'jetstream_tacc', 'slurm'],
        'partition': 'multi',
    },
    'jetstream_multi': {
        'clusters': ['jetstream-iu', 'jetstream-tacc'],
        'cluster_prefixes': ['jetstream-iu-large', 'jetstream-tacc-large'],
        'destination_prefixes': ['jetstream_iu', 'jetstream_tacc'],
        'partition': 'multi',
    },
}

'''
JETSTREAM_DESTINATION_MAPS = {
    LOCAL_DESTINATION: {
        'clusters': ['jetstream-tacc', 'roundup'],
        'cluster_prefixes': ['jetstream-tacc-large', 'roundup'],
        'destination_prefixes': ['jetstream_tacc', 'slurm'],
        'partition': 'multi',
    },
    'jetstream_multi': {
        'clusters': ['jetstream-tacc',],
        'cluster_prefixes': ['jetstream-tacc-large',],
        'destination_prefixes': ['jetstream_tacc',],
        'partition': 'multi',
    },
}
'''

'''
JETSTREAM_DESTINATION_MAPS = {
    LOCAL_DESTINATION: {
        'clusters': ['roundup'],
        'cluster_prefixes': ['roundup'],
        'destination_prefixes': ['slurm'],
        'partition': 'multi',
    },
    'jetstream_multi': {
        'clusters': ['jetstream-iu', 'jetstream-tacc'],
        'cluster_prefixes': ['jetstream-iu-large', 'jetstream-tacc-large'],
        'destination_prefixes': ['jetstream_iu', 'jetstream_tacc'],
        'partition': 'multi',
    },
}
'''

# Just needs to be a shell script, does not matter what it is
TEST_SCRIPT = '/usr/bin/ldd'

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

# Override the destination's walltime on a per-tool basis
WALLTIMES = {
    'align_families': '96:00:00',
}


def _rnastar(app, param_dict, destination_id, explicit_destination, job_id):
    source = param_dict['refGenomeSource']['geneSource']
    path = None
    ref_mb = 1
    factor = 1.0
    constant = 2048
    if source == 'indexed':
        build = param_dict['refGenomeSource']['GTFconditional']['genomeDir']
        path = '%s/SA' % app.tool_data_tables.get('rnastar_index2').get_entry('value', build, 'path')
        destination_id = None if not explicit_destination else destination_id
        ref_mb = os.stat(path).st_size / 1024 / 1024
        factor = 1.5
    else:
        # Avoid the expense of staging large genome files
        path = param_dict['refGenomeSource']['genomeFastaFiles'].get_file_name()
        destination_id = LOCAL_DESTINATION if not explicit_destination else destination_id
        ref_mb = os.stat(path).st_size / 1024 / 1024
        factor = 11.0
    need_mb = ref_mb * factor + constant
    log.debug("(%s) _rnastar source '%s'; index size = %s MB, factor = %s, constant = %s, need = %s MB, ref path = %s", job_id, source, ref_mb, factor, constant, need_mb, path)
    if need_mb < 8192:
        # In testing, very small jobs needed more than the formula above, so guarantee everyone gets at least 8 GB
        need_mb = 8192
        log.debug("(%s) _rnastar: need increased to minimum = %s MB", job_id, need_mb)
    elif need_mb > 40960 and not explicit_destination:
        # 147456 MB == 144 GB (3 cores) (128GB is the minimum for LM)
        destination_id = BRIDGES_DESTINATION
        need_mb = 147456
        log.debug("(%s) _rnastar: sending to bridges with need = %s MB", job_id, need_mb)
    if explicit_destination:
        if destination_id in (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION, RESERVED_DESTINATION) and need_mb > 40960:
            need_mb = 40960
            log.debug("(%s) _rnastar destination explicit '%s': need decreased to maximum = %s MB", job_id, destination_id, need_mb)
        elif destination_id in JETSTREAM_DESTINATIONS:
            log.debug("(%s) _rnastar destination explicit '%s': need will be ignored", job_id, destination_id)
            #pass  # won't be set anyway
        elif destination_id in BRIDGES_DESTINATIONS:
            need_mb = 147456
            log.debug("(%s) _rnastar destination explicit '%s': need set to = %s MB", job_id, destination_id, need_mb)
    return (destination_id, int(need_mb))


def _set_walltime(tool_id, native_spec):
    walltime = WALLTIMES.get(tool_id, None)
    if walltime:
        if '--time=' in native_spec:
            native_spec = re.sub(r'--time=[^\s]+', '--time=' + walltime, native_spec)
        else:
            native_spec += ' --time=' + walltime
    return native_spec


def __rule(app, tool, job, user_email, resource_params, resource):
    destination = None
    destination_id = None
    default_destination_id = RESOURCES[resource][0]
    explicit_destination = False
    tool_id = tool.id

    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )
    
    # Explcitly set the destination if the user has chosen to do so with the resource selector
    if resource_params:
        resource_key = None
        for resource_key in resource_params.keys():
            if resource_key == resource:
                destination_id = resource_params[resource_key]
                if destination_id in RESOURCES[resource_key]:
                    explicit_destination = True
                    break
                elif destination_id == TEAM_DESTINATION:
                    explicit_destination = True
                    break
                else:
                    log.warning('(%s) Destination/walltime dynamic plugin got an invalid destination: %s', job.id, destination_id)
                    raise JobMappingException(FAILURE_MESSAGE)
        else:
            log.warning('(%s) Destination/walltime dynamic plugin did not receive a valid resource key, resource params were: %s', job.id, resource_params)
            raise JobMappingException(FAILURE_MESSAGE)
    else:
        # if __job_resource is not passed or __job_resource_select is not set to a "yes-like" value, resource_params is an empty dict
        if user_email.lower() in NORM_RESERVED_USERS:
            log.info("(%s) Destination/walltime dynamic plugin returning default reserved destination for '%s'", job.id, user_email)
            #return RESERVED_DESTINATION
            destination_id = RESERVED_DESTINATION

    if destination_id == TEAM_DESTINATION:
        if user_email in TEAM_USERS:
            destination_id = TEAM_DESTINATION
            destination = app.job_config.get_destination(TEAM_DESTINATION)
            destination.params['nativeSpecification'] += ' --ntasks=%s' % resource_params['team_cpus']
        else:
            log.warning("(%s) Unauthorized user '%s' selected team development destination", job.id, user_email)
            destination_id = LOCAL_DESTINATION
            explicit_destination = False

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
                destination_id = default_destination_id

    if not explicit_destination and user_email in ('nate+test@bx.psu.edu', 'cartman@southpark.org'):
        log.info('(%s) Sending job for %s to Jetstream @ IU reserved partition', job.id, user_email)
        explicit_destination = True
        destination_id = 'jetstream_iu_reserved'

    # Some tools do not react well to Jetstream
    if not explicit_destination and tool_id not in JETSTREAM_TOOLS:
        log.info('(%s) Default destination requested and tool is not in Jetstream-approved list, job will be sent to local cluster', job.id)
        destination_id = default_destination_id

    # FIXME: this is getting really messy
    mem_mb = None

    if resource == 'multi_bridges_compute_resource' and tool_id == 'rna_star':
        # FIXME: special casing
        try:
            _destination_id, mem_mb = _rnastar(app, param_dict, destination_id, explicit_destination, job.id)
            if not explicit_destination:
                destination_id = _destination_id
                if destination_id == BRIDGES_DESTINATION:
                    destination = app.job_config.get_destination(destination_id)
                    destination.params['submit_native_specification'] += ' --time=48:00:00'
        except:
            log.exception('(%s) Error determining parameters for STAR job', job.id)
            raise JobMappingException(FAILURE_MESSAGE)

    # Need to explicitly pick a destination because of staging. Otherwise we
    # could just submit with --clusters=a,b,c and let slurm sort it out
    if destination_id in JETSTREAM_DESTINATIONS + (None,) and default_destination_id == LOCAL_DESTINATION:
        test_destination_id = destination_id or default_destination_id
        clusters = ','.join(JETSTREAM_DESTINATION_MAPS[test_destination_id]['clusters'])
        native_specification = app.job_config.get_destination(test_destination_id).params.get('nativeSpecification', '')
        native_specification = _set_walltime(tool_id, native_specification)
        if mem_mb:
            native_specification += ' --mem=%s' % mem_mb
        sbatch_test_cmd = ['sbatch', '--test-only', '--clusters=%s' % clusters] + native_specification.split() + [TEST_SCRIPT]
        log.debug('(%s) Testing job submission to determine suitable cluster: %s', job.id, ' '.join(sbatch_test_cmd))

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
        for i, prefix in enumerate(JETSTREAM_DESTINATION_MAPS[test_destination_id]['cluster_prefixes']):
            if node.startswith(prefix):
                cluster = JETSTREAM_DESTINATION_MAPS[test_destination_id]['clusters'][i]
                destination_prefix = JETSTREAM_DESTINATION_MAPS[test_destination_id]['destination_prefixes'][i]
                break
        else:
            log.error("Could not determine the cluster of node '%s', clusters are: '%s'", node, clusters)
            raise JobMappingException( 'An error occurred while trying to schedule this job. Please retry it and if it continues to fail, report it to an administrator using the bug icon.' )

        destination_id = '%s_%s' % (destination_prefix, JETSTREAM_DESTINATION_MAPS[default_destination_id]['partition'])
        destination = app.job_config.get_destination(destination_id)
        # FIXME: aaaaah i just need this to work for now
        if destination_id.startswith('jetstream'):
            destination.params['submit_native_specification'] = _set_walltime(tool_id, destination.params.get('submit_native_specification', ''))
        else:
            destination.params['nativeSpecification'] = _set_walltime(tool_id, destination.params.get('nativeSpecification', ''))

    if destination_id is None:
        destination_id = default_destination_id

    if mem_mb:
        if destination is None:
            destination = app.job_config.get_destination(destination_id)
        # FIXME: and here wow such mess
        if destination_id in (LOCAL_DESTINATION, LOCAL_DEVELOPMENT_DESTINATION, RESERVED_DESTINATION):
            destination.params['nativeSpecification'] += ' --mem=%s' % mem_mb
        elif destination_id.startswith('jetstream'):
            pass  # don't set --mem, you get the whole node anyway
        elif destination_id in BRIDGES_DESTINATIONS:
            destination.params['submit_native_specification'] += ' --mem=%s' % mem_mb

    # Set a walltime if local is the destination and this is a dynamic walltime tool
    #if destination_id == LOCAL_DESTINATION and tool_id in RUNTIMES:
    #    destination_id = LOCAL_WALLTIME_DESTINATION
    #    #walltime = datetime.timedelta(seconds=(RUNTIMES[tool_id]['runtime'] + (RUNTIMES[tool_id]['stddev'] * RUNTIMES[tool_id]['devs'])) * 60)
    #    walltime = '36:00:00'
    #    destination = app.job_config.get_destination( LOCAL_WALLTIME_DESTINATION ) 
    #    destination.params['nativeSpecification'] += ' --time=%s' % str(walltime).split('.')[0]

    # Allow for overriding the walltime
    if not destination:
        destination = app.job_config.get_destination(destination_id)
    destination.params['nativeSpecification'] = _set_walltime(tool_id, destination.params.get('nativeSpecification', ''))

    log.debug("(%s) Destination/walltime dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("(%s)     nativeSpecification is: %s", job.id, destination.params['nativeSpecification'])
    return destination or destination_id

def dynamic_local_stampede_select_dynamic_walltime(app, tool, job, user_email, resource_params):
    return __rule(app, tool, job, user_email, resource_params, 'tacc_compute_resource')

def dynamic_multi_bridges_select(app, tool, job, user_email, resource_params):
    return __rule(app, tool, job, user_email, resource_params, 'multi_bridges_compute_resource')

def dynamic_stampede_select(app, tool, job, user_email, resource_params):
    return __rule(app, tool, job, user_email, resource_params, 'stampede_compute_resource')
