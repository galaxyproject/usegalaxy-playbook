##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import heapq
import logging
import time
from collections import namedtuple

from sqlalchemy import func

from galaxy.jobs.mapper import JobMappingException, JobNotReadyException


log = logging.getLogger(__name__)

JOB_PRIORITY_USERS_GROUP_NAME = 'Job Priority Users'
#JOB_PRIORITY_USERS_GROUP = None
JOB_PRIORITY_USERS_GROUP_CACHE_TIME = None
JOB_PRIORITY_USERS_GROUP_CACHE_TTL = 300
JOB_PRIORITY_USERS_GROUP_MEMBERS = None

# we can't fully trust galaxy not to leave jobs stuck in 'queued', so don't defer assignment indefinitely
MAX_DEFER_SECONDS = 30


DestinationConfig = namedtuple('DestinationConfig', [
    'id',
    'native_spec_param',
    'partition',
    'default_cores',
    'max_cores',
    'default_walltime',
    'max_walltime',
    # jobs take a bit to dispatch, so we don't want to foul up the logic with jobs that will soon change state
    'queued_job_threshold',
    # count jobs in these destinations against this one
    'shared_thresholds',
])

COMPUTE_RESOURCE_SELECTOR = 'multi_compute_resource'
DEFAULT_DESTINATION = DestinationConfig('slurm_multi', 'nativeSpecification', 'multi', 6, 6, 36, 36, 4, [])
JETSTREAM_IU_DESTINATION = DestinationConfig('jetstream_iu_multi', 'submit_native_specification', 'multi', 10, 10, 36, 36, 4, [])

SELECTABLE_DESTINATIONS = (
    DEFAULT_DESTINATION,
    JETSTREAM_IU_DESTINATION,
    DestinationConfig('slurm_multi_development', 'nativeSpecification', 'multi', 2, 2, 2, 2, 4, []),
    DestinationConfig('stampede_normal', 'submit_native_specification', 'normal', 128, 272, 48, 48, 4, []),
    DestinationConfig('stampede_skx_normal', 'submit_native_specification', 'skx-normal', 48, 48, 48, 48, 4, []),
    DestinationConfig('stampede_development', 'submit_native_specification', 'development', 128,272,  2, 2, 4, []),
    DestinationConfig('stampede_skx_development', 'submit_native_specification', 'skx-dev', 48, 48, 2, 2, 4, []),
)

MULTI_DESTINATIONS = (
    DEFAULT_DESTINATION,
    JETSTREAM_IU_DESTINATION,
)

MULTI_LONG_DESTINATIONS = (
    DestinationConfig('slurm_multi_long', 'nativeSpecification', 'multi', 6, 6, 72, 72, 20, ['slurm_multi']),
    DestinationConfig('stampede_long', 'submit_native_specification', 'multi', 128, 272, 72, 120, 20, []),
)

FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

deferred_jobs = {}


#def __job_priority_users_group(app):
#    global JOB_PRIORITY_USERS_GROUP
#    if JOB_PRIORITY_USERS_GROUP is None:
#        group = app.model.context.query(app.model.Group).filter(
#            app.model.Group.table.c.name == JOB_PRIORITY_USERS_GROUP_NAME,
#            app.model.Group.table.c.deleted.is_(False)
#        ).first()
#        JOB_PRIORITY_USERS_GROUP = group
#    return JOB_PRIORITY_USERS_GROUP


#def __user_in_priority_group(app, user_email):
#    group = __job_priority_users_group(app)
#    user = app.model.context.query(app.model.User).filter(
#        app.model.User.table.c.email == user_email,
#        app.model.User.table.c.deleted.is_(False)
#    ).first()
#    return user and (group in [uga.group for uga in user.groups])


def __job_priority_users_group(app):
    return app.model.context.query(app.model.Group).filter(
        app.model.Group.table.c.name == JOB_PRIORITY_USERS_GROUP_NAME,
        app.model.Group.table.c.deleted.is_(False)
    ).first()


def __job_priority_users_group_members(app):
    # returns email strings, not user objects
    global JOB_PRIORITY_USERS_GROUP_CACHE_TIME
    global JOB_PRIORITY_USERS_GROUP_MEMBERS
    if not JOB_PRIORITY_USERS_GROUP_CACHE_TIME \
            or (time.time() - JOB_PRIORITY_USERS_GROUP_CACHE_TIME > JOB_PRIORITY_USERS_GROUP_CACHE_TTL):
        group = __job_priority_users_group(app)
        if group:
            app.model.context.refresh(group)
            JOB_PRIORITY_USERS_GROUP_MEMBERS = [uga.user.email for uga in group.users]
        else:
            JOB_PRIORITY_USERS_GROUP_MEMBERS = []
        JOB_PRIORITY_USERS_GROUP_CACHE_TIME = time.time()
    return JOB_PRIORITY_USERS_GROUP_MEMBERS


def __user_in_priority_group(app, user_email):
    members = __job_priority_users_group_members(app)
    return user_email in members


def __dynamic_reserved(key, app, job, user_email):
    destination_id = 'slurm_' + key
    if __user_in_priority_group(app, user_email):
        destination_id = 'reserved_' + key
        log.debug("(%s) User in priority group, job destination is: %s", job.id, destination_id)
    return destination_id


def __parse_resource_selector(job, param_dict):
    # handle job resource parameters
    try:
        # validate params
        cores = int(param_dict['__job_resource'].get('cores', 0))
        time = int(param_dict['__job_resource'].get('time', 0))
        destination_id = param_dict['__job_resource'][COMPUTE_RESOURCE_SELECTOR]
        for destination in SELECTABLE_DESTINATIONS:
            if destination.id == destination_id:
                # if 0, set to destination default
                cores = cores or destination.default_cores
                time = time or destination.max_walltime
                return (cores, time, destination)
        else:
            raise Exception("Destination '{}' not found in valid destination list".format(destination_id))
    except:
        # resource param selector not sent with tool form, job_conf.xml misconfigured
        log.exception('(%s) job resource error, keys were: %s', job.id, param_dict.keys())
        raise JobMappingException(FAILURE_MESSAGE)


def __queued_job_count(app, destination_configs):
    destination_ids = set()
    for destination_config in destination_configs:
        destination_ids.add(destination_config.id)
        [destination_ids.add(st) for st in destination_config.shared_thresholds]
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(destination_ids),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    return dict([(d, c) for d, c in job_counts])


def __get_best_destination(app, job, destination_configs):
    """Given a preference-ordered list of DestinationConfigs, attempt to determine the best place to send a job.

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
    job_counts = __queued_job_count(app, destination_configs)
    priority_destinations = []
    for destination_config in destination_configs:
        destination_id = destination_config.id
        threshold = destination_config.queued_job_threshold
        count = job_counts.get(destination_id, 0) \
            + sum([job_counts.get(shared_threshold, 0) for shared_threshold in destination_config.shared_thresholds])
        # select the first destination under the threshold
        if count <= threshold:
            log.debug("(%s) selecting preferred destination with %s queued jobs: %s", job.id, count, destination_id)
            deferred_jobs.pop(job.id, None)
            return destination_config
        heapq.heappush(priority_destinations, (count, destination_config))
    if job.id not in deferred_jobs:
        deferred_jobs[job.id] = time.time()
    elif time.time() - deferred_jobs[job.id] > MAX_DEFER_SECONDS:
        count, destination_config = heapq.heappop(priority_destinations)
        log.debug(
            "(%s) all destinations over threshold (%s), reached max deferrment, selecting least busy (ct: %s) "
            "destination: %s", job.id, destination_config.queued_job_threshold, count, destination_config.id)
        deferred_jobs.pop(job.id, None)
        return destination_config
    log.debug("(%s) all destinations over threshold, deferring job scheduling: %s", job.id, job_counts)
    raise JobNotReadyException(message="All destinations over max queued thresholds")


def __dynamic_multi_cores_time(app, job, destination_configs):

    # build the param dictionary
    param_dict = job.get_param_values(app)

    if param_dict.get('__job_resource', {}).get('__job_resource__select') != 'yes':
        log.debug("(%s) Job resource parameters not seleted", job.id)
        destination_config = __get_best_destination(app, job, destination_configs)
        cores = destination_config.default_cores
        time = destination_config.max_walltime
    else:
        log.debug("(%s) Job resource parameters seleted", job.id)
        cores, time, destination_config = __parse_resource_selector(job, param_dict)

    destination_id = destination_config.id
    destination = app.job_config.get_destination(destination_id)
    native_spec_param = destination_config.native_spec_param
    cores = min(destination_config.max_cores, cores)
    time = min(destination_config.max_walltime, time)

    # <env id="_JAVA_OPTIONS">$_JAVA_OPTIONS -Xmx@JAVA_MEM@ -Xms256m</env>
    #destination.env.append({
    #    'name': '_JAVA_OPTIONS',
    #    'value': '$_JAVA_OPTIONS -Xmx{} -Xms256m',
    #})

    # Stampede assigns whole nodes, so $SLURM_CPUS_ON_NODE is not the same as the requested number of tasks.
    # GALAXY_SLOTS should be explicitly overridden to SLURM_NTASKS in an <env> tag in Stampede destinations in
    # job_conf.xml.
    #if destination_config.force_slots:
    #    destination.env.append({
    #        'name': 'GALAXY_SLOTS',
    #        'value': '$SLURM_NTASKS',
    #    })

    #if destination_id.startswith('stampede_mpi_skx_'):
    #    cores = min(cores, 48)
    #elif destination_id.startswith('stampede_mpi_'):
    #    cores = min(cores, 272)
    #elif destination_id == 'slurm_mpi_multi_development':
    #    cores = 1
    #else:
    #    # slurm_mpi_multi
    #    cores = min(cores, 6)

    #if destination_id.endswith('_development'):
    #    time = min(time, 2)
    #elif destination_id == 'slurm_mpi_multi':
    #    time = min(time, 24)
    #else:
    #    # normal stampede destinations
    #    time = min(time, 48)

    #destination = app.job_config.get_destination(destination_id)

    # stampede_mpi_* dests already contain: --account=TG-MCB140147 --partition=... --nodes=1
    # slurm_mpi_* dests already contains: --partition=... --nodes=1
    params = [
        '--cpus-per-task=1',
        '--ntasks={}'.format(cores),
        '--time={}:00:00'.format(time),
    ]
    native_spec = destination.params.get(native_spec_param, '') + ' ' + ' '.join(params)
    destination.params[native_spec_param] = native_spec

    log.info('(%s) Returning destination: %s', job.id, destination_id)
    log.info('(%s) Native specification: %s', job.id, destination.params.get(native_spec_param))
    return destination


def dynamic_normal_reserved(app, job, user_email):
    return __dynamic_reserved('normal', app, job, user_email)


def dynamic_normal_16gb_reserved(app, job, user_email):
    return __dynamic_reserved('normal_16gb', app, job, user_email)


def dynamic_normal_16gb_long_reserved(app, job, user_email):
    return __dynamic_reserved('normal_16gb_long', app, job, user_email)


def dynamic_normal_32gb_reserved(app, job, user_email):
    return __dynamic_reserved('normal_32gb', app, job, user_email)


def dynamic_normal_64gb_reserved(app, job, user_email):
    return __dynamic_reserved('normal_64gb', app, job, user_email)


def dynamic_multi_reserved(app, job, user_email):
    destination_id = __dynamic_reserved('multi', app, job, user_email)
    if destination_id.startswith('reserved_'):
        return destination_id
    else:
        return __dynamic_multi_cores_time(app, job, MULTI_DESTINATIONS)


def dynamic_multi_long_reserved(app, job, user_email):
    destination_id = __dynamic_reserved('multi_long', app, job, user_email)
    if destination_id.startswith('reserved_'):
        return destination_id
    else:
        return __dynamic_multi_cores_time(app, job, MULTI_LONG_DESTINATIONS)
