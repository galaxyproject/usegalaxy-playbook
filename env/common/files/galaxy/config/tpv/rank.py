import random
from itertools import product
from sqlalchemy import func
from tpv.core.entities import TagType

# 0. history tags are checked and if any destinations' prefer tags match the history tags, that destination is chosen
# 1. queued counts are considered before the tag score
# 2. we make queued counts less precise to increase the importance of the prefer tags in the score

MIN_DIVISOR = 0.01
DEFAULT_DIVISOR = 3
LIMITS = {
    "bridges2": 100,
    "expanse": 64,
    "anvil": 100,
    "stampede3_skx": 20,
    "stampede3_icx": 20,
    "stampede3_spr": 20,
}

final_destinations = None

history = job.history
tags = history and history.tags

if tags and not tool.id.startswith("interactive_tool_"):
    for history_tag, dest in product([hta.user_tname for hta in tags], candidate_destinations):
        matches = list(dest.tpv_dest_tags.filter(TagType.PREFER, "scheduling", history_tag))
        if matches:
            log.debug(f"#### ({job.id=}) overriding destination due to history tag {history_tag=} in prefer tags for dest: {dest=}")
            final_destinations = [dest]
            break

if final_destinations is None and len(candidate_destinations) > 1:
    job_counts = app.model.context.query(app.model.Job.table.c.destination_id, app.model.Job.table.c.state, func.count()).filter(
        app.model.Job.table.c.destination_id.in_(d.id for d in candidate_destinations),
        app.model.Job.table.c.state.in_([app.model.Job.states.QUEUED, app.model.Job.states.RUNNING])
    ).group_by(app.model.Job.destination_id, app.model.Job.state).all()
    queued_counts_by_destination = dict((d, c) for d, s, c in job_counts if s == "queued")
    total_counts_by_destination = {k: sum(t[2] for t in job_counts if t[0] == k) for k, _, _ in job_counts}
    divisors = {k: max(DEFAULT_DIVISOR * (1 - (total_counts_by_destination.get(k, 0) / v)), MIN_DIVISOR) for k, v in LIMITS.items()}
    log.debug(f"#### ({job.id=}) {job_counts=}")
    # always simulate a few queued so the limit factor is not zeroed out
    for d in candidate_destinations:
        log.debug(f"#### ({job.id=}) {d.id} rank: ({int(max(queued_counts_by_destination.get(d.id, DEFAULT_DIVISOR), DEFAULT_DIVISOR) / divisors.get(d.id, DEFAULT_DIVISOR))}, {-1 * d.score(entity)}, ...)")
    candidate_destinations.sort(key=lambda d: (int(max(queued_counts_by_destination.get(d.id, DEFAULT_DIVISOR), DEFAULT_DIVISOR) / divisors.get(d.id, DEFAULT_DIVISOR)), -1 * d.score(entity), random.randint(0,9)))
    final_destinations = candidate_destinations

if final_destinations is None:
    final_destinations = candidate_destinations

log.debug(f"#### ({job.id=}) final rank: {[d.id for d in final_destinations]}")

final_destinations
