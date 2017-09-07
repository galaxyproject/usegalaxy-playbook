# usegalaxy-playbook change log

This is a log of any changes that were made manually that could not easily be codified in to Ansible. Changes made
prior to the first entry have not been logged.

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
