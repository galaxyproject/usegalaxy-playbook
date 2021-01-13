usegalaxy.org Playbook
======================

This [Ansible][ansible] playbook is used to deploy and maintain the public Galaxy servers, namely [Galaxy Main
(usegalaxy.org)][main] and [Galaxy Test (test.galaxyproject.org)][test]. The generalized roles herein have been
published to [Ansible Galaxy][ansiblegalaxy] and can be installed for your own use via the `ansible-galaxy` command, but
a few site-specific roles are contained here as well.

This playbook is not designed to be used by Galaxy deployers/admins at other sites, but should be useful as a reference
for anyone wishing to emulate a setup like usegalaxy.org.

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/
[main]: https://usegalaxy.org/
[test]: https://test.galaxyproject.org/
[ansiblebestpractices]: http://docs.ansible.com/playbooks_best_practices.html

Usage
-----

Usage documentation can be found in the [usegalaxy-playbook wiki][wiki]. All standard playbook operations can be done
using the targets in the [Makefile](Makefile).

You will need the vault password to run most plays. These can be found in the galaxyproject [`pass(1)` password
store][pass]. If you have configured a `gpg-agent(1)`, you can avoid being prompted for your passphrase on every
execution.

[wiki]: https://github.com/galaxyproject/usegalaxy-playbook/wiki
[pass]: http://www.passwordstore.org/

Build Notes
-----------

NOTE: out of date now, need to update

Building Pulsar's dependencies' dependencies as an unprivileged user on some
HPC systems was a difficult manual process, so I made some notes, which may be
helpful:

slurm-drmaa compiled and installed by hand on Stampede (slurm-devel is not installed (or worse, some login nodes have
mismatched versions), so I had to work around this):

    cd slurm
    mkdir -p include/slurm
    cd src/slurm-2.6.3
    ./configure --prefix=/usr
    cp slurm/*.h ../../include/slurm
    cd slurm-drmaa-1.0.7
    ./configure --prefix=/work/galaxy/test/slurm-drmaa --with-slurm-inc=/work/galaxy/test/slurm/include && make && make install

Python + virtualenv compiled and installed by hand on Stampede:

    cd /work/galaxy/test/python/src/Python-2.7.6
    ./configure --prefix=/work/galaxy/test/python --enable-unicode=ucs4 && make && make install
    cd ../virtualenv-1.11.5
    /work/galaxy/test/python/bin/python setup.py install

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Credits
-------

[Contributors](https://github.com/galaxyproject/usegalaxy-playbook/graphs/contributors)

### Inspiration/Thanks ###

[Lance Parsons](https://github.com/lparsons/)  
[Peter van Heusden](https://github.com/pvanheus/)
