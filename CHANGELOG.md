# usegalaxy-playbook change log

This is a log of any changes that were made manually that could not easily be codified in to Ansible. Changes made
prior to the first entry have not been logged.


### Thu Nov  2 21:05:55 CDT 2023

Manually fixed the (legacy) TS dep
`/cvmfs/main.galaxyproject.org/deps/perl/5.18.1/iuc/package_perl_5_18/114b6af405fa/env.sh` for
`toolshed.g2.bx.psu.edu/repos/bgruening/text_processing/tp_multijoin_tool/1.0.0`

### Mon Oct 30 14:09:13 CDT 2023

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/devteam/logistic_regression_vif/LogisticRegression/1.0.1` - Has only been run 151 times
  (mostly by Marten's testbot) since the beginning of Main, and it errored all but 5 of those times. Depends on an R
  package (car) that is not installed.
- `toolshed.g2.bx.psu.edu/repos/devteam/quality_filter/qualityFilter/1.0.1` - Depends on very old Galaxy internals and
  has not worked for a long time.

Applied manual fixes:

- `toolshed.g2.bx.psu.edu/repos/boris/phylorelatives/phylorelatives/0.0.1` - set `$LD_LIBRARY_PATH` in
  `/cvmfs/main.galaxyproject.org/deps/R/2.15.0/boris/phylorelatives/06d6e56e8c2b/env.sh`
- `toolshed.g2.bx.psu.edu/repos/guru-ananda/heatmap/heatmap_1/1.0.0` - replaced `\$R_SCRIPT_PATH` in wrapper with
  `$__tool_directory__`
- `toolshed.g2.bx.psu.edu/repos/iuc/anndata_export/anndata_export` versions
  `0.6.22.post1+galaxy3` through `0.7.5+galaxy0` - backported https://github.com/galaxyproject/tools-iuc/pull/4602

### Sat Oct 28 23:04:16 CDT 2023

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/devteam/substitution_rates/subRate1/1.0.0` - This tool needs python2, a python2 galaxy
  lib, galaxy.eggs, so it would require a custom image and has likely been broken for a long time
- `toolshed.g2.bx.psu.edu/repos/devteam/substitutions/substitutions1/1.0.0` - Same as above, but this at least has a
  functional version 1.0.1.
- `toolshed.g2.bx.psu.edu/repos/peterjc/venn_list/venn_list/0.0.9` - Deps are not installed mulled properly and a newer
  working version is installed.

### Fri Oct 27 20:30:38 CDT 2023

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/lparsons/htseq_count/htseq_count/0.6.1galaxy1`: Broken, `0.6.1galaxy3` is installed and
  partially works, newer versins installed that fully work.
- `toolshed.g2.bx.psu.edu/repos/mbernt/maxbin2/maxbin2/2.2.7+galaxy2`: Mostly broken and `2.2.7+galaxy3` is installed
  and not broken.

### Mon May  9 14:07:45 CDT 2022

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/iuc/newick_utils/newick_display/1.6` - broken version, working version 1.6+galaxy1 is
  installed
- `toolshed.g2.bx.psu.edu/repos/iuc/scpipe/scpipe/1.0.0+galaxy1` - `galaxy2` is installed and contains all the fixes
  needed for this to run properly in a container and basically no other changes.
- `toolshed.g2.bx.psu.edu/repos/iuc/sarscov2formatter/sarscov2formatter/` - versions `0.1` and `0.5.3+galaxy1`. These
  run forever and never finish, the `1.0` version is installed and works properly.
- `toolshed.g2.bx.psu.edu/repos/iuc/star_fusion/star_fusion/0.5.4-3` - The `galaxy1` version is installed and fixes the
  dependency issues.
- `toolshed.g2.bx.psu.edu/repos/iuc/tag_pileup_frequency/tag_pileup_frequency/1.0.1` - writes to input, 1.0.2 is
  installed and fixed.
- `toolshed.g2.bx.psu.edu/repos/iuc/tetyper/tetyper/1.1+galaxy0` - working `galaxy1` version is installed
- `toolshed.g2.bx.psu.edu/repos/iuc/tbprofiler/tb_profiler_profile/2.6.1+galaxy0` - writes to dependency install dir,
  newer versions are installed and fixed.

### Wed May  4 12:15:13 CDT 2022

- Manually applied [tools-iuc#3980](https://github.com/galaxyproject/tools-iuc/pull/3980/) to `toolshed.g2.bx.psu.edu/repos/iuc/feelnc/feelnc/0.1.1.1`
- Updated and then hid `toolshed.g2.bx.psu.edu/repos/devteam/table_annovar/table_annovar/0.2`

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/iuc/gffcompare/gffcompare/0.9.8`
- `toolshed.g2.bx.psu.edu/repos/devteam/table_annovar/table_annovar/0.1`
- Pre-2016 `macs2_*`

### Tue May  3 15:45:37 CDT 2022

- Set `LD_LIBRARY_PATH="$RHOME/lib"` in the `rpy/1.0.3` tool_shed_package `env.sh` because _rpy2110.so has an RPATH that
  points to `/galaxy`, which has not existed since unmounting Corral 3 (and would not work on JS2 anyway).
- Restored a bunch of tools that I had tested in Singularity that didn't work to their pre-Singularity configs
- Manually applied [tools-iuc#3934](https://github.com/galaxyproject/tools-iuc/pull/3934) to 1.0.0 versions.

### Fri Apr 29 12:36:39 CDT 2022

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/guerler/charts/charts/1.0.0`

Fixed `anndata_import` old versions with fix from https://github.com/galaxyproject/tools-iuc/pull/3983

### Thu Apr 28 09:49:37 CDT 2022

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/devteam/lastz/lastz_wrapper_2/1.2.2`
- `toolshed.g2.bx.psu.edu/repos/devteam/scatterplot/scatterplot_rpy/1.0.0`
- `toolshed.g2.bx.psu.edu/repos/devteam/xy_plot/XY_Plot_1/1.0.1`

### Wed Apr 27 12:43:48 CDT 2022

Uninstalled:

- `toolshed.g2.bx.psu.edu/repos/devteam/freebayes/freebayes/0.0.2`
- `toolshed.g2.bx.psu.edu/repos/devteam/dna_filtering/histogram_rpy/1.0.3`
- `toolshed.g2.bx.psu.edu/repos/devteam/histogram/histogram_rpy/1.0.3`

### Thu Apr 21 14:02:39 CDT 2022

Uninstalled broken/unfixable:

- `toolshed.g2.bx.psu.edu/repos/crs4/taxonomy_krona_chart/taxonomy_krona_chart/2.0.0`
- `toolshed.g2.bx.psu.edu/repos/devteam/canonical_correlation_analysis/cca1/1.0.0`
- `toolshed.g2.bx.psu.edu/repos/devteam/correlation/cor2/1.0.0`
- `toolshed.g2.bx.psu.edu/repos/devteam/count_gff_features/count_gff_features/0.1`
- `toolshed.g2.bx.psu.edu/repos/devteam/cufflinks/cufflinks/0.0.6`
- `toolshed.g2.bx.psu.edu/repos/devteam/cufflinks/cufflinks/0.0.7`
- All `cuff*` tools version `2.2.1.0`

### Thu Apr 14 14:59:02 CDT 2022

- Uninstalled broken versions of deeptools: 2.2.2.0, 2.2.3.0, 2.3.6.0

### Wed Apr 13 13:22:33 CDT 2022

- `toolshed.g2.bx.psu.edu/repos/arkarachai-fungtammasan/str_fm/PEsortedSAM2readprofile` (all versions) - removed import
  of galaxy.eggs
- Uninstalled all old versions of ChemicalToolBox tools and reinstalled at their latest versions.

### Forgot to record the date

1. Uninstalled the following old tool versions because they did not work even before Singularity, and newer, working
versions exist:

- `toolshed.g2.bx.psu.edu/repos/iuc/gfa_to_fa/gfa_to_fa/0.1.0`
- `toolshed.g2.bx.psu.edu/repos/galaxyp/mz_to_sqlite/mz_to_sqlite/2.0.0`

### Fri Oct 29 09:42:39 CDT 2021

2. Applied manual fixes to the following tools:

- `toolshed.g2.bx.psu.edu/repos/iuc/crossmap_vcf/crossmap_vcf/0.5.2+galaxy0` -
  https://github.com/galaxyproject/tools-iuc/pull/4126
- `toolshed.g2.bx.psu.edu/repos/iuc/crossmap_vcf/crossmap_vcf/0.3.7` - same
- `toolshed.g2.bx.psu.edu/repos/iuc/crossmap_vcf/crossmap_vcf/0.3.7+galaxy1` - same
- `toolshed.g2.bx.psu.edu/repos/iuc/bioext_bam2msa/bioext_bam2msa/0.20.1+galaxy0` -
  https://github.com/galaxyproject/tools-iuc/pull/3986
- `toolshed.g2.bx.psu.edu/repos/iuc/bioext_bam2msa/bioext_bam2msa/0.19.7.0` - same

### Thu Oct 21 13:39:44 CDT 2021

2. Applied manual fixes to the following tools:

- `toolshed.g2.bx.psu.edu/repos/iuc/bedtools/bedtools_nucbed` (all versions) -
  https://github.com/galaxyproject/tools-iuc/pull/3930
- `toolshed.g2.bx.psu.edu/repos/iuc/bedtools/bedtools_getfastabed` (all versions) - same

### Mon Oct 18 11:20:37 CDT 2021

1. Uninstalled the following old tool versions because they did not work even before Singularity, and newer, working
versions exist:

- `toolshed.g2.bx.psu.edu/repos/devteam/sam_pileup/sam_pileup/1.1.2`
- `toolshed.g2.bx.psu.edu/repos/devteam/bam_to_sam/bam_to_sam/1.0.3`

2. Applied manual fixes to the following tools:

- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_mpileup/samtools_mpileup/2.0` -
  https://github.com/galaxyproject/tools-iuc/pull/3951/
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_mpileup/samtools_mpileup/2.1` - same
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_mpileup/samtools_mpileup/2.1.3` - same
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_mpileup/samtools_mpileup/2.1.4` - same
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_idxstats/samtools_idxstats/2.0.1` - Tool previously symlinked the bai
  next to the input dataset, changed to symlink both to the working dir.
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_stats/samtools_stats/2.0` - Same issue/fix as samtools_mpileup
- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_stats/samtools_stats/2.0.1` - same

3. Uninstalled for other reasons:

- `toolshed.g2.bx.psu.edu/repos/devteam/samtools_mpileup/samtools_mpileup/0.0.1` - Migrated version, has the same input
  writing problem as the newer versions above but also uses a python wrapper and it's just not worth the trouble to fix.

### Tue Oct 12 15:25:37 CDT 2021

1. Uninstalled the following old tool versions because they did not work even before Singularity, and newer, working
versions exist:

- `toolshed.g2.bx.psu.edu/repos/devteam/sam_merge/sam_merge2/1.2.0`: Broken picard version, not updated since 2015.


### Thu Oct  7 20:23:05 CDT 2021

Rolled back these uninstalls from the previous change (i.e. they are reinstalled) because I figured out how to make them
work:

1.

- `toolshed.g2.bx.psu.edu/repos/pjbriggs/trimmomatic/trimmomatic/0.32.3`: Dependency problems

2.

- `toolshed.g2.bx.psu.edu/repos/bgruening/text_processing/*/1.0.0`: No containers, requirements are a mess
  (`gnu_coreutils` instead of `coreutils`), many newer versions already installed
- `toolshed.g2.bx.psu.edu/repos/bgruening/trim_galore/trim_galore/0.4.0`: Only has requirement on cutadapt 1.8 but also
  needs perl, no container exists, would have to hack the `__cutadapt@1.8` conda env to include Perl, this only worked
  outside containers because `/usr/bin/perl`, newer working versions (including 0.4.3.1) already installed
- `toolshed.g2.bx.psu.edu/repos/bgruening/trim_galore/trim_galore/0.4.1`: Same as 0.4.0
- `toolshed.g2.bx.psu.edu/repos/bgruening/trim_galore/trim_galore/0.4.2`: Same as 0.4.0
- `toolshed.g2.bx.psu.edu/repos/devteam/fastx_barcode_splitter/cshl_fastx_barcode_splitter/1.0.0`: Seems to only work
  with a very old Perl version, has no dependency on Perl, deps are TS Packages
- `toolshed.g2.bx.psu.edu/repos/devteam/fastx_nucleotides_distribution/cshl_fastx_nucleotides_distribution/1.0.0`: Needs
  gnuplot which it probably previously got from `$PATH`
- `toolshed.g2.bx.psu.edu/repos/devteam/fastq_quality_boxplot/cshl_fastq_quality_boxplot/1.0.0`: Same as
  `cshl_fastx_nucleotides_distribution`

### Wed Oct  6 21:53:16 CDT 2021

- Changed Main's `tool_dependency_path` from `/galaxy/main/deps` to `/cvmfs/main.galaxyproject.org/deps`. The former is
  a symlink to the latter but does not exist inside Singularity containers
- Used `sed` to update all the Galaxy Package and Tool Shed Package dep `env.sh` files to use the `/cvmfs` path instead
  of `/galaxy`.

1. Uninstalled the following old tool versions because they did not work even before Singularity, and newer, working
versions exist:

- `toolshed.g2.bx.psu.edu/repos/devteam/column_maker/Add_a_column1/1.1.0`: Incompatible Python 2 syntax
- `toolshed.g2.bx.psu.edu/repos/galaxyp/regex_find_replace/regexColumn1/1.0.0`: Never worked, working version had been
  installed immediately after.
- `toolshed.g2.bx.psu.edu/repos/galaxyp/regex_find_replace/regex1/1.0.0`: Never worked, working version had been
  installed immediately after.
- `toolshed.g2.bx.psu.edu/repos/mvdbeek/add_input_name_as_column/addName/0.1.1`: Incompatible Python 2 syntax
- `toolshed.g2.bx.psu.edu/repos/mvdbeek/add_input_name_as_column/addName/0.1.1`: Incompatible Python 2 syntax
- `toolshed.g2.bx.psu.edu/repos/bgruening/uniprot_rest_interface/uniprot/0.1`: Incompatible Python 2 syntax
- `toolshed.g2.bx.psu.edu/repos/devteam/fastq_manipulation/fastq_manipulation/1.0.1`: Incompatible Python 2 syntax
- `toolshed.g2.bx.psu.edu/repos/devteam/fastq_manipulation/fastq_manipulation/1.1.1`: Incompatible Python 2 syntax

2. Uninstalled the following old tool versions because they could not made to run under Singularity with reasonable effort
and newer, working versions exist:

- `toolshed.g2.bx.psu.edu/repos/bgruening/text_processing/tp_awk_tool/1.1.1`: 1.1.2 (installed) was literally just a fix
  for container usage: https://github.com/bgruening/galaxytools/pull/1030

3. And uninstalled the following tools that don't fit into the above bins:

- `toolshed.g2.bx.psu.edu/repos/devteam/short_reads_figure_score/quality_score_distribution/1.0.2`: Only has TS deps and
  even running in a Python 2.7 container it doesn't work because rpy 1 can't find libR. But also hasn't run successfully
  on Main since August 2020.

### Tue Apr  7 18:12:05 EDT 2020

Upgraded Conda and recreated Galaxy venv as Conda Python 3.6 for Test on login2.stampede2.tacc.utexas.edu with:

```console
$ /work/galaxy/test/deps/_conda/bin/conda install 'conda<4.8'
$ /work/galaxy/test/deps/_conda/bin/conda create --override-channels --channel conda-forge --channel defaults --name _galaxy_ 'python=3.6' 'pip>=9' 'virtualenv>=16'
$ mv /work/galaxy/test/galaxy/venv /work/galaxy/test/galaxy/venv-2.7
$ /work/galaxy/test/deps/_conda/envs/_galaxy_/bin/virtualenv /work/galaxy/test/galaxy/venv
```

I also set $GALAXY_HOME in the (manually maintained) supervisor config for Pulsar on Stampede2 because the job_conf.xml
param doesn't seem to work anymore (but the Pulsar client still requires it to be set if the remote metadata option is
enabled).

The same process was repeated for Main

### Wed Apr  3 12:32:07 EDT 2019

Installed version 357 of various UCSC dependencies (mainly of converters and other built-in tools).

### Thu Sep 27 21:48:27 EDT 2018

#### Bridges

Ran out of quota in `/home` so I moved Galaxy and Conda back to `/pylon5` since the quotas there are now relaxed and the
automatic cleaner is disabled. This required doing the same `conda list --export | conda create --file /dev/stdin`
process as before. Java again had to be uninstalled from the `__unicycler@0.4.1` environment.

### Thu Sep 27 14:47:37 EDT 2018

#### DESeq2 dependencies

Because `--offline` support is broken in Conda 4.x (or was when we last upgraded, to 4.3.34) when running from a
read-only location, per-job conda envs have been broken since we upgraded Main from Conda 3 last year. In order to avoid
this, I tediously mulled all of the existing multi-dependency envs with the help of [some
scripts](https://github.com/natefoo/misc-scripts) I wrote in order to ensure the same versions of *all* packages in the
environments would be the same in the mulled env as they were in the per-job envs.

This was done last year at the time of upgrading to Conda 4, for all but two tools, two different versions of DESeq2,
which failed to mull:

- Tool version 2.11.39, DESeq2 version 1.14.1
- Tool version 2.1.8.4, DESeq2 version 1.10.1

I don't recall why the first one failed - I was able to mull it today using the "Manage dependencies" interface in
Galaxy. The second, however, was more broken, because the version of DESeq2 was dependent on an older version of R
(3.2.2) and one of the tool's other dependencies (r-getopt 1.20.0) was no longer available from Conda for that version
of R. However, [there is one copy from a community member](https://anaconda.org/fongchun/r-getopt). Using that version
allowed the mulled env to install, although I was not able to use the mulled env name because the packages were old
enough that they ran in to the conda-build < 3.0 path element length limits... To get around that, I named the env
`deseq2-1.10.1-mulled` and then symlinked `mulled-v1-eac05d01b4e8eb7f41627035822f7eda0dd5a91adc5442bcbf1e12a95a80ee9f`
to it.

I can't guarantee that these two versions of DESeq2 will produce the same results as they did before the Conda
upgrade-and-mull last year, but at least they work now.

### Thu Mar  1 11:11:05 EST 2018

**Bridges**

Due to ongoing problems with `/pylon2`, and with a quota increase on `/home` from PSC, I've moved everything to either
`/home` or `/pylon5` on Bridges. As of now, `/pylon5` contains staging/job runtime data, as well as Pulsar's AMQP
retry/state and job state files. Everything else is in `/home`. A few things that occurred as a result:

- Reinstalled Conda and rebuilt Conda envs with `conda list --export` and `conda create --file`.
- Uninstalled OpenJDK from Unicycler envs (but allowed it to install in `__trinity@2.4.0`. Because we no longer use
  Conda in `/pylon2` we can now run OpenJDK from Conda, but due to rrwick/Unicycler#60, we'll need to keep the `java
  -version` wrapper around permanently for older versions.
- `galaxy.ini` has to be installed by hand for the conditional wheel installation to succeed, this is a bug.

### February 7-14, 2018

Too much to list here, and unfortunately I didn't capture it all, but the summary is that Main was running Conda 3.19,
and when we upgraded to Galaxy 18.01, it was no longer compatible. Unfortunately, due to the `conda install --offline`
bugs that were present in Conda >= 4.0 < 4.4, we could not upgrade to 4.x. However, 18.01 forced the upgrade, but 4.4
had not been released yet. As a result, I installed 4.3 and had to do the following things to fix our dependencies:

- Reordered our dependency resolution to put Conda before Galaxy Packages
- Temporarily disabled certain Galaxy packages while installing from Conda
- Found any tool with a mixture of Conda and non-Conda dependencies and mulled them (mainly using a set of scripts I
  have over in [natefoo/misc-scripts](https://github.com/natefoo/misc-scripts/)) to ensure that no per-job Conda envs
  will ever be created (this is where the `--offline` bugs cause failures)

### Wed Jan 31 12:18:22 EST 2018

Installed Trinity 2.4.0 on Bridges via Conda. As with Unicycler, the Conda version of Java must be removed. Also
apparently `--override-channels` did not work as expected because I had to reinstall bzip2:

```console
[xcgalaxy@br005 ~]$ conda create -n __trinity@2.4.0 --override-channels -c bioconda -c conda-forge -c defaults trinity=2.4.0
[xcgalaxy@br005 ~]$ conda remove -n __trinity@2.4.0 openjdk
[xcgalaxy@br005 ~]$ conda install -n __trinity@2.4.0 -c conda-forge bzip2=1.0.6=1
```

### Wed Nov 15 15:11:55 EST 2017

#### Jetstream

The set_metadata conda environments for Main were not working because they had installed bzip2 from defaults, which does
not provide libbzip2.so. I fixed this by explicitly installing the conda-forge version:

```sh-session
g2main@jetstream-iu0$ conda install -n set_metadata@20171114 --override-channels -c conda-forge bzip2=1.0.6=1
```

In the future, when creating/installing environments, `--override-channels` should prevent this.

#### Bridges

Somehow, conda's `stat.pyc` had been corrupted. I removed it and ran `conda` to recreate it, and conda is functional
again.

### Wed Nov 15 12:12:00 EST 2017

Because the Pulsar command line, including metadata, is generated on the Galaxy side, it's not possible to resolve the
metadata tool's dependencies for Pulsar. Because of this, Jetstream jobs were failing to set metadata on BAM outputs on
*certain* jobs where samtools did not remain on `$PATH` after running the tool and setting up the environment for
`set_metadata.py`. As a result, it's necessary to set up `$PATH` manually to contain the dependencies. I installed them
with conda as both Test/Main on both TACC/IU Jetstreams:

```sh-session
g2test@jetstream-iu0$ /jetstream/scratch0/test/conda/bin/conda create -n set_metadata@20171114 -c bioconda -c conda-forge -c defaults samtools bcftools=1.5
g2main@jetstream-iu0$ /jetstream/scratch0/main/conda/bin/conda create -n set_metadata@20171114 -c bioconda -c conda-forge -c defaults samtools bcftools=1.5
g2test@jetstream-tacc0$ /jetstream/scratch0/test/conda/bin/conda create -n set_metadata@20171114 -c bioconda -c conda-forge -c defaults samtools bcftools=1.5
g2main@jetstream-tacc0$ /jetstream/scratch0/main/conda/bin/conda create -n set_metadata@20171114 -c bioconda -c conda-forge -c defaults samtools bcftools=1.5
```

And changed `job_conf.xml` accordingly, committed with this change log message.


### Wed Oct  4 12:59:53 EDT 2017

Unicycler 0.4.1 has been installed on Bridges for Main using the process below (OpenJDK is shared between Test and Main).

### Tue Oct  3 14:20:57 EDT 2017

Unicycler on Test was upgraded to 0.4.1 requiring roughly the same process as before, but the new version also checks
its dependency versions, which led to [Unicycler#60](https://github.com/rrwick/Unicycler/pull/60) due to our use of
`$_JAVA_OPTIONS`. In the process, I created a copy of OpenJDK expressly for use on Bridges rather than relying on the
system default in `/usr/bin/java`:

```console
[xcgalaxy@br005 ~]$ /pylon2/mc48nsp/xcgalaxy/test/deps/_conda/bin/conda create -c conda-forge -p /pylon5/mc48nsp/xcgalaxy/openjdk8 --copy openjdk=8.0.144
```

It was then necessary to manually install and fix Unicycler:

```console
[xcgalaxy@br005 ~]$ conda create -n __unicycler@0.4.1 -c iuc -c bioconda -c conda-forge -c defaults -c r unicycler=0.4.1 python=3.5
(__unicycler@0.4.1)[xcgalaxy@br005 ~]$ conda remove -n __unicycler@0.4.1 openjdk bzip2
(__unicycler@0.4.1)[xcgalaxy@br005 ~]$ conda install -n __unicycler@0.4.1 -c conda-forge bzip2=1.0.6=1
```

In order to work around [Unicycler#60](https://github.com/rrwick/Unicycler/pull/60), I've renamed
`/pylon5/mc48nsp/xcgalaxy/openjdk8/bin/java` to `java.real` and replaced `java` with:

```bash
#!/bin/sh

case "$@" in
    *-version*)
        /pylon5/mc48nsp/xcgalaxy/openjdk8/bin/java.real "$@" java.real -version 2>&1 | grep -v _JAVA_OPTIONS >&2
        ;;
    *)
        exec /pylon5/mc48nsp/xcgalaxy/openjdk8/bin/java.real "$@"
        ;;
esac
```

We'll need to do the same when upgrading Main to 0.4.1.

### Tue Sep 12 13:06:55 EDT 2017

With Bridges access restored, I've finished up work on Unicycler. Jobs were still failing due to a failure to run
SPAdes, although Unicycler was not logging this, even with `--verbosity 3` and the SPAdes output handling in
`unicycler.spades_func`. I ran SPAdes by hand to get the error message:

```
== Error ==  python version 3.6 is not supported!
Supported versions are 2.4, 2.5, 2.6, 2.7, 3.2, 3.3, 3.4, 3.5
```

As of the time of writing it does not appear that SPAdes works with 3.6, so I am not sure if the bioconda Unicycler
Python 3.6 packages are just not tested/used? Regardless, I fixed this by downgrading Unicycler's Python to 3.5 and
reinstalling:

```console
(__unicycler@0.3.0b)[xcgalaxy@br005 ~]$ CONDARC=/pylon2/mc48nsp/xcgalaxy/test/deps/_condarc conda install 'python<3.6'
(__unicycler@0.3.0b)[xcgalaxy@br005 ~]$ CONDARC=/pylon2/mc48nsp/xcgalaxy/test/deps/_condarc conda uninstall 'unicycler'
(__unicycler@0.3.0b)[xcgalaxy@br005 ~]$ CONDARC=/pylon2/mc48nsp/xcgalaxy/test/deps/_condarc conda install 'unicycler'
(__unicycler@0.3.0b)[xcgalaxy@br005 ~]$ CONDARC=/pylon2/mc48nsp/xcgalaxy/test/deps/_condarc conda uninstall 'openjdk'
```

The same process has been performed for Main's Unicycler conda environment on Bridges.

### Wed Sep  6 20:51:50 EDT 2017

I've placed a modified version of cron/updateucsc.sh.sample and its scripst into CVMFS at
/cvmfs/data.galaxyproject.org/managed/bin/ucsc_update.sh, and scheduled it to run on the first Wednesday of every
month. THis will publish changes to:

- /cvmfs/data.galaxyproject.org/managed/location/builds.txt
- /cvmfs/data.galaxyproject.org/managed/location/ucsc_build_sites.txt
- /cvmfs/data.galaxyproject.org/managed/len/ucsc/*.len

Corresponding config changes are in this commit.

### Thu Aug 31 10:44:05 EDT 2017

On Bridges, OpenJDK < 9 cannot open JAR files stored in SLASH2 without the `sun.zip.disableMemoryMapping=true` option
set ([related issue][jar-mmap-map-shared]). Unfortunately, this workaround does not apply to the JVM being able to open
the runtime jar (e.g. /pylon2/mc48nsp/xcgalaxy/test/deps/_conda/envs/__unicycler@0.3.0b/jre/lib/rt.jar). I could find
no solution to this problem, so I worked around it by uninstalling the `openjdk` package from the `__unicycler@0.3.0b`
conda environment, which will allow the tool to pick up java from the system.

I've also set `$_JAVA_OPTIONS` to `-Dsun.zip.disableMemoryMapping=true` so that java can open the pilon jar.

[jar-mmap-map-shared]: https://bugs.openjdk.java.net/browse/JDK-7085890
