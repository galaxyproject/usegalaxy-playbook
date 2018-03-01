# usegalaxy-playbook change log

This is a log of any changes that were made manually that could not easily be codified in to Ansible. Changes made
prior to the first entry have not been logged.

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
