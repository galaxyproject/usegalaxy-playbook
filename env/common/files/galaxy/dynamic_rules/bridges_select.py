##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

BRIDGES_NORMAL_DESTINATION = 'bridges_normal'
BRIDGES_DEVELOPMENT_DESTINATION = 'bridges_development'
BRIDGES_DESTINATIONS = (BRIDGES_NORMAL_DESTINATION, BRIDGES_DEVELOPMENT_DESTINATION,)
VALID_DESTINATIONS = BRIDGES_DESTINATIONS
RESOURCE_KEYS = ('bridges_compute_resource',)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

def dynamic_bridges_select( app, tool, job, user_email ):
    destination_id = 'jetstream_iu_multi'
    log.debug("(%s) dynamic_bridges_select() returning '%s'", job.id, destination_id)
    return destination_id

def _dynamic_bridges_select( app, tool, job, user_email ):
    destination = None
    tool_id = tool.id
    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    inp_data = dict( [ ( da.name, da.dataset ) for da in job.input_datasets ] )
    inp_data.update( [ ( da.name, da.dataset ) for da in job.input_library_datasets ] )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )
    
    if '__job_resource' in param_dict and param_dict['__job_resource']['__job_resource__select'] == 'yes':
        resource_key = None
        for resource_key in param_dict['__job_resource'].keys():
            if resource_key in RESOURCE_KEYS:
                break
        else:
            log.warning('(%s) Bridges dynamic plugin did not find a valid resource key, keys were: %s', job.id, param_dict['__job_resource'].keys())
            raise JobMappingException( FAILURE_MESSAGE )

        destination_id = param_dict['__job_resource'][resource_key]
        if destination_id not in VALID_DESTINATIONS:
            log.warning('(%s) Bridges dynamic plugin got an invalid destination: %s', job.id, destination_id)
            raise JobMappingException( FAILURE_MESSAGE )

        if destination_id == BRIDGES_NORMAL_DESTINATION:
            destination = app.job_config.get_destination(BRIDGES_NORMAL_DESTINATION)
        elif destination_id == BRIDGES_DEVELOPMENT_DESTINATION:
            destination = app.job_config.get_destination( BRIDGES_DEVELOPMENT_DESTINATION )
    else:
        # default to 15 cpus in the regular queue
        destination = app.job_config.get_destination(BRIDGES_NORMAL_DESTINATION)

    if destination is None:
        log.error('"(%s) bridges_select dynamic plugin did not set a destination', job.id)
        raise JobMappingException( FAILURE_MESSAGE )

    if destination.id == BRIDGES_NORMAL_DESTINATION:
        mem = 240 * 1024 # 5 * 48 GB
        walltime = '24:00:00'

        if tool_id in ('trinity_psc', 'trinity'):
            infile = None
            if tool_id == 'trinity_psc':
                infile = inp_data.get('left_input') or inp_data.get('input')
            elif tool_id == 'trinity':
                infile = inp_data.get('pool|left_input') or inp_data.get('pool|input')

            if infile is None:
                log.error('Trinity submitted without inputs, failing')
                raise JobMappingException( FAILURE_MESSAGE )
            insize = infile.get_size()

            if param_dict.get('additional_params', {}).get('normalize_reads', False):
                # normalizing: less runtime, less memory
                if insize < (10 * 1024 ** 3):
                    mem = 240 * 1024 # 5 * 48 GB
                    walltime = '72:00:00'
                elif insize < (100 * 1024 ** 3):
                    mem = 480 * 1024 # 10 * 48 GB
                    walltime = '96:00:00'
                else:
                    mem = 720 * 1024 # 15 * 48 GB
                    walltime = '96:00:00'
            else:
                # increased runtime, increased memory
                if insize < (10 * 1024 ** 3):
                    mem = 480 * 1024 # 10 * 48 GB
                    walltime = '96:00:00'
                elif insize < (100 * 1024 ** 3):
                    mem = 720 * 1024 # 15 * 48 GB
                    walltime = '96:00:00'
                else:
                    mem = 960 * 1024 # 20 * 48 GB
                    walltime = '96:00:00'

        elif tool_id in ('unicycler', 'spades'):
            # SPAdes uses at most 250GB
            mem = 288 * 1024
            walltime = '48:00:00'
            stack_ulimit = 24576
            destination.env.append({
                'name': None,
                'file': None,
                'execute': 'ulimit -s %d' % stack_ulimit,
                'value': None,
                'raw': False,
            })
            log.debug('(%s) will execute `ulimit -s %d`', job.id, stack_ulimit)
        else:
            # nothing to go off of yet so we'll just guess
            mem = 480 * 1024
            walltime = '48:00:00'

        destination.env.append({
            'name': 'GALAXY_MEMORY_MB',
            'file': None,
            'execute': None,
            'value': str(mem),
            'raw': False,
        })
        log.debug("(%s) set $GALAXY_MEMORY_MB to %s", job.id, mem)

        destination.params['submit_native_specification'] += ' --time=%s' % walltime
        destination.params['submit_native_specification'] += ' --mem=%s' % mem

    log.debug("(%s) bridges_select dynamic plugin returning '%s' destination", job.id, destination.id)
    log.debug("     submit_native_specification is: %s", destination.params['submit_native_specification'])
    return destination
