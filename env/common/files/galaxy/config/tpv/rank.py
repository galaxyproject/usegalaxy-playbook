import random
from sqlalchemy import func
from galaxy.jobs.mapper import JobNotReadyException

if len(candidate_destinations) > 1:
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(d.id for d in candidate_destinations),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    queued_counts_by_destination = dict((d, c) for d, c in job_counts)
    log.debug(f"#### {queued_counts_by_destination=}")
    for d in candidate_destinations:
        log.debug(f"#### {d.id} ({-1 * d.score(entity)}, {queued_counts_by_destination.get(d.id, 0)})")
    candidate_destinations.sort(key=lambda d: (-1 * d.score(entity), queued_counts_by_destination.get(d.id, 0), random.randint(0,9)))
    #raise JobNotReadyException()
    final_destinations = candidate_destinations
else:
    final_destinations = candidate_destinations
final_destinations
