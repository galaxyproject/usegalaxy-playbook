import glob
import math
import os


def cached_index_mem(job, app, tool, index_source, index_param, index_table, index_files):
    """Return the GB to request for the built-in (cached) index a job uses, or 0 if it uses none.

    A built-in index is not an input dataset, so input_size misses it. The aligner holds the index in RAM and
    samtools sort runs in the same job, so request 1.5x the on-disk index size + 2 GB. The 1.5x covers per-core
    overhead, since cores are scaled from mem at ~3.5 GB/core.

    index_source: the conditional value that selects a cached index, as passed to helpers.job_args_match
    index_param: "|"-separated path to the index select param
    index_table: the data table that select is built from
    index_files: globs, relative to the table's path column, of the files the aligner loads
    """
    try:
        if not helpers.job_args_match(job, app, index_source):
            return 0
        value = job.get_param_values(app)
        for key in index_param.split("|"):
            value = value[key]
        path = app.tool_data_tables.get(index_table).get_entry("value", value, "path")
        files = [f for pattern in index_files for f in glob.glob(glob.escape(path) + pattern)] if path else []
        if not files:
            log.warning("No '%s' index files found for '%s' at: %s", index_table, value, path)
            return 0
        return math.ceil(sum(os.path.getsize(f) for f in files) / 1024**3 * 1.5 + 2)
    except Exception:
        log.exception("Failed to size cached index for tool: %s", tool.id)
        return 0
