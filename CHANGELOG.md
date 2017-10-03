# usegalaxy-playbook change log

This is a log of any changes that were made manually that could not easily be codified in to Ansible. Changes made
prior to the first entry have not been logged.

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
