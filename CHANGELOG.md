# usegalaxy-playbook change log

This is a log of any changes that were made manually that could not easily be codified in to Ansible. Changes made
prior to the first entry have not been logged.

### Wed Oct  6 21:53:16 CDT 2021

- Changed Main's `tool_dependency_path` from `/galaxy/main/deps` to `/cvmfs/main.galaxyproject.org/deps`. The former is
  a symlink to the latter but does not exist inside Singularity containers
- Used `sed` to update all the Galaxy Package and Tool Shed Package dep `env.sh` files to use the `/cvmfs` path instead
  of `/galaxy`.

Uninstalled the following old tool versions because they did not work even before Singularity, and newer, working
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
- `toolshed.g2.bx.psu.edu/repos/pjbriggs/trimmomatic/trimmomatic/0.32.3`: Dependency problems

Uninstalled the following old tool versions because they could not made to run under Singularity with reasonable effort
and newer, working versions exist:

- `toolshed.g2.bx.psu.edu/repos/bgruening/text_processing/tp_awk_tool/1.1.1`: 1.1.2 (installed) was literally just a fix
  for container usage: https://github.com/bgruening/galaxytools/pull/1030
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

And uninstalled the following tools that don't fit into the above bins:

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
