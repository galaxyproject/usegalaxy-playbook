##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import heapq
import logging
import operator
import os
import re
import threading
import time
from functools import partial

import yaml
from sqlalchemy import func

import galaxy.tools
from galaxy import model
from galaxy.jobs.mapper import JobMappingException, JobNotReadyException
from galaxy.util import size_to_bytes


GALAXY_LIB_TOOLS = galaxy.tools.GALAXY_LIB_TOOLS_UNVERSIONED


log = logging.getLogger(__name__)

# Use a thread-local var for storing per-job logger adapter
local = threading.local()

# TODO: might be cleaner to make `app` a global
JOB_ROUTER_CONF_FILE = None
JOB_ROUTER_CONF_FILENAME = 'job_router_conf.yml'

# Contents of the tool mappings file and special group assignments will be cached
# this is an rlock because getting group member cache also hits the job router conf cache
CACHE_LOCK = threading.RLock()
CACHE_TTL = 30  # FIXME: 300
CACHE_TIMES = {}
CACHE_MEMBERS = {}
PARAM_RES = {}

# Users' roles are cached for TIaaS and must be periodically expunged to prevent infinite growth
USER_ROLES_CACHE_TTL = 900

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
share_job_counts = {}


class JobLogger(logging.LoggerAdapter):
    """Custom logger adapter to prepend job id to all messages"""
    def process(self, msg, kwargs):
        return '(%s) %s' % (self.extra['job_id'], msg), kwargs


def __int_gb_to_bytes(gb):
    return gb * (1024 ** 3)


def __versionless_tool_id(tool_id):
    if '/' in tool_id:
        tool_id, version = tool_id.rsplit('/', 1)
    return tool_id


def __short_tool_id(tool_id):
    if '/' in tool_id:
        # extract short tool id from tool shed id
        tool_id = tool_id.split('/')[-2]
    return tool_id


def __clean_user_roles_cache():
    # must be called w/ lock acquired
    for key in [k for k, t in CACHE_TIMES.items() if k.startswith('user_roles_') and time.time() - t > USER_ROLES_CACHE_TTL]:
        del CACHE_MEMBERS[key]
        del CACHE_TIMES[key]
        log.debug("Expired user roles from cache for key: %s", key)


def __get_cached(key, refresh_func):
    # TODO: this may be too much locking...
    # cache is shared across job worker threads, lock to prevent cache update collisions
    CACHE_LOCK.acquire()
    try:
        __clean_user_roles_cache()
        cache_time = CACHE_TIMES.get(key, None)
        if not cache_time or (time.time() - cache_time > CACHE_TTL):
            CACHE_MEMBERS[key] = refresh_func()
            CACHE_TIMES[key] = time.time()
            log.debug("Added/updated cache for key: %s", key)
        return CACHE_MEMBERS[key]
    finally:
        CACHE_LOCK.release()


def __set_job_router_conf_file_path(app):
    global JOB_ROUTER_CONF_FILE
    JOB_ROUTER_CONF_FILE = os.path.join(app.config.config_dir, JOB_ROUTER_CONF_FILENAME)
    log.info("Set job router config file path to: %s", JOB_ROUTER_CONF_FILE)


def __job_router_conf():
    def _job_router_conf_refresh_func():
        with open(JOB_ROUTER_CONF_FILE) as fh:
            return yaml.safe_load(fh.read())
    return __get_cached('job_router_conf', _job_router_conf_refresh_func)


def __destination_configs():
    job_router_conf = __job_router_conf()
    try:
        return job_router_conf['destinations']
    except KeyError:
        return {}


def __destination_config(destination_id):
    destination_configs = __destination_configs()
    try:
        return destination_configs[destination_id]
    except KeyError:
        return None


def __share_job_counts(destination_id):
    # NOTE: rval should always include the ID that was passed in
    job_router_conf = __job_router_conf()
    if destination_id not in share_job_counts:
        share_with = set([destination_id])
        shares = job_router_conf.get('share_job_counts', [])
        for share_set in shares:
            if destination_id in share_set:
                share_with.update(share_set)
        share_job_counts[destination_id] = share_with
    return share_job_counts[destination_id]


def __data_table_lookup(app, param, lookup_value):
    # TODO: possible to get table name from the tool?
    table_name = param['table_name']
    lookup_column = param.get('lookup_column', 'value')
    value_column = param.get('value_column', 'path')
    value_template = param.get('value_template', '{value}')

    runtime_value = app.tool_data_tables.get(table_name).get_entry(lookup_column, lookup_value, value_column)
    if runtime_value is None:
        local.log.warning("Data table '%s' lookup '%s=%s: %s=None' returned None!, defaulting to 0",
                          table_name, lookup_column, lookup_value, value_column)
        return 0
    runtime_value = value_template.format(value=runtime_value)

    if value_column == 'path':
        # TODO: cache this value
        try:
            _t = runtime_value
            runtime_value = os.path.getsize(runtime_value)
            local.log.debug("Data table '%s' lookup '%s=%s: %s=%s' (converted value: %s bytes)",
                            table_name, lookup_column, lookup_value, value_column, _t, runtime_value)
        except OSError:
            local.log.exception('Failed to get size of: %s', runtime_value)
            runtime_value = 0
    else:
        local.log.debug("Data table '%s' lookup '%s=%s: %s=%s'", table_name, lookup_column, lookup_value, value_column, runtime_value)

    return runtime_value


def __check_param(app, param_dict, param):
    """Check if a tool param is set to a given value.

    param_dict should be a series of nested dicts
    param should be a string in dotted format e.g. 'reference_source.reference_source_selector'`

    value can be a list, in which case the return is the logical OR of the checks against all values in the list
    """
    name = param['name']
    value = param['value']
    op = param.get('op', '==')
    type_ = param.get('type')

    # When walking the dict down to the param, any element that's a list will be replaced by the first element of that
    # list. This handles repeats (you always check the first element of the repeat) and things like Trinity paired
    # inputs, which are lists of (single?) HDAs. This may prevent more complex rules but it's good enough for our needs
    # right now.

    subpd = param_dict.copy()
    try:
        # walk the param dict
        for subname in name.split('.'):
            subpd = subpd[subname]
            # replace lists by the first element of the list
            if isinstance(subpd, list):
                local.log.warning("Converting list param element '%s' to single (first) element: %s", subname, name)
                subpd = subpd[0]
    except (KeyError, IndexError):
        return False
    runtime_value = subpd

    if not isinstance(value, list):
        value = [value]

    # TODO: probably shouldn't assume size but that's good enough for now since it's all we're interested in. if this
    # needed to be on something other than size we could add a 'property' key that indicates what property of the param
    # to check
    if type_ == 'data_table_lookup':
        # TODO: any way to automatically detect if a param is a data table value
        runtime_value = __data_table_lookup(app, param, runtime_value)
        value = [size_to_bytes(str(x)) for x in value]
    elif isinstance(runtime_value, model.HistoryDatasetCollectionAssociation):
        # TODO: this is probably only valid for pairs, do we want to maybe do sum([x.get_size() for x in runtime_value.dataset_instances]) ?
        runtime_value = runtime_value.dataset_instances[0].get_size()
        # TODO: maybe store this since it will never change, but the YAML is reloaded frequently via the caching
        # function so that's easier said than done for probably negligible gain
        value = [size_to_bytes(str(x)) for x in value]
    elif isinstance(runtime_value, model.DatasetCollectionElement):
        runtime_value = runtime_value.first_dataset_instance().get_size()
        value = [size_to_bytes(str(x)) for x in value]
    elif isinstance(runtime_value, model.DatasetInstance) or hasattr(runtime_value, 'get_size'):
        # hasattr for tests, is there a better way to mock it?
        runtime_value = runtime_value.get_size()
        value = [size_to_bytes(str(x)) for x in value]

    return any([OPERATIONS[op](runtime_value, x) for x in value])


def __tool_mapping(app, tool_id, param_dict):
    job_router_conf = __job_router_conf()
    tool_mappings = None
    tool_mapping = None
    tool_ids = (tool_id, __versionless_tool_id(tool_id), __short_tool_id(tool_id))
    for tool_id in tool_ids:
        try:
            tool_mappings = job_router_conf['tools'][tool_id]
            break
        except KeyError:
            pass
    else:
        local.log.debug("Tool '%s' not in tool_mapping", tool_id)
    if isinstance(tool_mappings, str):
        tool_mappings = job_router_conf['tools'][tool_mappings]
    if isinstance(tool_mappings, dict):
        tool_mappings = [tool_mappings]
    if isinstance(tool_mappings, list):
        default_tool_mapping = None
        for _tool_mapping in tool_mappings:
            if 'params' in _tool_mapping:
                for param in _tool_mapping['params']:
                    if not __check_param(app, param_dict, param): #param['name'], param['value'], param.get('op', '==')):
                        break  # try next
                else:
                    tool_mapping = _tool_mapping
                    destination_id = _tool_mapping.get('destination', '_no_destination_provided_')
                    local.log.debug("Tool '%s' mapped to destination '%s' due to params: %s",
                                    tool_id, destination_id, _tool_mapping['params'])
                    break
            else:
                default_tool_mapping = _tool_mapping
        if not tool_mapping:
            if default_tool_mapping:
                tool_mapping = default_tool_mapping
                destination_id = tool_mapping.get('destination', '_no_destination_provided_')
                local.log.debug("Tool '%s' mapped to param-less default: %s", tool_id, destination_id)
            else:
                local.log.debug("Tool '%s' has mapping but no default", tool_id)
    return tool_mapping


def __group_mappings():
    return __job_router_conf().get('groups', {})


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
            local.log.debug("User '%s' found in map group '%s'", user_email, group_name)
            if rval:
                local.log.warning("User '%s' found in more than one map group, an arbitrary one will be used!", user_email)
            rval = map_group[group_type]
    return rval


def __user_roles(app, user):
    def _user_roles_refresh_func(app, user):
        return [role.name for role in user.all_roles() if not role.deleted]
    return __get_cached(f'user_roles_{user.id}', partial(_user_roles_refresh_func, app, user))


def __user_in_training(app, user):
    return user is not None and any([role.startswith('training-') for role in __user_roles(app, user)])


def __resolve_destination_list(app, job, destination_id):
    # resolve using the `destinations` dict in job_router_conf yaml
    destination_config = __destination_config(destination_id)
    # if it's a list then we need to use the best dest algorithm
    destination_id = __get_best_destination(app, job, destination_config) or destination_id
    return destination_id


def __resolve_destination(app, job, user_email, destination_id):
    # if user is in a special group (named in `groups` dict in job_router_conf yaml) then get destination id overrides
    user_group_destination_mappings = __user_group_mappings(app, user_email, 'destination_overrides')
    # if an override exists then use it, otherwise use what was passed in
    destination_id = user_group_destination_mappings.get(destination_id, destination_id)
    # if it's a list then we need to use the best dest algorithm
    destination_id = __resolve_destination_list(app, job, destination_id)
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
        max_value = 0
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
            local.log.debug("Normalizing '%s bytes' by '%s'", value, normalize)
            normalize_bytes = size_to_bytes(str(normalize))
            floor_factor = int(value / normalize_bytes)
            value = floor_factor * normalize_bytes
            local.log.debug("Normalized to '%s * %s = %s'", floor_factor, normalize_bytes, value)
        if value > 0:
            rval[param] = value
            local.log.debug("Value of param '%s' set by user: %s", param, value)
        else:
            local.log.warning("User set param '%s' to '%s' but that is not allowed, so it will be ignored", param, orig_value)
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
    # bypass any group mappings and just pick a destination if the supplied dest is a list
    destination_id = __resolve_destination_list(app, job, destination_id)
    destination_config = __destination_config(destination_id)
    if destination_config:
        # true if user is allowed to override params up to the value in destination_config.override
        user_group_param_overrides = __user_group_mappings(app, user_email, 'param_overrides')
        spec = __override_params(selections, destination_config, user_group_param_overrides)
        local.log.debug('Spec from selections: %s', spec)
    elif selections:
        local.log.warning("Ignored invalid selections for destination '%s': %s", destination_id, selections)
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
        # this set includes the destination_id passed in
        share_job_counts = __share_job_counts(destination_config['id'])
        destination_ids.update(share_job_counts)
    query_timer = app.execution_timer_factory.get_timer(
        'usegalaxy.jobs.rules.job_router',
        'job_router.__queued_job_count query for destination IDs ${destination_ids} executed'
    )
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(destination_ids),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    local.log.debug(query_timer.to_str(destination_ids=str(sorted(destination_ids))))
    return dict([(d, c) for d, c in job_counts])


def __get_best_destination(app, job, destination_configs):
    """Given a preference-ordered list of destination configs, attempt to determine the best place to send a job.

    It works like this:

    1. Each destination in the list is checked in order
    2. If fewer jobs are queued at the destination (and destinations listed in share_job_counts) than the threshold,
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
        queue_factor = destination_config.get('queue_factor', 1)
        threshold = destination_config.get('threshold', DEFAULT_THRESHOLD)
        share_job_counts = __share_job_counts(destination_id)
        count = sum([job_counts.get(destination_id, 0) for destination_id in share_job_counts])
        local.log.debug("Sum of job counts for '%s' (includes: %s): %s", destination_id, share_job_counts, count)
        if queue_factor != 1:
            count *= queue_factor
            local.log.debug("Adjusted job count with applied queue factor of %s: %s", queue_factor, count)
        # select the first destination under the threshold
        if count <= threshold:
            local.log.debug("selecting preferred destination with %s queued jobs: %s", count, destination_id)
            deferred_jobs.pop(job.id, None)
            return destination_id
        heapq.heappush(priority_destinations, (count, destination_id))
    if job.id not in deferred_jobs:
        deferred_jobs[job.id] = time.time()
    elif time.time() - deferred_jobs[job.id] > MAX_DEFER_SECONDS:
        count, destination_id = heapq.heappop(priority_destinations)
        local.log.debug(
            "all destinations over threshold (%s), reached max deferrment, selecting least busy (ct: %s) "
            "destination: %s", threshold, count, destination_id)
        deferred_jobs.pop(job.id, None)
        return destination_id
    local.log.debug("all destinations over threshold, deferring job scheduling: %s", job_counts)
    raise JobNotReadyException(message="All destinations over max queued thresholds")


def __update_native_spec(destination_id, spec, native_spec):
    destination_config = __destination_config(destination_id)
    for param, value in spec.items():
        if param not in destination_config.get('valid', []):
            local.log.debug("Setting param '%s' on destination '%s' is not valid, so it will be ignored", param, destination_id)
        else:
            value = __convert_native_spec_param(param, value)
            native_spec = __replace_param_value(native_spec, param, value)
    return native_spec


def __native_spec_param(destination):
    for param in NATIVE_SPEC_PARAMS:
        if param in destination.params:
            return param
    return None


def __update_env(destination, envs):
    for env in envs:
        local.log.debug("Setting env on destination '%s': %s", destination.id, env)
        destination.env.append({
            'name': env.get('name'),
            'file': env.get('file'),
            'execute': env.get('execute'),
            'value': env.get('value'),
            'raw': env.get('raw', False),
        })


def __training_tools():
    job_router_conf = __job_router_conf()
    try:
        return job_router_conf['training_tools']
    except KeyError:
        return {}


def __is_training_compatible_tool(tool_id):
    return tool_id not in __training_tools().get('incompatible', [])


def __training_tool_mapping(tool_id):
    mapping = __training_tools().get('mapping', {})
    default = mapping.get('_default_', None)
    return mapping.get(tool_id, default)


def __is_training_history(job, tool_id):
    try:
        return (any([(hta.user_value == 'training' or hta.user_tname == 'training') for hta in job.history.tags])
                and not tool_id.startswith('interactive_tool_'))
    except:
        local.log.warning("Failed to read tags")
        return False


def __is_galaxy_lib_tool(tool_id):
    # TODO: versioned?
    return tool_id in GALAXY_LIB_TOOLS


def job_router(app, job, tool, resource_params, user):
    tool_mapping = None

    envs = []
    spec = {}
    login_required = False
    destination_id = None
    destination = None
    container_override = None

    if JOB_ROUTER_CONF_FILE is None:
        __set_job_router_conf_file_path(app)

    # build the param dictionary
    param_dict = job.get_param_values(app)
    local.log = JobLogger(log, {'job_id': job.id})
    local.log.debug("param dict for execution of tool '%s': %s", tool.id, param_dict)

    # find any mapping for this tool and params
    # tool_mapping = an item in tools[iool_id] in job_router_conf yaml
    tool_mapping = __tool_mapping(app, tool.id, param_dict)
    if tool_mapping:
        spec = tool_mapping.get('spec', {}).copy()
        envs = tool_mapping.get('env', []).copy()
        login_required = tool_mapping.get('login_required', False)
        container_override = tool_mapping.get('container_override', None)

    tool_id = __short_tool_id(tool.id)

    if login_required and user is None:
        raise JobMappingException('Please log in to use this tool')

    user_email = None if user is None else user.email

    # resource_params is an empty dict if not set
    if resource_params:
        local.log.debug("Job resource parameters selected: %s", resource_params)
        destination_id, user_spec = __parse_resource_selector(app, job, user_email, resource_params)
        if spec and user_spec:
            local.log.debug("Mapped spec for tool '%s' was (prior to resource param selection): %s", tool_id, spec)
        spec.update(user_spec)
        local.log.debug("Spec for tool '%s' after resource param selection: %s", tool_id, spec or 'none')
    elif (__is_training_history(job, tool_id) or __user_in_training(app, user)) and __is_training_compatible_tool(tool_id):
        destination_id = __training_tool_mapping(tool_id)
        local.log.info("User %s is in a training, mapped to destination: %s", user_email, destination_id)
        # bypass any group mappings and just pick a destination if the supplied dest is a list
        destination_id = __resolve_destination_list(app, job, destination_id)
    elif tool_mapping and tool_mapping.get('destination'):
        destination_id = tool_mapping['destination']
        destination_id = __resolve_destination(app, job, user_email, destination_id)
        local.log.debug("Tool '%s' mapped to '%s' native specification overrides: %s", tool_id, destination_id, spec or 'none')

    if destination_id is None:
        if __is_galaxy_lib_tool(tool_id):
            # TODO: should this be a mapping or something? e.g. s/$/_galaxy_env/ so that their regular tool mapping
            # (16 GB or whatever) still applies
            tool_mapping = __tool_mapping(app, '_galaxy_lib_', {})
            destination_id = tool_mapping['destination']
            local.log.debug("'%s' is a Galaxy lib too, using destination '%s'", tool_id, destination_id)
        else:
            tool_mapping = __tool_mapping(app, '_default_', {})
            destination_id = tool_mapping['destination']
            local.log.debug("'%s' has no destination mapping, using default destination '%s'", tool_id, destination_id)
        destination_id = __resolve_destination(app, job, user_email, destination_id)

    local.log.debug('Final destination after resolution is: %s', destination_id)
    destination = app.job_config.get_destination(destination_id)
    # TODO: requires native spec to be set on all dests, you could do this by plugin instead
    native_spec_param = __native_spec_param(destination)
    if native_spec_param:
        native_spec = destination.params.get(native_spec_param, '')
        native_spec = __update_native_spec(destination_id, spec, native_spec)
        destination.params[native_spec_param] = native_spec
    elif spec:
        local.log.warning(
            "Could not determine native spec param for destination '%s', spec will not be applied: %s",
            destination.id, destination.params)

    __update_env(destination, envs)

    if container_override:
        destination.params['container_override'] = container_override
        local.log.debug("Container override from tool mapping: %s", container_override)

    local.log.info('Returning destination: %s', destination_id)
    local.log.info('Native specification: %s', destination.params.get(native_spec_param))
    return destination
