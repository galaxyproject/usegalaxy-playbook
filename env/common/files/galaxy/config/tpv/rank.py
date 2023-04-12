import random
from itertools import product
from sqlalchemy import func
from tpv.core.entities import TagType

# 0. history tags are checked and if any destinations' prefer tags match the history tags, that destination is chosen
# 1. queued counts are considered before the tag score
# 2. we make queued counts less precise to increase the importance of the prefer tags in the score
# 3. prefer destinations with less memory and fewer cores when other factors are equal

final_destinations = None

if job.history.tags and not tool.id.startswith("interactive_tool_"):
    for history_tag, dest in product([hta.user_tname for hta in job.history.tags], candidate_destinations):
        matches = list(dest.tpv_dest_tags.filter(TagType.PREFER, "scheduling", history_tag))
        if matches:
            log.debug(f"#### ({job.id=}) overriding destination due to history tag {history_tag=} in prefer tags for dest: {dest=}")
            final_destinations = [dest]
            break

if final_destinations is None and len(candidate_destinations) > 1:
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, func.count(app.model.Job.table.c.destination_id)).filter(
        app.model.Job.table.c.destination_id.in_(d.id for d in candidate_destinations),
        app.model.Job.table.c.state == app.model.Job.states.QUEUED
    ).group_by(app.model.Job.destination_id).all()
    queued_counts_by_destination = dict((d, c) for d, c in job_counts)
    log.debug(f"#### ({job.id=}) {queued_counts_by_destination=}")
    candidate_destinations.sort(key=lambda d: (int(queued_counts_by_destination.get(d.id, 0) / 3), -1 * d.score(entity), d.max_accepted_mem, d.max_accepted_cores, random.randint(0,9)))
    for d in candidate_destinations:
        log.debug(f"#### ({job.id=}) {d.id}: ({int(queued_counts_by_destination.get(d.id, 0) / 3)}, {-1 * d.score(entity)}, {d.max_accepted_mem}, {d.max_accepted_cores})")
    final_destinations = candidate_destinations

if final_destinations is None:
    final_destinations = candidate_destinations

final_destinations
