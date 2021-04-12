"""
This unit test module is stretching the dynamic rules used for Galaxy Main
while using an actual Main's job_conf and job_resource_params_conf configuration
files. The rest of the stack is mocked.
"""
import logging
import pytest
import mock
import os
import time

import galaxy.model

from galaxy.jobs.mapper import JobMappingException, JobNotReadyException
from galaxy.jobs import JobConfiguration

from ... import job_router


# TODO:
#  - collection elements, HDCAs, etc.


# for test purposes we want this to be very low
job_router.MAX_DEFER_SECONDS = 2

NORMAL_NATIVE_SPEC = "--partition=normal,jsnormal --nodes=1 --ntasks=1 --time=36:00:00"
MULTI_NATIVE_SPEC = "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=36:00:00"
JETSTREAM_MULTI_NATIVE_SPEC = "--partition=multi --nodes=1 --time=36:00:00"

job_router.JOB_ROUTER_CONF_FILE = os.path.join(os.path.dirname(__file__), 'job_router_conf.yml')
MAIN_JOB_CONF = os.path.join(os.path.dirname(__file__), "job_conf.yml")
MAIN_JOB_RESOURCE_PARAMS_CONF = os.path.join(
    os.path.dirname(__file__), "job_resource_params_conf.xml")

KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
GIGABYTE = 1024 * MEGABYTE

mock_dataset = mock.Mock()
mock_dataset.get_size = lambda: os.stat('mock_path').st_size

mock_app = mock.MagicMock()
mock_app.tool_data_tables.get.return_value.get_entry.return_value = "mock_path"
mock_app.config.job_config_file = MAIN_JOB_CONF
mock_app.config.job_resource_params_file = MAIN_JOB_RESOURCE_PARAMS_CONF
mock_app.job_config = JobConfiguration(mock_app)
mock_job = mock.Mock()
mock_job.parameters = []
mock_job.id = 1


@mock.patch.object(job_router, '__queued_job_count')
@mock.patch("os.stat")
def __test_job_router(testconfig, os_stat, queued_job_count, user_email="test@example.org"):
    tool_id = testconfig["tool"].id
    if '/' in tool_id:
        tool_id = tool_id.split('/')[-2]
    # Mock the size of ref/input data
    os_stat.return_value.st_size = testconfig.get("ref_size", 0)

    mock_job.get_param_values.return_value = testconfig["tool"].params
    queued_job_count.return_value = testconfig.get("queued_job_counts", {})
    resource_params = testconfig.get('resource_params', {})

    for i in range(0, 3):
        try:
            destination = job_router.job_router(mock_app, mock_job, testconfig["tool"], resource_params, user_email)
            break
        except JobNotReadyException:
            time.sleep(1)

    native_spec = destination.params.get('nativeSpecification')
    if not native_spec:
        native_spec = destination.params.get('native_specification')
    if not native_spec:
        native_spec = destination.params['submit_native_specification']

    assert native_spec == testconfig["return_native_spec"]

    if "return_destination_id" in testconfig:
        assert destination.id == testconfig["return_destination_id"]


#
# Tool mappings
#

def test_normal():
    tool = mock.Mock()
    tool.id = "cat1"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC,
        "return_destination_id": "slurm_normal",
    }
    __test_job_router(test)


def test_normal_legacy():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/bgruening/text_processing/tp_cut_tool/1.0.0"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC,
        "return_destination_id": "slurm_normal_legacy",
    }
    __test_job_router(test)


def test_normal_16gb():
    tool = mock.Mock()
    tool.id = "join1"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC + " --mem=15360",
        "return_destination_id": "slurm_normal_16gb",
    }
    __test_job_router(test)


def test_normal_32gb():
    tool = mock.Mock()
    tool.id = "Interval2Maf1"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC.replace('36:', '24:') + " --mem=30720",
        "return_destination_id": "slurm_normal_32gb",
    }
    __test_job_router(test)


def test_normal_64gb():
    tool = mock.Mock()
    tool.id = "wig_to_bigWig"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC.replace('36:', '4:') + " --mem=61440",
        "return_destination_id": "slurm_normal_64gb",
    }
    __test_job_router(test)


def test_multi():
    tool= mock.Mock()
    tool.id = "bowtie2"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_multi_legacy():
    tool= mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/devteam/bowtie2/bowtie2/0.2"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi_legacy",
    }
    __test_job_router(test)


def test_require_login():
    tool= mock.Mock()
    tool.id = "deseq2"
    tool.params = {}
    test = {
        "tool": tool,
    }
    with pytest.raises(JobMappingException):
        __test_job_router(test, user_email=None)


def test_repeat_input_param():
    tool= mock.Mock()
    tool.id = "spades"
    tool.params = {"libraries": {"files": [{"file_type": {"type": "separate", "fwd_reads": mock_dataset}}]}}
    test = {
        "ref_size": 1024,
        "tool": tool,
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_rnastar_indexed_small():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
    tool.params = {"refGenomeSource": {"geneSource": "indexed", "GTFconditional": {"genomeDir": "hg19"}}}
    test = {
        "ref_size": 12 * GIGABYTE,
        "tool": tool,
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_rnastar_indexed_large():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
    tool.params = {"refGenomeSource": {"geneSource": "indexed", "GTFconditional": {"genomeDir": "hg19"}}}
    test = {
        "ref_size": 24 * GIGABYTE,
        "tool": tool,
        "return_native_spec": "--partition=xlarge --nodes=1 --time=36:00:00",
        "return_destination_id": "jetstream_tacc_xlarge",
    }
    __test_job_router(test)


def test_rnastar_history_small():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
    tool.params = {"refGenomeSource": {"geneSource": "history", "genomeFastaFiles": mock_dataset}}
    test = {
        "ref_size": 2 * GIGABYTE,
        "tool": tool,
        "return_native_spec": "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=36:00:00",
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_rnastar_history_large():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
    tool.params = {"refGenomeSource": {"geneSource": "history", "genomeFastaFiles": mock_dataset}}
    test = {
        "ref_size": 4 * GIGABYTE,
        "tool": tool,
        "return_native_spec": "--partition=xlarge --nodes=1 --time=36:00:00",
        "return_destination_id": "jetstream_tacc_xlarge",
    }
    __test_job_router(test)


def test_kraken_bacteria():
    tool = mock.Mock()
    tool.id = "kraken"
    tool.params = {"kraken_database": "bacteria"}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=skx-normal --nodes=1 --account=TG-MCB140147 --ntasks=48 --time=36:00:00",
        "return_destination_id": "stampede_skx_normal",
    }
    __test_job_router(test)


def test_kraken_other():
    tool = mock.Mock()
    tool.id = "kraken"
    tool.params = {"kraken_database": "foo"}
    test = {
        "tool": tool,
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_align_families():
    tool = mock.Mock()
    tool.id = "align_families"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=192:00:00",
        "return_destination_id": "slurm_multi_long",
    }
    __test_job_router(test)


def test_multi_long():
    tool = mock.Mock()
    tool.id = "fasterq_dump"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=72:00:00",
        "return_destination_id": "slurm_multi_long",
    }
    __test_job_router(test)


def test_bridges_normal():
    tool = mock.Mock()
    tool.id = "abyss-pe"
    tool.params = {}
    test = {
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=72:00:00 --mem={288 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_normalize_small():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": True}
    test = {
        "ref_size": 8 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=72:00:00 --mem={240 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_normalize_medium():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": True}
    test = {
        "ref_size": 64 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={480 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_normalize_large():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": True}
    test = {
        "ref_size": 128 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={720 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_no_normalize_small():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": False}
    test = {
        "ref_size": 8 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={480 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_no_normalize_medium():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": False}
    test = {
        "ref_size": 64 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={720 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_no_normalize_large():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "single", "input": mock_dataset}}, "norm": False}
    test = {
        "ref_size": 128 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={960 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_trinity_no_normalize_large_paired():
    tool = mock.Mock()
    tool.id = "trinity"
    tool.params = {"pool": {"inputs": {"paired_or_single": "paired", "left_input": [mock_dataset]}}, "norm": False}
    test = {
        "ref_size": 128 * GIGABYTE,
        "tool": tool,
        #"return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={960 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_stampede_normal():
    tool = mock.Mock()
    tool.id = "megablast_wrapper"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=normal --nodes=1 --account=TG-MCB140147 --ntasks=68 --time=36:00:00",
        "return_destination_id": "stampede_normal",
    }
    __test_job_router(test)


def test_deseq2():
    tool = mock.Mock()
    tool.id = "deseq2"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


#
# Features
#

def test_tool_mapping_alias():
    tool = mock.Mock()
    tool.id = "rna_starsolo"
    tool.params = {"refGenomeSource": {"geneSource": "history", "genomeFastaFiles": mock_dataset}}
    test = {
        "ref_size": 4 * GIGABYTE,
        "tool": tool,
        "return_native_spec": "--partition=xlarge --nodes=1 --time=36:00:00",
        "return_destination_id": "jetstream_tacc_xlarge",
    }
    __test_job_router(test)


def test_priority_group_override():
    tool = mock.Mock()
    tool.id = "cat1"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=reserved,jsreserved --nodes=1 --ntasks=1 --time=36:00:00",
        "return_destination_id": "reserved_slurm_normal",
    }
    destinations = {"slurm_normal": "reserved_slurm_normal"}
    with mock.patch.object(job_router, '__user_group_mappings', mock.Mock(return_value=destinations)):
        __test_job_router(test)


def test_resource_selector():
    tool = mock.Mock()
    tool.id = "bowtie2"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "jetstream_multi"},
        "return_native_spec": "--partition=multi --nodes=1 --time=36:00:00",
        "return_destination_id": "jetstream_iu_multi",
    }
    __test_job_router(test)


def test_resource_decrease():
    tool = mock.Mock()
    tool.id = "bowtie2"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "stampede_normal", "ntasks": 24, "time": 12},
        "return_native_spec": "--partition=normal --nodes=1 --account=TG-MCB140147 --ntasks=24 --time=12:00:00",
        "return_destination_id": "stampede_normal",
    }
    __test_job_router(test)


def test_resource_cap():
    tool = mock.Mock()
    tool.id = "bowtie2"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "stampede_normal", "ntasks": 512, "time": 72},
        "return_native_spec": "--partition=normal --nodes=1 --account=TG-MCB140147 --ntasks=272 --time=48:00:00",
        "return_destination_id": "stampede_normal",
    }
    __test_job_router(test)


def test_resource_no_override():
    tool = mock.Mock()
    tool.id = "spades"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "bridges_normal", "mem": 720 * KILOBYTE},
        #"return_native_spec": f"--partition=RM --time=36:00:00 --mem={288 * KILOBYTE}",
        "return_native_spec": f"--partition=RM --time=36:00:00",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_resource_group_override():
    tool = mock.Mock()
    tool.id = "spades"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "bridges_normal", "mem": 720 * KILOBYTE},
        "return_native_spec": f"--partition=RM --time=36:00:00 --mem={720 * KILOBYTE}",
        "return_destination_id": "bridges_normal",
    }
    options = {"param_overrides": True}
    with mock.patch.object(job_router, '__user_group_mappings', mock.Mock(return_value=options)):
        __test_job_router(test)


def test_resource_group_override_cap():
    tool = mock.Mock()
    tool.id = "spades"
    tool.params = {}
    test = {
        "tool": tool,
        "resource_params": {"multi_compute_resource": "bridges_normal", "mem": 912 * KILOBYTE},
        "return_native_spec": f"--partition=RM --time=36:00:00 --mem={720 * KILOBYTE}",
        "return_destination_id": "bridges_normal",
    }
    options = {"param_overrides": True}
    with mock.patch.object(job_router, '__user_group_mappings', mock.Mock(return_value=options)):
        __test_job_router(test)


def test_best_destination_roundup():
    tool = mock.Mock()
    tool.id = "hisat2"
    test = {
        "tool": tool,
        "queued_job_counts": {
            "slurm_multi": 3,
            "jetstream_iu_multi": 0,
        },
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_best_destination_jetstream():
    tool = mock.Mock()
    tool.id = "hisat2"
    test = {
        "tool": tool,
        "queued_job_counts": {
            "slurm_multi": 10,
            "jetstream_iu_multi": 2,
        },
        "return_native_spec": JETSTREAM_MULTI_NATIVE_SPEC,
        "return_destination_id": "jetstream_iu_multi",
    }
    __test_job_router(test)


def test_best_destination_with_queue_factor_roundup():
    # both over threshold so it should go to the queue with the lowest, but jetstream has a queue factor of 2
    tool = mock.Mock()
    tool.id = "hisat2"
    test = {
        "tool": tool,
        "queued_job_counts": {
            "slurm_multi": 10,
            "jetstream_iu_multi": 6,
        },
        "return_native_spec": MULTI_NATIVE_SPEC,
        "return_destination_id": "slurm_multi",
    }
    __test_job_router(test)


def test_best_destination_with_queue_factor_jetstream():
    tool = mock.Mock()
    tool.id = "hisat2"
    test = {
        "tool": tool,
        "queued_job_counts": {
            "slurm_multi": 14,
            "jetstream_iu_multi": 6,
        },
        "return_native_spec": JETSTREAM_MULTI_NATIVE_SPEC,
        "return_destination_id": "jetstream_iu_multi",
    }
    __test_job_router(test)
