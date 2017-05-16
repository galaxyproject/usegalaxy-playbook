Galaxy Tool Shed
================

An [Ansible][ansible] role for installing and managing [Galaxy][galaxyproject]
Tool Shed servers.  Despite the name confusion, [Galaxy][galaxyproject] bears no relation
to [Ansible Galaxy][ansiblegalaxy].

This role is not for installing Galaxy servers. [A separate role][galaxyrole]
exists for that purpose.

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/
[galaxyrole]: https://github.com/galaxyproject/ansible-galaxy/

Requirements
------------

None

Role Variables
--------------

### Required variables ###

- `galaxy_toolshed_server_dir`: Filesystem path where the Tool Shed (Galaxy)
  server code is installed.

### Optional variables ###

Two variables control which functions this role will perform (both default to
`yes`):

- `galaxy_toolshed_manage_static_setup`: Manage "static" Tool Shed
  configuration files - ones which are not modifiable by the Galaxy server
  itself. At a minimum, this is the primary Tool Shed configuration file,
  `tool_shed.ini`.
- `galaxy_toolshed_manage_database`: Upgrade the database schema as necessary,
  when new schema versions become available.

You can control various things about where you get Galaxy from, what version
you use, and where its configuration files will be placed:

- `galaxy_toolshed_venv_dir` (default: `<galaxy_toolshed_server_dir>/.venv`):
  The role will use a python interpreter in this [virtualenv][virtualenv] to
  manage the database. [galaxyproject.galaxy][galaxyrole] will create it
  for you and so setting this to the same as `galaxy_venv_dir` is a good idea.
- `galaxy_toolshed_config_dir` (default:
  `<galaxy_toolshed_server_dir>/config`): Directory that will be used for
  "static" configuration files.
- `galaxy_toolshed_mutable_config_dir` (default:
  `<galaxy_toolshed_server_dir>/config`): Directory that will be used for
  "mutable" configuration files, must be writable by the user running the Tool
  Shed.
- `galaxy_toolshed_mutable_data_dir` (default:
  `<galaxy_toolshed_server_dir>/database`): Directory that will be used for
  "mutable" data and caches, must be writable by the user running Galaxy.
- `galaxy_toolshed_config_file` (default:
  `<galaxy_toolshed_config_dir>/tool_shed.ini`): The Tool Shed's primary
  configuration file.
- `galaxy_toolshed_config`: The contents of the Tool Shed configuration file
  (`tool_shed.ini` by default) are controlled by this variable. It is a hash of
  hashes (or dictionaries) that will be translated in to the configuration
  file. See the Example Playbooks below for usage.
- `galaxy_toolshed_config_files`: List of hashes (with `src` and `dest` keys)
  of files to copy from the control machine.
- `galaxy_toolshed_config_templates`: List of hashes (with `src` and `dest`
  keys) of templates to fill from the control machine.

Dependencies
------------

This module does not directly depend on any others, but most likely you will
want to use [galaxyproject.galaxy][galaxyrole] to install the Galaxy
(Tool Shed) code. It requires the variable:

- `galaxy_server_dir`: Filesystem path where the Galaxy server code will be
  installed (cloned). Set this to `galaxy_toolshed_server_dir`.

For additional optional variables, see the [galaxyproject.galaxy
documentation][galaxyrole]. Most notably, you probably want to set
`galaxy_config_file` to the path to `tool_shed.ini` to cause the galaxy role to
fetch the correct eggs.

Example Playbook
----------------

Install the Tool Shed with code owned by a different user

```
- name: Tool Shed code and eggs, manage static configs
  hosts: toolshedservers
  remote_user: shedcode
  vars:
    galaxy_toolshed_server_dir: "/srv/toolshed/server"
    galaxy_toolshed_venv_dir: "/srv/toolshed/venv"
    galaxy_toolshed_config_dir: "/srv/toolshed/config"
    galaxy_toolshed_config_file: "{{ galaxy_toolshed_config_dir }}/tool_shed.ini"
    galaxy_toolshed_mutable_config_dir: "/srv/toolshed/var/config"
    galaxy_toolshed_mutable_data_dir: "/srv/toolshed/var/data"
    galaxy_server_dir: "{{ galaxy_toolshed_server_dir }}"
    galaxy_venv_dir: "{{ galaxy_toolshed_venv_dir }}"
    galaxy_config_file: "{{ galaxy_toolshed_config_file }}"
  roles:
    - role: galaxyproject.galaxy
      galaxy_manage_clone: yes
      galaxy_manage_static_setup: no
      galaxy_manage_mutable_setup: no
      galaxy_manage_database: no
      galaxy_fetch_eggs: no
    - role: galaxyproject.galaxy_toolshed
      galaxy_toolshed_manage_static_setup: yes
      galaxy_toolshed_manage_database: no
    - role: galaxyproject.galaxy
      galaxy_manage_clone: no
      galaxy_manage_static_setup: no
      galaxy_manage_mutable_setup: no
      galaxy_manage_database: no
      galaxy_fetch_eggs: yes

- name: Tool Shed database
  hosts: toolshedservers
  remote_user: shed
  vars:
    galaxy_toolshed_server_dir: "/srv/toolshed/server"
    galaxy_toolshed_venv_dir: "/srv/toolshed/venv"
    galaxy_toolshed_config_dir: "/srv/toolshed/config"
    galaxy_toolshed_config_file: "{{ galaxy_toolshed_config_dir }}/tool_shed.ini"
  roles:
    - role: galaxyproject.galaxy_toolshed
      galaxy_toolshed_manage_static_setup: no
      galaxy_toolshed_manage_database: yes
```

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

[Nate Coraor](https://github.com/natefoo)  
