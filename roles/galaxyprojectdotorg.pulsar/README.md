Pulsar
======

An [Ansible][ansible] role for installing and managing [Pulsar][pulsar]
servers.

[ansible]: http://www.ansible.com/
[pulsar]: https://github.com/galaxyproject/pulsar/

Requirements
------------

This role has the same dependencies as the `git` module, namely,
[git][git]. In addition, [Python virtualenv][venv] is required (as is
[pip][pip], but pip will automatically installed with virtualenv). These can
easily be installed via a pre-task in the same play as this role:

    - hosts: pulsarservers
        pre_tasks:
          - name: Install Mercurial
            apt: pkg={{ item }} state=installed
            sudo: yes
            when: ansible_os_family = 'Debian'
            with_items:
              - git
              - python-virtualenv
          - name: Install Mercurial
            yum: pkg={{ item }} state=installed
            sudo: yes
            when: ansible_os_family = 'RedHat'
            with_items:
              - git
              - python-virtualenv
        roles:
          - galaxyprojectdotorg.pulsar

If your `virtualenv` executable is not on `$PATH`, you can specify its location with
the `pip_virtualenv_command` variable.

[git]: http://git-scm.com/
[venv]: http://virtualenv.readthedocs.org/
[pip]: http://pip.readthedocs.org/

Role Variables
--------------

### Required variables ###

- `pulsar_server_dir`: Filesystem path where the Pulsar server code will be
  installed (cloned).

### Optional variables ###

You can control various things about where you get Pulsar from, what version
you use, and where its configuration files will be placed:

- `pulsar_git_repo` (default: `https://github.com/galaxyproject/pulsar`):
  Upstream git repository from which Pulsar should be cloned.
- `pulsar_changeset_id` (default: `master`): A changeset id, tag, branch, or
  other valid git identifier for which changeset Pulsar should be updated to.
- `pulsar_venv_dir` (default: `<pulsar_server_dir>/.venv`): The role will
  create a [virtualenv][virtualenv] from which Pulsar will run, this controls
  where the virtualenv will be placed.
- `pulsar_config_dir` (default: `<pulsar_server_dir>`): Directory that will be
  used for Pulsar configuration files.
- `pulsar_optional_dependencies` (default: None): List of optional dependency
  modules to install. Whether or not you need these depends on what features
  you are enabling.
- `pulsar_install_environments` (default: None): Installing dependencies may
  require setting certain environment variables to compile successfully.


Additional options from Pulsar's `server.ini` are configurable via the
following variables (these options are explained in the [Pulsar
documentation][pulsardocs] and `server.ini.sample`):

- `pulsar_host` (default: `localhost`)
- `pulsar_port` (default: `8913`)
- `pulsar_dependencies_dir` (default: `<pulsar_server_dir>/deps`)
- `pulsar_persistence_dir` (default:
  `<pulsar_server_dir>/files/persisted_data`)
- `pulsar_staging_dir` (default: `<pulsar_server_dir>/files/staging`)
- `pulsar_drmaa_library_path`
- `pulsar_job_managers` (default: `_default_`, type `queued_python`): The
  contents of the job managers configuration file (job_managers.ini by default)
  are controlled by this variable. It is a hash of hashes (or dictionaries)
  that will be translated in to the configuration file. See the definition in
  the defaults for syntax hints.

### pulsar_optional_dependencies ###

Currently, the list of optional dependencies is:

    pulsar_optional_dependencies:
      - pyOpenSSL
      # For remote transfers initiated on the Pulsar end rather than the Galaxy end
      - pycurl
      # uwsgi used for more robust deployment than paste
      - uwsgi
      # drmaa required if connecting to an external DRM using it.
      - drmaa
      # kombu needed if using a message queue
      - kombu
      # requests and poster using Pulsar remote staging and pycurl is unavailable
      - requests
      - poster
      # psutil and pylockfile are optional dependencies but can make Pulsar
      # more robust in small ways.
      - psutil

Many of these dependencies have their own dependencies. A nice future
enhancement to this role would be to install the dependencies' dependencies via
the system package manager if desired.

### pulsar_install_environments ###

Some sites may need to set environment variables when installing certain
modules, e.g. to point pyOpenSSL at a non-standard OpenSSL or libffi locations,
or to instruct pycurl to use the NSS library:

    pulsar_install_environments:
      pyOpenSSL:
        PKG_CONFIG_PATH: "/opt/site/libffi/lib64/pkgconfig"
        CFLAGS: "-I/opt/site/openssl/include"
        LDFLAGS: "-L/opt/site/openssl/lib"
      pycurl:
        PYCURL_SSL_LIBRARY: "nss"

[pulsardocs]: http://pulsar.readthedocs.org/

Dependencies
------------

None

Example Playbook
----------------

Install Pulsar on your local system with all the default options:

    - hosts: localhost
      connection: local
      vars:
        pulsar_server_dir: /home/nate/pulsar
      roles:
        - role: galaxyprojectdotorg.pulsar

Install Pulsar with directory separation and also install Galaxy:


    - hosts: pulsarservers
      vars:
        pulsar_venv_dir: /opt/pulsar/venv
        pulsar_server_dir: /opt/pulsar/server
        pulsar_config_dir: /opt/pulsar/config
        pulsar_persistence_dir: /var/opt/pulsar/persisted_data
        pulsar_staging_dir: /var/opt/pulsar/staging"
        pulsar_optional_dependencies:
          - pyOpenSSL
          - pycurl
          - uwsgi
          - drmaa
          - kombu
          - requests
          - poster
          - psutil
        galaxy_server_dir: /opt/galaxy/server
        galaxy_config_dir: /opt/galaxy/config
        galaxy_config_files:
          - name: files/galaxy/config/datatypes_conf.xml
            dest: "{{ galaxy_config_dir }}/datatypes_conf.xml"
      pre_tasks:
        - name: Install Mercurial
          pip: name=mercurial virtualenv={{ hg_virtualenv }} virtualenv_command={{ pip_virtualenv_command | default( 'virtualenv' ) }}
      roles:
        - role: galaxyprojectdotorg.pulsar
        # Install with:
        #   % ansible-galaxy install natefoo.postgresql_objects
        - role: galaxyprojectdotorg.galaxy
          galaxy_manage_mutable_setup: no
          galaxy_manage_database: no

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

[John Chilton](https://github.com/jmchilton)  
[Nate Coraor](https://github.com/natefoo)
