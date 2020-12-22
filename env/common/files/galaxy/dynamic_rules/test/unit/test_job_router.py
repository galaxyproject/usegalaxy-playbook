"""
This unit test module is stretching the dynamic rules used for Galaxy Main
while using an actual Main's job_conf and job_resource_params_conf configuration
files. The rest of the stack is mocked.
"""
import logging
import pytest
import mock
import os

import galaxy.model

from galaxy.jobs.mapper import JobMappingException
from galaxy.jobs import JobConfiguration

#from ... import multi_dynamic_walltime as mdw
from ... import job_router

NORMAL_NATIVE_SPEC = "--partition=normal,jsnormal --nodes=1 --ntasks=1 --time=36:00:00"
MULTI_NATIVE_SPEC = "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=36:00:00"

job_router.JOB_ROUTER_CONF_FILE = os.path.join(os.path.dirname(__file__), 'job_router_conf.yml')
#MAIN_JOB_CONF = os.path.join(os.path.dirname(__file__), "job_conf.xml")
MAIN_JOB_CONF = os.path.join(os.path.dirname(__file__), "job_conf.yml")
MAIN_JOB_RESOURCE_PARAMS_CONF = os.path.join(
    os.path.dirname(__file__), "job_resource_params_conf.xml")

KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
GIGABYTE = 1024 * MEGABYTE

mock_dataset = mock.Mock()
mock_dataset.get_size = lambda: os.stat('mock_path').st_size



tool_bowtie2_indexed = mock.Mock()
tool_bowtie2_indexed.id = "toolshed.g2.bx.psu.edu/repos/devteam/bowtie2/bowtie2/2.3.4.2"
tool_bowtie2_indexed.params_from_strings.return_value = {"reference_genome": {
    "source": "indexed"}}
tool_tophat2_indexed = mock.Mock()
tool_tophat2_indexed.id = "toolshed.g2.bx.psu.edu/repos/devteam/tophat2/tophat2/2.1.1"
tool_tophat2_indexed.params_from_strings.return_value = {"refGenomeSource": {
    "genomeSource": "indexed"}}
tool_tophat2_history = mock.Mock()
tool_tophat2_history.id = "toolshed.g2.bx.psu.edu/repos/devteam/tophat2/tophat2/2.1.1"
tool_tophat2_history.params_from_strings.return_value = {"refGenomeSource": {
    "genomeSource": "history"}}
tool_hisat2_indexed = mock.Mock()
tool_hisat2_indexed.id = "toolshed.g2.bx.psu.edu/repos/iuc/hisat2/hisat2/2.1.0+galaxy4"
tool_hisat2_indexed.params_from_strings.return_value = {"reference_genome": {
    "source": "indexed"}}
tool_hisat2_history = mock.Mock()
tool_hisat2_history.id = "toolshed.g2.bx.psu.edu/repos/iuc/hisat2/hisat2/2.1.0+galaxy4"
tool_hisat2_history.params_from_strings.return_value = {"reference_genome": {
    "source": "history"}}
tool_align_families = mock.Mock()
tool_align_families.id = "toolshed.g2.bx.psu.edu/repos/nick/dunovo/align_families/2.15"

"""
The following configuration list provides dicts with both input params and
expected output params (prefixed with 'return_').
"""
"""
test_configs = [
    # tool: rnastar
    # indexed reference
    #{"ref_size": 1 * GIGABYTE,  # 1
    {"ref_size": 23 * GIGABYTE,  # 1
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
     "resource_params": {},
     #"return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --bork",
     "return_nativeSpecification": "--partition=xlarge --nodes=1 --time=36:00:00",
     #"return_destination_id": "slurm_multi"},
     "return_destination_id": "jetstream_tacc_xlarge"},
    {"ref_size": 1 * GIGABYTE,  # 2
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "jetstream_multi"},
     "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
     "return_destination_id": "jetstream_iu_multi"},
    {"ref_size": 1 * GIGABYTE,  # 3
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "bridges_normal"},
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=8192",
     "return_destination_id": "bridges_normal"},
    {"ref_size": 1 * GIGABYTE,  # 4
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi_development"},
     "return_nativeSpecification": "--partition=normal --nodes=1 --cpus-per-task=2 --time=00:30:00 --mem-per-cpu=5120 --mem=8192",
     "return_destination_id": "slurm_multi_development"},
    {"ref_size": 100 * GIGABYTE,  # 5
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi_development"},
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    {"ref_size": 500 * GIGABYTE,  # 6
     "tool": tool_rnastar_indexed,
     "sbatch_node": "roundup",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi_development"},
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    #{"ref_size": 1000 * GIGABYTE,  # 7
    # "tool": tool_rnastar_indexed,
    # "sbatch_node": "jetstream-tacc-large",
    # "resource_params": {"multi_bridges_compute_resource": "slurm_multi_development"},
    # "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
    # "return_destination_id": "bridges_normal"},
    # reference from history
    {"ref_size": 500 * MEGABYTE,  # 8
     "tool": tool_rnastar_history,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --mem=8192",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 1 * GIGABYTE,  # 9
     "tool": tool_rnastar_history,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --mem=13312",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 100 * GIGABYTE,  # 10
     "tool": tool_rnastar_history,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    # without explicit destination
    {"ref_size": 1 * GIGABYTE,  # 11
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": None,
     "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
     "return_destination_id": "jetstream_iu_multi"},
    {"ref_size": 50 * GIGABYTE,  # 12
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": None,
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    {"ref_size": 50 * GIGABYTE,
     "tool": tool_rnastar_indexed,  # 13
     "sbatch_node": "jetstream-iu-large",
     "resource_params": None,
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    {"ref_size": 1000 * GIGABYTE,  # 14
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": None,
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},
    # with different cluster prefixes
    #{"ref_size": 500 * MEGABYTE,  # 15
    # "tool": tool_rnastar_indexed,
    # "sbatch_node": "jetstream-tacc-large",
    # "resource_params": None,
    # "return_submit_native_specification": "--partition=multi --nodes=1 --time=36:00:00",
    # "return_destination_id": "jetstream_tacc_multi"},
    {"ref_size": 500 * MEGABYTE,  # 16
     "tool": tool_rnastar_indexed,
     "sbatch_node": "roundup",
     "resource_params": None,
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --mem=8192",
     "return_destination_id": "slurm_multi"},
    #{"ref_size": 500 * MEGABYTE,  # 17
    # "tool": tool_rnastar_indexed,
    # "sbatch_node": "jetstream-tacc-large",
    # "resource_params": None,
    # "return_submit_native_specification": "--partition=multi --nodes=1 --time=36:00:00",
    # "return_destination_id": "jetstream_tacc_multi"},
    {"ref_size": 500 * MEGABYTE,  # 18
     "tool": tool_rnastar_indexed,
     "sbatch_node": "roundup",
     "resource_params": None,
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --mem=8192",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 10 * GIGABYTE,  # 19
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "jetstream_multi"},
     "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
     "return_destination_id": "jetstream_iu_multi"},
    {"ref_size": 30 * GIGABYTE,  # 20
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "jetstream_multi"},
     "return_submit_native_specification": "-p LM --constraint=LM --time=48:00:00 --mem=147456",
     "return_destination_id": "bridges_normal"},

    # tool: bowtie
    {"ref_size": 1 * GIGABYTE,  # 21
     "tool": tool_bowtie2_indexed,
     "sbatch_node": "roundup",
     "resource_params": None,
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 1 * GIGABYTE,  # 22
     "tool": tool_bowtie2_indexed,
     "sbatch_node": "roundup",
     "resource_params": None,
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    #{"ref_size": 1 * GIGABYTE,  # 23
    # "tool": tool_bowtie2_indexed,
    # "sbatch_node": "jetstream-tacc-large",
    # "resource_params": None,
    # "return_submit_native_specification": "--partition=multi --nodes=1 --time=36:00:00",
    # "return_destination_id": "jetstream_tacc_multi"},
    #{"ref_size": 1 * GIGABYTE,  # 24
    # "tool": tool_bowtie2_indexed,
    # "sbatch_node": "jetstream-iu-large",
    # "resource_params": None,
    # "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
    # "return_destination_id": "jetstream_iu_multi"},

    # tool: tophat2
    {"ref_size": 1 * GIGABYTE,  # 25
     "tool": tool_tophat2_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": None,
     "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
     "return_destination_id": "jetstream_iu_multi"},
    {"ref_size": 20 * GIGABYTE,  # 26
     "tool": tool_tophat2_indexed,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 20 * GIGABYTE,  # 27
     "tool": tool_tophat2_history,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_submit_native_specification": "--partition=normal --nodes=1 --cpus-per-task=16 --time=48:00:00 --account=TG-MCB140147",
     "return_destination_id": "stampede_normal"},

    # tool: hisat2
    {"ref_size": 500 * MEGABYTE,  # 28
     "tool": tool_hisat2_indexed,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 20 * GIGABYTE,  # 29
     "tool": tool_hisat2_indexed,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 50 * GIGABYTE,  # 30
     "tool": tool_hisat2_indexed,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
     "return_destination_id": "slurm_multi"},
    {"ref_size": 20 * GIGABYTE,  # 31
     "tool": tool_hisat2_history,
     "sbatch_node": "roundup",
     "resource_params": {"tacc_compute_resource": "stampede_normal"},
     "return_submit_native_specification": "--partition=normal --nodes=1 --cpus-per-task=16 --time=48:00:00 --account=TG-MCB140147",
     "return_destination_id": "stampede_normal"},


    # align_families tool
    # Has a case in the MDW but the job_conf would never send it there
    #
    # {"ref_size": 1 * GIGABYTE,
    #  "tool": tool_align_families,
    #  "sbatch_node": "roundup",
    #  "resource_params": None,
    #  "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=96:00:00",
    #  "return_destination_id": "slurm_multi"},

    # DLSSDW all explicit destinations
    # No tools seem to be mapped here through jobconf yet
    #
    # {"ref_size": 1 * GIGABYTE,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"tacc_compute_resource": "slurm_multi"},
    #  "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00",
    #  "return_destination_id": "slurm_multi"},
    # {"ref_size": 1 * GIGABYTE,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"tacc_compute_resource": "slurm_multi_development"},
    #  "return_nativeSpecification": "--partition=normal --nodes=1 --cpus-per-task=2 --time=00:30:00 --mem-per-cpu=5120",
    #  "return_destination_id": "slurm_multi_development"},
    # {"ref_size": 1 * GIGABYTE,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"tacc_compute_resource": "stampede_development"},
    #  "return_submit_native_specification": "--partition=development --nodes=1 --cpus-per-task=16 --time=00:30:00 --account=TG-MCB140147",
    #  "return_destination_id": "stampede_development"},
    # {"ref_size": 1 * GIGABYTE,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"tacc_compute_resource": "jetstream_multi"},
    #  "return_submit_native_specification": "--partition=multi --time=36:00:00 --mem=28672",
    #  "return_destination_id": "jetstream_iu_multi"},

    # DSS all explicit destinations
    # No tools seem to be mapped here through jobconf yet

    # {"ref_size": 1024 ** 4,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"stampede_compute_resource": "stampede_normal"},
    #  "return_submit_native_specification": "--partition=normal --nodes=1 --cpus-per-task=16 --time=48:00:00 --account=TG-MCB140147",
    #  "return_destination_id": "stampede_normal"},
    # {"ref_size": 1024 ** 4,
    #  "tool": tool_rnastar_indexed,
    #  "sbatch_node": "jetstream-iu-large",
    #  "resource_params": {"stampede_compute_resource": "stampede_development"},
    #  "return_submit_native_specification": "--partition=development --nodes=1 --cpus-per-task=16 --time=00:30:00 --account=TG-MCB140147",
    #  "return_destination_id": "stampede_development"},
]
"""

mock_app = mock.MagicMock()
mock_app.tool_data_tables.get.return_value.get_entry.return_value = "mock_path"
mock_app.config.job_config_file = MAIN_JOB_CONF
mock_app.config.job_resource_params_file = MAIN_JOB_RESOURCE_PARAMS_CONF
mock_app.job_config = JobConfiguration(mock_app)
mock_job = mock.Mock()
mock_job.parameters = []
mock_job.id = 1


#def test_user_presence():
#    with pytest.raises(JobMappingException):
#        mdw.dynamic_multi_bridges_select(
#            mock_app, tool_rnastar_indexed, mock_job, user_email=None, resource_params=[])


@mock.patch("subprocess.Popen")
@mock.patch("os.stat")
def __test_job_router(testconfig, os_stat, subprocess_popen):
    #for i, testconfig in enumerate(test_configs):
    #print("TESTING CASE {0}".format(i + 1))
    #print(testconfig)
    # Retrieve the tool id from mock object
    tool_id = testconfig["tool"].id
    if '/' in tool_id:
        tool_id = tool_id.split('/')[-2]
    # Retrieve destination from job conf
    #tool_destination = mock_app.job_config.tools[tool_id][0].get("destination")
    # Mock the size of ref data
    os_stat.return_value.st_size = testconfig.get("ref_size", 0)
    # Mock sbatch test run
    #mock_sbatch = (
    #    "sbatch: Job 1968650 to start at 2020-04-11T16:58:40 using 10 processors on nodes {} in partition "
    #    "multi".format(testconfig["sbatch_node"])
    #)
    #subprocess_popen.return_value.stderr.read.return_value = mock_sbatch
    subprocess_popen.return_value.returncode = 0
    destination = None
    mock_job.get_param_values.return_value = testconfig["tool"].params
    destination = job_router.job_router(mock_app, mock_job, testconfig["tool"], {}, "test@example.org")
    #if tool_destination == "dynamic_multi_bridges_select":
    #    destination = mdw.dynamic_multi_bridges_select(
    #        mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
    #elif tool_destination == "dynamic_local_stampede_select_dynamic_walltime":
    #    destination = mdw.dynamic_local_stampede_select_dynamic_walltime(
    #        mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
    #elif tool_destination == "dynamic_stampede_select":
    #    destination = mdw.dynamic_stampede_select(
    #        mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
    #elif tool_destination == "dynamic_rnastar":
    #    destination = mdw.dynamic_rnastar(
    #        mock_app, testconfig["tool"], mock_job, "test@example.com")
    #else:
    #    raise("Unknown destination %s" % tool_destination)
    # print(destination)
    native_spec = destination.params.get('nativeSpecification')
    if not native_spec:
        native_spec = destination.params.get('native_specification')
    if not native_spec:
        native_spec = destination.params['submit_native_specification']

    assert native_spec == testconfig["return_native_spec"]

    #if "return_nativeSpecification" in testconfig:
    #    assert native_spec == testconfig["return_nativeSpecification"]
    #if "return_submit_native_specification" in testconfig:
    #    assert native_spec == testconfig["return_submit_native_specification"]

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
        "return_native_spec": NORMAL_NATIVE_SPEC + " --mem=30720",
        "return_destination_id": "slurm_normal_32gb",
    }
    __test_job_router(test)


def test_normal_64gb():
    tool = mock.Mock()
    tool.id = "wig_to_bigWig"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": NORMAL_NATIVE_SPEC + " --mem=61440",
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


def test_rnastar_indexed_small():
    tool = mock.Mock()
    tool.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
    tool.params = {"refGenomeSource": {"geneSource": "indexed", "GTFconditional": {"genomeDir": "hg19"}}}
    test = {
        "ref_size": 12 * GIGABYTE,
        "tool": tool,
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
        "return_native_spec": "--partition=multi,jsmulti --nodes=1 --ntasks=6 --time=36:00:00",
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
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
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
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
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
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
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
        "return_native_spec": "--partition=skx-normal --nodes=1 --account=TG-MCB140147 --ntasks=48 --time=24:00:00",
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
    tool.id = "unicycler"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=72:00:00 --mem={288 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=72:00:00 --mem={240 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={480 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={720 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={480 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={720 * KILOBYTE}",
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
        "return_native_spec": f"--partition=LM --constraint=LM&EGRESS --time=96:00:00 --mem={960 * KILOBYTE}",
        "return_destination_id": "bridges_normal",
    }
    __test_job_router(test)


def test_stampede_normal():
    tool = mock.Mock()
    tool.id = "ncbi_blastn_wrapper"
    tool.params = {}
    test = {
        "tool": tool,
        "return_native_spec": "--partition=normal --nodes=1 --account=TG-MCB140147 --ntasks=68 --time=24:00:00",
        "return_destination_id": "stampede_normal",
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
        #"resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
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


# TODO:
#  - resource selector
#  - resource overrides
#  - queued job threshold stuff (but probably test this in production first)
