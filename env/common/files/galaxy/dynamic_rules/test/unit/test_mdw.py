"""
This unit test module is stretching the dynamic rules used for Galaxy Main
while using an actual Main's job_conf and job_resource_params_conf configuration
files. The rest of the stack is mocked.
"""
import pytest
import mock
import os

from galaxy.jobs.mapper import JobMappingException
from galaxy.jobs import JobConfiguration

from ... import multi_dynamic_walltime as mdw

MAIN_JOB_CONF = os.path.join(os.path.dirname(__file__), "job_conf.xml")
MAIN_JOB_RESOURCE_PARAMS_CONF = os.path.join(
    os.path.dirname(__file__), "job_resource_params_conf.xml")

KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
GIGABYTE = 1024 * MEGABYTE

tool_rnastar_indexed = mock.Mock()
tool_rnastar_indexed.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
tool_rnastar_indexed.params_from_strings.return_value = {"refGenomeSource": {"geneSource": "indexed",
                                                                             "GTFconditional": {"genomeDir": "hg19"}}}
tool_rnastar_history = mock.Mock()
tool_rnastar_history.id = "toolshed.g2.bx.psu.edu/repos/iuc/rgrnastar/rna_star/2.6.0b-1"
tool_rnastar_history.params_from_strings.return_value = {"refGenomeSource": {"geneSource": "history",
                                                                            "genomeFastaFiles": mock.Mock()}}
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
test_configs = [
    # tool: rnastar
    # indexed reference
    {"ref_size": 1 * GIGABYTE,  # 1
     "tool": tool_rnastar_indexed,
     "sbatch_node": "jetstream-iu-large",
     "resource_params": {"multi_bridges_compute_resource": "slurm_multi"},
     "return_nativeSpecification": "--partition=multi --nodes=1 --cpus-per-task=6 --time=36:00:00 --mem=8192",
     "return_destination_id": "slurm_multi"},
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

mock_app = mock.MagicMock()
mock_app.tool_data_tables.get.return_value.get_entry.return_value = "mock_path"
mock_app.config.job_config_file = MAIN_JOB_CONF
mock_app.config.job_resource_params_file = MAIN_JOB_RESOURCE_PARAMS_CONF
mock_app.job_config = JobConfiguration(mock_app)
mock_job = mock.Mock()
mock_job.parameters = []
mock_job.id = 1


def test_user_presence():
    with pytest.raises(JobMappingException):
        mdw.dynamic_multi_bridges_select(
            mock_app, tool_rnastar_indexed, mock_job, user_email=None, resource_params=[])


@mock.patch("subprocess.Popen")
@mock.patch("os.stat")
def test_dynamic_multi_bridges_select(os_stat, subprocess_popen):
    for i, testconfig in enumerate(test_configs):
        print("TESTING CASE {0}".format(i + 1))
        print(testconfig)
        # Retrieve the tool id from mock object
        tool_id = testconfig["tool"].id.split('/')[-2]
        # Retrieve destination from job conf
        tool_destination = mock_app.job_config.tools[
            tool_id][0].get("destination")
        # Mock the size of ref data
        os_stat.return_value.st_size = testconfig["ref_size"]
        # Mock sbatch test run
        mock_sbatch = (
            "sbatch: Job 1968650 to start at 2020-04-11T16:58:40 using 10 processors on nodes {} in partition "
            "multi".format(testconfig["sbatch_node"])
        )
        subprocess_popen.return_value.stderr.read.return_value = mock_sbatch
        subprocess_popen.return_value.returncode = 0
        destination = None
        if tool_destination == "dynamic_multi_bridges_select":
            destination = mdw.dynamic_multi_bridges_select(
                mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
        elif tool_destination == "dynamic_local_stampede_select_dynamic_walltime":
            destination = mdw.dynamic_local_stampede_select_dynamic_walltime(
                mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
        elif tool_destination == "dynamic_stampede_select":
            destination = mdw.dynamic_stampede_select(
                mock_app, testconfig["tool"], mock_job, "test@example.com", testconfig["resource_params"])
        # print(destination)
        if "return_nativeSpecification" in testconfig:
            assert destination.params["nativeSpecification"] == testconfig[
                "return_nativeSpecification"]
        if "return_submit_native_specification" in testconfig:
            assert destination.params["submit_native_specification"] == testconfig[
                "return_submit_native_specification"]
        if "return_destination_id" in testconfig:
            assert destination.id == testconfig["return_destination_id"]
