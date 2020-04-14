##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

DEFAULT_DESTINATION = 'stampede_normal'
DEFAULT_LARGEMEM_DESTINATION = 'stampede_skx_normal'
VALID_DESTINATIONS = (
    DEFAULT_DESTINATION,
    DEFAULT_LARGEMEM_DESTINATION,
    'stampede_development',
    'stampede_skx_development'
)
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'


def __parse_resource_selector(param_dict):
    # handle job resource parameters
    try:
        # validate params
        destination_id = param_dict['__job_resource']['stampede_compute_resource']
        assert destination_id in VALID_DESTINATIONS
        return destination_id
    except:
        # resource param selector not sent with tool form, job_conf.xml misconfigured
        log.exception('(%s) job resource error, keys were: %s', job.id, param_dict.keys())
        raise JobMappingException(FAILURE_MESSAGE)


def dynamic_stampede_select(app, tool, job, user_email):
    destination_id = DEFAULT_DESTINATION
    destination = None
    native_spec_param = 'submit_native_specification'

    tool_id = tool.id
    if '/' in tool.id:
        # extract short tool id from tool shed id
        tool_id = tool.id.split('/')[-2]

    if tool_id == 'trinity_psc':
        raise JobMappingException('This version of Trinity can not be run at this time. Please use the latest version.')

    if user_email is None:
        raise JobMappingException('Please log in to use this tool.')

    inp_data = dict([(da.name, da.dataset) for da in job.input_datasets])
    inp_data.update([(da.name, da.dataset) for da in job.input_library_datasets])

    param_dict = job.get_param_values(app)
    
    if param_dict.get('__job_resource', {}).get('__job_resource__select') != 'yes':
        # override default destination for tools that will always need more memory
        if tool_id == 'trinity':
            destination_id = DEFAULT_LARGEMEM_DESTINATION
        log.debug("Job resource parameters not seleted, using default destination: %s", destination_id)
    else:
        destination_id = __parse_resource_selector(param_dict)

    destination = app.job_config.get_destination(destination_id)

    if tool_id in ('unicycler', 'spades', 'shovill'):
        # prevent SPAdes crashes on large-core nodes
        stack_ulimit = 24576
        destination.env.append({
            'name': None,
            'file': None,
            'execute': 'ulimit -s %d' % stack_ulimit,
            'value': None,
            'raw': False,
        })
        log.debug('(%s) will execute `ulimit -s %d`', job.id, stack_ulimit)

    # FIXME: maybe this is already set properly?
    #destination.env.append({
    #    'name': 'GALAXY_MEMORY_MB',
    #    'file': None,
    #    'execute': None,
    #    'value': str(mem),
    #    'raw': False,
    #})
    #log.debug("(%s) set $GALAXY_MEMORY_MB to %s", job.id, mem)

    log.info('(%s) returning destination: %s', job.id, destination_id)
    log.info('(%s) native specification: %s', job.id, destination.params.get(native_spec_param))
    return destination
