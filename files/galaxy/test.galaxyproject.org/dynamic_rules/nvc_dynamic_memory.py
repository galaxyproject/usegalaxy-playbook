##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import sys
import logging

from galaxy import eggs
from galaxy.jobs.mapper import JobMappingException

sys.path.insert(0, '/galaxy-repl/test/deps/pyBamTools/0.0.1/blankenberg/package_pybamtools_0_0_1/84ac1c74b371/lib/python/pyBamTools-0.0.1-py2.7.egg')
sys.path.insert(0, '/galaxy-repl/test/deps/pyBamParser/0.0.1/blankenberg/package_pybamparser_0_0_1/46bd908161b6/lib/python/pyBamParser-0.0.1-py2.7.egg')

eggs.require('numpy')

from pyBamTools.util import guess_array_memory_usage
from pyBamParser.bam import Reader

log = logging.getLogger(__name__)

DESTINATION = 'slurm_normal_single_dynamic_mem'
NORMAL_PARAMS = ' --clusters=rodeo,roundup --partition=normal'
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
    bam_readers = map( lambda x: Reader( x.file_name, x.metadata.bam_index.file_name ), inp_data.values() )
    dtype = params.get( 'advanced_options', {} ).get( 'coverage_dtype', None )
    use_strand = str( params.get( 'use_strand', False ) )
    array_bytes = guess_array_memory_usage( bam_readers, dtype, use_strand=False )
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
