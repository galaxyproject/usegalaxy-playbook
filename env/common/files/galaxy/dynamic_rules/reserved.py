##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import heapq
import logging
import operator
import os
import re
import time
from functools import partial

import yaml
from sqlalchemy import func

from galaxy import model
from galaxy.jobs.mapper import JobMappingException, JobNotReadyException
from galaxy.util import size_to_bytes


log = logging.getLogger(__name__)


TOOL_MAPPINGS_FILE = None
TOOL_MAPPINGS_FILENAME = 'tool_mappings.yml'

# TODO: could pull this from the job config as well
DEFAULT_DESTINATION_ID = 'slurm_normal'

# Contents of the tool mappings file and special group assignments will be cached
CACHE_TTL = 300
CACHE_TIMES = {}
CACHE_MEMBERS = {}
PARAM_RES = {}

# We can't fully trust Galaxy not to leave jobs stuck in 'queued', so don't defer assignment indefinitely
MAX_DEFER_SECONDS = 30

# If max queued job thresholds are not specified for destination lists, a default is used
DEFAULT_THRESHOLD = 4

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

OPERATIONS = {
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
}

NATIVE_SPEC_PARAMS = (
    'submit_native_specification',
    'native_specification',
    'nativeSpecification',
)

RESOURCE_PARAM_CONVERSIONS = {
    # in: int in GB; out: int in bytes
    'mem': lambda x: x * (1024 ** 3),
}

TOOL_MAPPING_PARAM_CONVERSIONS = {
    # in: size str; out: int in bytes
    'mem': lambda x: size_to_bytes(str(x)),
}

NATIVE_SPEC_PARAM_CONVERSIONS = {
    # in: int in bytes or size str; out: int in mb
    'mem': lambda x: int(size_to_bytes(str(x)) / (1024 ** 2)),
    'time': lambda x: '{}:00:00'.format(x) if isinstance(x, int) else x,
}

deferred_jobs = {}


def __int_gb_to_bytes(gb):
    return gb * (1024 ** 3)


def __short_tool_id(tool_id):
    if '/' in tool_id:
        # extract short tool id from tool shed id
        tool_id = tool_id.split('/')[-2]
    return tool_id


def __get_cached(key, refresh_func):
    cache_time = CACHE_TIMES.get(key, None)
    if not cache_time or (time.time() - cache_time > CACHE_TTL):
        CACHE_MEMBERS[key] = refresh_func()
        CACHE_TIMES[key] = time.time()
    return CACHE_MEMBERS[key]


def __set_tool_mappings_file_path(app):
    global TOOL_MAPPINGS_FILE
    TOOL_MAPPINGS_FILE = os.path.join(app.config.config_dir, TOOL_MAPPINGS_FILENAME)


def __tool_mappings():
    def _tool_mappings_refresh_func():
        with open(TOOL_MAPPINGS_FILE) as fh:
            return yaml.safe_load(fh.read())
    return __get_cached('tool_mappings', _tool_mappings_refresh_func)


def __destination_configs():
    tool_mappings = __tool_mappings()
    try:
        return tool_mappings['destinations']
    except KeyError:
        return {}


def __destination_config(destination_id):
    destination_configs = __destination_configs()
    try:
        return destination_configs[destination_id]
    except KeyError:
        return None


def __check_param(param_dict, param, value, op):
    """Check if a tool param is set to a given value.

    param_dict should be a series of nested dicts
    param should be a string in dotted format e.g. 'reference_source.reference_source_selector'`

    value can be a list, in which case the return is the logical OR of the checks against all values in the list
    """
    subpd = param_dict.copy()
    try:
        # walk the param dict
        for name in param.split('.'):
            subpd = subpd[name]
    except KeyError:
        return False
    if not isinstance(value, list):
        value = [value]
    # TODO: probably shouldn't assume size but that's good enough for now since it's all we're interested in. if this
    # needed to be on something other than size we could add a 'property' key that indicates what property of the param
    # to check
    if isinstance(subpd, model.HistoryDatasetCollectionAssociation):
        # TODO: this is probably only valid for pairs, do we want to maybe do sum([x.get_size() for x in subpd.dataset_instances]) ?
        runtime_value = subpd.dataset_instances[0].get_size()
        # TODO: maybe store this since it will never change, but the YAML is reloaded frequently via the caching
        # function so that's easier said than done for probably negligible gain
        value = [size_to_bytes(str(x)) for x in value]
    elif isinstance(subpd, model.DatasetCollectionElement):
        runtime_value = subpd.first_dataset_instance().get_size()
        value = [size_to_bytes(str(x)) for x in value]
    elif isinstance(subpd, model.DatasetInstance):
        runtime_value = subpd.get_size()
        value = [size_to_bytes(str(x)) for x in value]
    else:
        runtime_value = subpd
    return any([OPERATIONS[op](runtime_value, x) for x in value])


def __tool_mapping(tool_id, param_dict):
    tool_mappings = __tool_mappings()
    tool_mappings_for_tool = None
    tool_mapping = None
    try:
        tool_mappings_for_tool = tool_mappings['tools'][tool_id]
    except KeyError:
        tool_id = __short_tool_id(tool.id)
        try:
            tool_mappings_for_tool = tool_mappings['tools'][tool_id]
        except KeyError:
            log.debug("Tool '%s' not in tool_mapping", tool_id)
    if isinstance(tool_mappings_for_tool, dict):
        tool_mappings_for_tool = [tool_mappings_for_tool]
    if isinstance(tool_mappings_for_tool, list):
        default_tool_mapping = None
        for tm in tool_mappings_for_tool:
            if 'params' in tm:
                for param in tm['params']:
                    if not __check_param(param_dict, param['name'], param['value'], param.get('op', '==')):
                        break  # try next
                else:
                    tool_mapping = tm
                    log.debug("Tool '%s' mapped to destination '%s' due to params: %s", tool_id, tm['destination'], tm['params'])
                    break
            else:
                default_tool_mapping = tm
        if not tool_mapping:
            if default_tool_mapping:
                tool_mapping = default_tool_mapping
                log.debug("Tool '%s' mapped to param-less default: %s", tool_id, tool_mapping['destination'])
            else:
                log.debug("Tool '%s' has mapping but no default", tool_id)
    return tool_mapping


def __tool_destination(tool_id, param_dict):
    # For when you don't care about mem/walltime etc.
    destination_id = None
    tool_mapping = __tool_mapping(tool_id, param_dict)
    if tool_mapping:
        destination_id = tool_mapping['destination']
    return destination_id


def __group_mappings():
    return __tool_mappings().get('groups', {})


def __map_groups(app):
    group_mappings = __group_mappings()
    group_names = group_mappings.keys()
    return app.model.context.query(app.model.Group).filter(
        app.model.Group.table.c.name.in_(group_names),
        app.model.Group.table.c.deleted.is_(False)
    ).all()


def __map_group_members(app):
    # returns email strings, not user objects
    def _map_group_members_refresh_func(app):
        rval = {}
        groups = __map_groups(app)
        for group in groups:
            app.model.context.refresh(group)
            rval[group.name] = [uga.user.email for uga in group.users]
        return rval
    return __get_cached('map_group_members', partial(_map_group_members_refresh_func, app))


def __user_group_mappings(app, user_email, group_type):
    rval = {}
    groups = __map_group_members(app)
    for group_name, members in groups.items():
        map_group = __group_mappings().get(group_name, {})
        if user_email in members and group_type in map_group.keys():
            log.debug("User '%s' found in map group '%s'", user_email, group_name)
            if rval:
                log.warning("User '%s' found in more than one map group, an arbitrary one will be used!", user_email)
            rval = map_group[group_type]
    return rval


def __resolve_destination(app, job, user_email, destination_id):
    # if user is in a special group (named in `groups` dict in tool_mappings yaml) then get destination id overrides
    user_group_destination_mappings = __user_group_mappings(app, user_email, 'destination_overrides')
    # if an override exists then use it, otherwise use what was passed in
    destination_id = user_group_destination_mappings.get(destination_id, destination_id)
    # resolve using the `destinations` dict in tool_mappings yaml
    destination_config = __destination_config(destination_id)
    # if it's a list then we need to use the best dest algorithm
    destination_id = __get_best_destination(app, job, destination_config) or destination_id
    return destination_id


def __convert_param(name, value, conversion_map):
    conversion = conversion_map.get(name)
    if conversion:
        value = conversion(value)
    return value

def __convert_resource_param(name, value):
    return __convert_param(name, value, RESOURCE_PARAM_CONVERSIONS)


def __convert_tool_mapping_param(name, value):
    return __convert_param(name, value, TOOL_MAPPING_PARAM_CONVERSIONS)


def __convert_native_spec_param(name, value):
    return __convert_param(name, value, NATIVE_SPEC_PARAM_CONVERSIONS)


def __override_params(selections, destination_config, override_allowed):
    rval = {}
    for param, value in selections.items():
        orig_value = value
        if value == 0:
            continue
        if override_allowed:
            # if override is not specified for this param then it can still be set to the max (in the next block) if specified
            max_value = destination_config.get('override', {}).get(param, 0)
        if max_value == 0:
            max_value = destination_config.get('max', {}).get(param, 0)
        value = __convert_resource_param(param, value)
        max_value = __convert_tool_mapping_param(param, max_value)
        value = min(value, max_value)
        normalize = destination_config.get('normalize', {}).get(param, None)
        if normalize:
            log.debug("Normalizing '%s bytes' by '%s'", value, normalize)
            normalize_bytes = size_to_bytes(str(normalize))
            floor_factor = int(value / normalize_bytes)
            value = floor_factor * normalize_bytes
            log.debug("Normalized to '%s * %s = %s'", floor_factor, normalize_bytes, value)
        if value > 0:
            rval[param] = value
            log.debug("Value of param '%s' set by user: %s", param, value)
        else:
            log.warning("User set param '%s' to '%s' but that is not allowed, so it will be ignored", param, orig_value)
    return rval


def __parse_resource_selector(app, job, user_email, resource_params):
    # handle job resource parameters
    # NOTE: key and value validation is done in Galaxy prior to job creation, so it is not necessary to do it here
    spec = {}
    selections = {}
    destination_id = None
    for param, value in [(p, v) for (p, v) in resource_params.items() if not p.startswith('__')]:
        if param.endswith('compute_resource'):
            destination_id = value
        else:
            # currently these are all integers
            selections[param] = int(value)
    assert destination_id is not None, "Failed to get destination_id from params"
    destination_config = __destination_config(destination_id)
    destination_id = __get_best_destination(app, job, destination_config) or destination_id
    destination_config = __destination_config(destination_id)
    if destination_config:
        # true if user is allowed to override params up to the value in destination_config.override
        user_group_param_overrides = __user_group_mappings(app, user_email, 'param_overrides')
        spec = __override_params(selections, destination_config, user_group_param_overrides)
        log.debug('Spec from selections: %s', spec)
    elif selections:
        log.warning("Ignored invalid selections for destination '%s': %s", destination_id, selections)
    return destination_id, spec


def __replace_param_value(native_spec, param, value):
    if param not in PARAM_RES:
        PARAM_RES[param] = re.compile(r'--{}=[^\s]+'.format(param))
    param_re = PARAM_RES[param]
    new_param = '--{}={}'.format(param, value)
    if '--{}'.format(param) in native_spec:
        native_spec = re.sub(param_re, new_param, native_spec)
    else:
        native_spec += ' ' + new_param
    return native_spec


def __queued_job_count(app, destination_configs):
    destination_ids = set()
    for destination_config in destination_configs:
        destination_ids.add(destination_config['id'])
        [destination_ids.add(st) for st in destination_config.get('shared_thresholds', [])]
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(destination_ids),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    return dict([(d, c) for d, c in job_counts])


def __get_best_destination(app, job, destination_configs):
    """Given a preference-ordered list of destination configs, attempt to determine the best place to send a job.

    It works like this:

    1. Each destination in the list is checked in order
    2. If fewer jobs are queued at the destination than its thresholds (and destinations listed in shared_thresholds),
       the job will be assigned to the destination
    3. Otherwise, repeat step 2 on the next destination in the list
    4. If all destinations are over their queued job threshold, defer assignment until the next scheduling loop, where
       steps 1-3 will be retried.
    5. If MAX_DEFER_SECONDS is reached and there are still no destinations under the threshold,, choose the destination
       with the fewest queued jobs.
    """
    # short circuit for cases where there aren't multiple to choose from
    if not isinstance(destination_configs, list):
        # nothing to do
        return None
    elif len(destination_configs) == 1:
        return destination_configs[0]['id']

    job_counts = __queued_job_count(app, destination_configs)
    priority_destinations = []
    for destination_config in destination_configs:
        destination_id = destination_config['id']
        threshold = destination_config.get('threshold', DEFAULT_THRESHOLD)
        shared_thresholds = destination_config.get('shared_thresholds', [])
        count = job_counts.get(destination_id, 0) + sum([job_counts.get(st, 0) for st in shared_thresholds])
        # select the first destination under the threshold
        if count <= threshold:
            log.debug("(%s) selecting preferred destination with %s queued jobs: %s", job.id, count, destination_id)
            deferred_jobs.pop(job.id, None)
            return destination_id
        heapq.heappush(priority_destinations, (count, destination_id))
    if job.id not in deferred_jobs:
        deferred_jobs[job.id] = time.time()
    elif time.time() - deferred_jobs[job.id] > MAX_DEFER_SECONDS:
        count, destination_id = heapq.heappop(priority_destinations)
        log.debug(
            "(%s) all destinations over threshold (%s), reached max deferrment, selecting least busy (ct: %s) "
            "destination: %s", job.id, threshold, count, destination_id)
        deferred_jobs.pop(job.id, None)
        return destination_id
    log.debug("(%s) all destinations over threshold, deferring job scheduling: %s", job.id, job_counts)
    raise JobNotReadyException(message="All destinations over max queued thresholds")


def __native_spec_param(destination):
    for param in NATIVE_SPEC_PARAMS:
        if param in destination.params:
            return param
    raise Exception(
        "Could not determine native spec param for destination '{}' with params: {}".format(
            destination.id, destination.params))


def __update_env(destination, envs):
    for env in envs:
        log.debug("Setting env on destination '%s': %s", destination.id, env)
        destination.env.append({
            'name': env.get('name'),
            'file': env.get('file'),
            'execute': env.get('execute'),
            'value': env.get('value'),
            'raw': env.get('raw', False),
        })


def dynamic_full(app, job, tool, resource_params, user_email):
    tool_mapping = None

    envs = []
    spec = {}
    destination_id = None
    destination = None

    if TOOL_MAPPINGS_FILE is None:
        __set_tool_mappings_file_path(app)

    # build the param dictionary
    param_dict = job.get_param_values(app)
    log.debug("(%s) param dict for execution of tool '%s': %s", job.id, tool_id, param_dict)

    # find any mapping for this tool and params
    # tool_mapping = an item in tools[iool_id] in tool_mappings yaml
    tool_mapping = __tool_mapping(tool.id, param_dict)
    if tool_mapping:
        spec = tool_mapping.get('spec', {})
        envs = tool_mapping.get('env', [])

    tool_id = __short_tool_id(tool.id)

    # resource_params is an empty dict if not set
    if resource_params:
        log.debug("(%s) Job resource parameters seleted: %s", job.id, resource_params)
        destination_id, user_spec = __parse_resource_selector(app, job, user_email, resource_params)
        if spec and user_spec:
            log.debug("(%s) Mapped spec for tool '%s' was (prior to resource param selection): %s", job.id, tool_id, spec)
        spec.update(user_spec)
        log.debug("(%s) Spec for tool '%s' after resource param selection: %s", job.id, tool_id, spec or 'none')
    elif tool_mapping:
        destination_id = tool_mapping['destination']
        destination_id = __resolve_destination(app, job, user_email, destination_id)
        log.debug("(%s) Tool '%s' mapped to '%s' native specification overrides: %s", job.id, tool_id, destination_id, spec or 'none')
    else:
        destination_id = DEFAULT_DESTINATION_ID
        destination_id = __resolve_destination(app, job, user_email, destination_id)
        log.debug("(%s) Tool '%s' has no mapping, using default '%s'", job.id, tool_id, destination_id)

    destination = app.job_config.get_destination(destination_id)
    # TODO: requires native spec to be set on all dests, you could do this by plugin instead
    native_spec_param = __native_spec_param(destination)
    native_spec = destination.params.get(native_spec_param, '')

    for param, value in spec.items():
        value = __convert_native_spec_param(param, value)
        native_spec = __replace_param_value(native_spec, param, value)

    __update_env(destination, envs)

    destination.params[native_spec_param] = native_spec

    log.info('(%s) Returning destination: %s', job.id, destination_id)
    log.info('(%s) Native specification: %s', job.id, destination.params.get(native_spec_param))
    return destination
