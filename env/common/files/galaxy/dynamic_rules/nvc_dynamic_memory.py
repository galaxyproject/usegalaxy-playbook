##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import sys
import logging

from galaxy.util import string_as_bool
from galaxy.jobs.mapper import JobMappingException
#from pyBamTools.util import guess_array_memory_usage
#from pyBamParser.bam import Reader

#galaxy.util.submodules ERROR 2020-09-30 13:42:30,316 usegalaxy.jobs.rules.nvc_dynamic_memory dynamic module could not be loaded (traceback follows):
#Traceback (most recent call last):
#  File "/cvmfs/main.galaxyproject.org/galaxy/lib/galaxy/util/submodules.py", line 44, in __import_submodules_impl
#    submodule = importlib.import_module(full_name)
#  File "/cvmfs/main.galaxyproject.org/deps/_conda/envs/_galaxy_/lib/python3.6/importlib/__init__.py", line 126, in import_module
#    return _bootstrap._gcd_import(name[level:], package, level)
#  File "<frozen importlib._bootstrap>", line 994, in _gcd_import
#  File "<frozen importlib._bootstrap>", line 971, in _find_and_load
#  File "<frozen importlib._bootstrap>", line 955, in _find_and_load_unlocked
#  File "<frozen importlib._bootstrap>", line 665, in _load_unlocked
#  File "<frozen importlib._bootstrap_external>", line 678, in exec_module
#  File "<frozen importlib._bootstrap>", line 219, in _call_with_frames_removed
#  File "/srv/galaxy/main/dynamic_rules/usegalaxy/jobs/rules/nvc_dynamic_memory.py", line 11, in <module>
#    from pyBamParser.bam import Reader
#  File "/cvmfs/main.galaxyproject.org/venv/lib/python3.6/site-packages/pyBamParser/bam/__init__.py", line 4, in <module>
#    from ..bai import Reader as BAIReader
#  File "/cvmfs/main.galaxyproject.org/venv/lib/python3.6/site-packages/pyBamParser/bai/__init__.py", line 4, in <module>
#    from ..util.odict import odict
#  File "/cvmfs/main.galaxyproject.org/venv/lib/python3.6/site-packages/pyBamParser/util/odict.py", line 6, in <module>
#    from UserDict import UserDict
#ModuleNotFoundError: No module named 'UserDict'

log = logging.getLogger(__name__)

# NOTE: The slurm_normal_dynamic_mem destination includes --partition=normal, but the --partition=X we append here
# overrides that. Keeping it in a single destination is intentional since we run jobs in the multi partition for
# priority reasons, but we only allocate 1 core.

DESTINATION = 'slurm_normal_dynamic_mem'
NORMAL_PARAMS = ' --partition=normal'
MULTI_PARAMS = ' --partition=multi'
MEM_DEFAULT = 7680
NORMAL_MAX_MEM = MEM_DEFAULT*2
MULTI_MAX_MEM = MEM_DEFAULT*16
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'
SIZE_FAILURE_MESSAGE = 'This tool could not be run because the input is too large to run on the available resources'

DEFAULT_OVERHEAD = 1024 #MB = 1GB fudge factor to cover non-nucleotide storage


def dynamic_nvc_dynamic_memory(app, tool, job):
    # FIXME hack hack hack
    destination = 'slurm_normal_16gb'
    log.debug("(%s) nvc_dynamic_memory dynamic plugin returning '%s' destination", job.id, destination)
    return destination

    """
    inp_data = dict([(da.name, da.dataset) for da in job.input_datasets])
    inp_data.update([(da.name, da.dataset) for da in job.input_library_datasets])
    params = job.get_param_values(app, ignore_errors=True)
    bams = filter(lambda x: x is not None and x.metadata.bam_index is not None, inp_data.values())
    if bams:
        bam_readers = list(map(lambda x: Reader(x.file_name, x.metadata.bam_index.file_name ), bams))
        dtype = params.get('advanced_options', {}).get('coverage_dtype', None)
        use_strand = string_as_bool(params.get('use_strand', False))
        array_bytes = guess_array_memory_usage(bam_readers, dtype, use_strand=use_strand)
        required_mb = (array_bytes / 1024 / 1024) + DEFAULT_OVERHEAD # this division will truncate, hopefully handled by overhead
    else:
        log.debug("(%s) all inputs or BAM indexes are None")
        required_mb = 1

    destination = app.job_config.get_destination(DESTINATION)

    required_mb = int(required_mb)

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
"""
