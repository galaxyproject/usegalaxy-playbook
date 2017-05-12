##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

DESTINATION = 'slurm_normal_single_dynamic_mem'
RODEO_PARAMS = ' --clusters=rodeo --partition=normal'
ROUNDUP_PARAMS = ' --partition=multi'
MEM_DEFAULT = 7680
RODEO_MAX_MEM = MEM_DEFAULT*2
ROUNDUP_MAX_MEM = MEM_DEFAULT*16
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'
SIZE_FAILURE_MESSAGE = 'This tool could not be run because the input is too large to run on the available resources'

def single_dynamic_memory( app, tool, job ):
    inp_data = dict( [ ( da.name, da.dataset ) for da in job.input_datasets ] )
    inp_data.update( [ ( da.name, da.dataset ) for da in job.input_library_datasets ] )

    tool_id = tool.id
    if '/' in tool.id:
        tool_id = tool.id.split('/')[-2]

    if tool_id == 'wig_to_bigWig':
        memfactor = 2.75
    elif tool_id == 'bed_to_bigBed':
        memfactor = 0.5
    else:
        log.warning("(%s) single_dynamic_memory plugin got invalid tool id: %s", job.id, tool_id)
        raise JobMappingException( FAILURE_MESSAGE )

    input_mb = int( inp_data[ "input1" ].get_size() ) / 1024 / 1024
    required_mb = int( input_mb * memfactor )

    destination = app.job_config.get_destination( DESTINATION ) 

    if required_mb < MEM_DEFAULT:
        log.debug("(%s) single_dynamic_memory plugin sending %s job (input1: %s MB) to rodeo with default (%s MB) mem-per-cpu (requires: %s MB)", job.id, tool_id, input_mb, MEM_DEFAULT, required_mb)
        destination.params['nativeSpecification'] += RODEO_PARAMS
    elif required_mb < RODEO_MAX_MEM:
        log.debug("(%s) single_dynamic_memory plugin sending %s job (input1: %s MB) to rodeo with --mem-per-cpu=%s MB", job.id, tool_id, input_mb, required_mb)
        destination.params['nativeSpecification'] += RODEO_PARAMS + ' --mem-per-cpu=%s' % required_mb
    elif required_mb < ROUNDUP_MAX_MEM:
        log.debug("(%s) single_dynamic_memory plugin sending %s job (input1: %s MB) to roundup with --mem-per-cpu=%s MB", job.id, tool_id, input_mb, required_mb)
        destination.params['nativeSpecification'] += ROUNDUP_PARAMS + ' --mem-per-cpu=%s' % required_mb
    else:
        log.warning("(%s) single_dynamic_memory plugin cannot run %s job (input1: %s MB) requiring %s MB", job.id, tool_id, input_mb, required_mb)
        raise JobMappingException( SIZE_FAILURE_MESSAGE )

    log.debug("(%s) single_dynamic_memory dynamic plugin returning '%s' destination", job.id, DESTINATION)
    log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination
