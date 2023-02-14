import random
from sqlalchemy import func
from galaxy.jobs.mapper import JobNotReadyException

# this is the same as the regular rank function with the following differences:
#
# 1. queued counts are considered before the tag score
# 2. we make queued counts less precise to increase the importance of the prefer tags in the score
# 3. prefer destinations with less memory and fewer cores when other factors are equal

if len(candidate_destinations) > 1:
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(d.id for d in candidate_destinations),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    queued_counts_by_destination = dict((d, c) for d, c in job_counts)
    log.debug(f"#### {queued_counts_by_destination=}")
    candidate_destinations.sort(key=lambda d: (int(queued_counts_by_destination.get(d.id, 0) / 3), -1 * d.score(entity), d.max_accepted_mem, d.max_accepted_cores, random.randint(0,9)))
    for d in candidate_destinations:
        log.debug(f"#### {d.id}: ({int(queued_counts_by_destination.get(d.id, 0) / 3)}, {-1 * d.score(entity)}, {d.max_accepted_mem}, {d.max_accepted_cores})")
    #raise JobNotReadyException()
    final_destinations = candidate_destinations
else:
    final_destinations = candidate_destinations
final_destinations
