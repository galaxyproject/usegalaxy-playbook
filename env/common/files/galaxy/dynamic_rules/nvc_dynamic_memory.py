##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import sys
import logging

from galaxy.util import string_as_bool
from galaxy.jobs.mapper import JobMappingException
from pyBamTools.util import guess_array_memory_usage
from pyBamParser.bam import Reader


log = logging.getLogger(__name__)

DESTINATION = 'slurm_normal_dynamic_mem'
NORMAL_PARAMS = ' --partition=normal'
MULTI_PARAMS = ' --partition=multi'
MEM_DEFAULT = 7680
NORMAL_MAX_MEM = MEM_DEFAULT*2
MULTI_MAX_MEM = MEM_DEFAULT*16
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'
SIZE_FAILURE_MESSAGE = 'This tool could not be run because the input is too large to run on the available resources'

DEFAULT_OVERHEAD = 1024 #MB = 1GB fudge factor to cover non-nucleotide storage


def nvc_dynamic_memory( app, tool, job ):
    inp_data = dict( [ ( da.name, da.dataset ) for da in job.input_datasets ] )
    inp_data.update( [ ( da.name, da.dataset ) for da in job.input_library_datasets ] )
    params = job.get_param_values( app, ignore_errors=True )
    bams = filter( lambda x: x.metadata.bam_index is not None, inp_data.values() )
    bam_readers = map( lambda x: Reader( x.file_name, x.metadata.bam_index.file_name ), bams )
    dtype = params.get( 'advanced_options', {} ).get( 'coverage_dtype', None )
    use_strand = string_as_bool( params.get( 'use_strand', False ) )
    array_bytes = guess_array_memory_usage( bam_readers, dtype, use_strand=use_strand )
    required_mb = ( array_bytes / 1024 / 1024 ) +  DEFAULT_OVERHEAD # this division will truncate, hopefully handled by overhead
    
    destination = app.job_config.get_destination( DESTINATION ) 

    if required_mb < MEM_DEFAULT:
        log.debug("(%s) nvc_dynamic_memory plugin sending %s job to normal with default (%s MB) mem-per-cpu (requires: %s MB)", job.id, tool.id, MEM_DEFAULT, required_mb)
        destination.params['nativeSpecification'] += NORMAL_PARAMS
    elif required_mb < NORMAL_MAX_MEM:
        log.debug("(%s) nvc_dynamic_memory plugin sending %s job to normal with --mem-per-cpu=%s MB", job.id, tool.id, required_mb)
        destination.params['nativeSpecification'] += NORMAL_PARAMS + ' --mem-per-cpu=%s' % required_mb
    elif required_mb < MULTI_MAX_MEM:
        log.debug("(%s) nvc_dynamic_memory plugin sending %s job to multi with --mem-per-cpu=%s MB", job.id, tool.id, required_mb)
        destination.params['nativeSpecification'] += MULTI_PARAMS + ' --mem-per-cpu=%s' % required_mb
    else:
        log.debug("(%s) nvc_dynamic_memory plugin sending %s job to multi with --mem-per-cpu=%s MB (trying MAX avialable)", job.id, tool.id, MULTI_MAX_MEM)
        destination.params['nativeSpecification'] += MULTI_PARAMS + ' --mem-per-cpu=%s' % MULTI_MAX_MEM

    log.debug("(%s) nvc_dynamic_memory dynamic plugin returning '%s' destination", job.id, DESTINATION)
    log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination
