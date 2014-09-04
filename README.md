usegalaxy.org Playbook
======================

This [Ansible][ansible] playbook is used to deploy and maintain the public
Galaxy servers, namely [Galaxy Main (usegalaxy.org)][main] and [Galaxy Test
(test.galaxyproject.org)][test]. The generalized roles herein have been
published to [Ansible Galaxy][ansiblegalaxy] and can be installed for your own
use via the `ansible-galaxy` command, but a few site-specific roles are
contained here as well.

This playbook is not designed to be used by Galaxy deployers/admins at other
sites, but should be useful as a reference for anyone wishing to emulate a
setup like usegalaxy.org.

### Best Practices ###

We differ slightly from [Ansible best practices][ansiblebestpractices]:

- Because we're trying to ensure that roles are generally consumable and can
  easily be updated from [Ansible Galaxy][ansiblegalaxy] whenever new versions
  are published, our files and templates do not live inside the roles.

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/
[main]: https://usegalaxy.org/
[test]: https://test.galaxyproject.org/
[ansiblebestpractices]: http://docs.ansible.com/playbooks_best_practices.html

Usage
-----

Galaxy Test is updated with:

    % ansible-playbook -i development/inventory galaxy.yml --ask-vault-pass

The static content alone (e.g. welcome.html and its dependencies) can be
updated without requiring a vault pass:

    % ansible-playbook -i development/inventory galaxy_static.yml

It's advisable to use a password manager for the vault password. Anything
secure will do, although I find [`pass(1)`][pass] to be incredibly useful in
combination with Ansible Vaults.

If you need to install Ansible and don't want to use the system packages for
your OS (or want the latest version), see `bootstrap-ansible.bash` in the root
directory.

[pass]: http://www.passwordstore.org/

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Credits
-------

[Nate Coraor](https://github.com/natefoo)  
[John Chilton](https://github.com/jmchilton)

### Inspiration/Thanks ###

[Peter van Heusden](https://github.com/pvanheus/)  
[Lance Parsons](https://github.com/lparsons/)
