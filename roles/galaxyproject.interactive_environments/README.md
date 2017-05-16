Interactive Environments
========================

Install [Galaxy](http://galaxyproject.org) [Interactive Environments](http://galaxy.readthedocs.org/en/master/admin/interactive_environments.html) in a production environment.

Requirements
------------

The minimum supported version of Ansible is 1.9, due to the use of the `clone=no` option with the synchronize module.

A supported version of Node (see the [IE proxy documentation](http://galaxy.readthedocs.org/en/master/admin/interactive_environments.html#deploying-gies) for details) and NPM should be installed. This can be done using `tasks/install_dependencies.yml`, which can be added to a play like so:

```yaml
- hosts: galaxyservers
  remote_user: root
  tasks:
    - include: roles/galaxyproject.interactive_environments/tasks/install_dependencies.yml
```

This is not included in the role's default tasks since the proper method for gaining root access for the package manager will vary by site.

Role Variables
--------------

### Required Variables

The role has two modes of operation, controlled by the `interactive_environments_install_method` variable. Possible values are `inplace` (default) and `copy`.

#### In-place installation method

The in-place method simply points the role at a Galaxy installation and uses the [IE plugins](https://github.com/galaxyproject/galaxy/tree/dev/config/plugins/interactive_environments) and [proxy](https://github.com/galaxyproject/galaxy/tree/dev/lib/galaxy/web/proxy/js) in place. To use the in-place method, ensure the following variables (as used by the Galaxy role) are set:

- `interactive_environments_install_method` to `inplace`
- `galaxy_server_dir`: the root of your Galaxy installation
- `galaxy_mutable_data_dir`: a persistent, writable directory where the IE proxy's session cache can be stored

This method requires less setup and does not maintain a separate copy of the IE components, but has some limitations:

1. It is not possible to control which IE plugins will attempt to be loaded
2. Modifications to the Galaxy clone must be made, namely, the IE config file(s) and the proxy's node dependencies will be written.

In order to avoid these limitations, it's necessary to make a separate copy of the IE components. To do so, use the copy method

#### Copy installation method

For the copy method, set the following variables:

- `interactive_environments_install_method` to `copy`
- `interactive_environments_plugins_path`: path on Galaxy server where the IE plugins should be installed
- `interactive_environments_proxy_path`: path on Galaxy server where the Node-based IE proxy should be installed
- `interactive_environments_enabled`: a list of names of IEs that will be installed
- `interactive_environments_config_files`: a list of config files that will be installed (the format is explained in greater detail below)

#### Additional required variables

Each plugin's config file(s) are created from the values in the `interactive_environments_config_files` list. An example of that list for the Jupyter plugin can be found below:

```yaml
interactive_environments_config_files:
  - ie_name: jupyter
    file: jupyter.ini
    contents:
      docker:
        command: "docker -H tcp://docker.example.org:2376 --tlsverify {docker_args}"
        galaxy_url: "https://example.galaxyproject.org"
        docker_hostname: "docker.example.org"
  - ie_name: jupyter
    file: allowed_images.yml
    contents:
      - image: "bgruening/docker-jupyter-notebook:16.01.1"
        description: >
          The Jupyter notebook is the next iteration of IPython, allowing
          analysis in many different languages. This image features the Python,
          R, Julia, Haskell, Bash kernels and many scientific analysis stacks for
          each.
```

This will create `<interactive_environments_plugins_path>/jupyter/config/jupyter.ini` with the following contents:

```ini
[docker]
command = docker -H tcp://docker.example.org:2376 --tlsverify {docker_args}
galaxy_url = https://galaxy.example.org
docker_hostname = docker.example.org
```

And `<interactive_environments_plugins_path>/jupyter/config/allowed_images.yml`:

```yaml
-   description: 'The Jupyter notebook is the next iteration of IPython, allowing
        analysis in many different languages. This image features the Python, R, Julia,
        Haskell, Bash kernels and many scientific analysis stacks for each.

        '
    image: quay.io/bgruening/docker-jupyter-notebook:16.01.1
```

## Optional Variables

### Supervisor config handling

- `interactive_environments_supervisor_conf_dir`: If set, write a supervisor config to this directory
- `interactive_environments_supervisor_program_name`: The proxy's `program` name in supervisor
- `interactive_environments_supervisorctl_path`: If set, write a supervisor config to this directory

### Nginx config handling

- `interactive_environments_nginx_config_dir`: If set, write an nginx config to this directory for each IE in `interactive_environments_config_files`

### Apache config handling

- `interactive_environments_apache_config_dir`: If set, write an Apache config to this directory for each IE in `interactive_environments_config_files`

### Additional optional variables

TODO: document these:

- `interactive_environments_node_executable` (default: `node`):
- `interactive_environments_proxy_ip` (default: `galaxy_config['app:main']['dynamic_proxy_bind_ip']` if set, otherwise `0.0.0.0`):
- `interactive_environments_proxy_port` (default: `galaxy_config['app:main']['dynamic_proxy_bind_port']` if set, otherwise `8800`):
- `interactive_environments_proxy_prefix` (default: `galaxy_config['app:main']['dynamic_proxy_prefix']` if set, otherwise `gie_proxy`):
- `interactive_environments_session_map` (default: `<interactive_environments_proxy_path>/session_map.sqlite`):
- `interactive_environments_proxy_user` (default: `remote_user`):
- `interactive_environments_access_log_path` (default: `<interactive_environments_proxy_path>/access.log`):
- `interactive_environments_error_log_path` (default: `<interactive_environments_proxy_path>/error.log`):
- `interactive_environments_ssl`: A hash with keys `ca_cert`, `cert`, and `key`, and corresponding values, which populate the Docker SSL client in `~/.docker`

The following variables only apply to the copy installation method:

- `interactive_environments_plugins_version` (default: the value of `galaxy_changeset_id` if set, otherwise `master`): commit id of Galaxy from which the plugins should be extracted
- `interactive_environments_proxy_version` (default: the value of `galaxy_changeset_id` if set, otherwise `master`): commit id of Galaxy from which the proxy should be extracted
- `interactive_environments_plugins_local_path`: path in local playbook where the plugins should be maintained (plugins are synchronized from here to the Galaxy server)
- `interactive_environments_proxy_local_path`: path in local playbook where the proxy should be maintained (the proxy is synchronized from here to the Galaxy server)

In addition, be sure to configure in Galaxy:

- `dynamic_proxy_manage` to `False`
- `dynamic_proxy_external_proxy` to `True`
- `dynamic_proxy_prefix`
- `galaxy_infrastructure_url`

If using the copy installation method, also set:

- `interactive_environment_plugins_directory`

Dependencies
------------

None, but you can save a bit of setup time by having this role run in a play where the variables from the [Galaxy role](https://github.com/galaxyproject/ansible-galaxy) are available. This will set `galaxy_server_dir` and `galaxy_config` (from which the proxy config is pulled)

Example Playbook
----------------

```yaml
- hosts: galaxyservers
  vars:
    interactive_environments_install_method: copy
    interactive_environments_plugins_path: "/srv/galaxy/interactive_environments/plugins"
    interactive_environments_proxy_path: "/srv/galaxy/interactive_environments/proxy"
    interactive_environments_enabled:
      - jupyter
      - bam_iobio
    interactive_environments_config_files:
      - ie_name: jupyter
        file: jupyter.ini
        contents:
          docker:
            command: "docker -H tcp://docker.example.org:2376 --tlsverify {docker_args}"
            galaxy_url: "https://example.galaxyproject.org"
            docker_hostname: "docker.example.org"
      - ie_name: jupyter
        file: allowed_images.yml
        contents:
          - image: "bgruening/docker-jupyter-notebook:16.01.1"
            description: >
              The Jupyter notebook is the next iteration of IPython, allowing
              analysis in many different languages. This image features the Python,
              R, Julia, Haskell, Bash kernels and many scientific analysis stacks for
              each.
      - ie_name: bam_iobio
        file: bam_iobio.ini
        contents:
          docker:
            command: "docker -H tcp://docker.example.org:2376 --tlsverify {docker_args}"
            image: "qiaoy/iobio-bundle.bam-iobio:1.0-ondemand"
            galaxy_url: "https://example.galaxyproject.org"
            docker_hostname: "docker.example.org"
    interactive_environments_supervisor_conf_dir: "/srv/galaxy/supervisor/etc/supervisord.conf.d"
    interactive_environments_nginx_conf_dir: "/srv/galaxy/nginx.conf.d"
    galaxy_config:
      "app:main":
        interactive_environment_plugins_directory: "{{ interactive_environments_plugins_path }}"
        dynamic_proxy_manage: "False"
        dynamic_proxy_session_map: /srv/galaxy/var/gie_proxy_session_map.sqlite
        dynamic_proxy_bind_port: 8880
        dynamic_proxy_bind_ip: 0.0.0.0
        dynamic_proxy_external_proxy: "True"
        dynamic_proxy_prefix: gie_proxy
        galaxy_infrastructure_url: https://galaxy.example.org
  pre_tasks:
    - name: Include Interactive Environments package installation tasks
      include: roles/galaxyproject.interactive_environments/tasks/install_dependencies.yml
  roles:
    - galaxyproject.interactive_environments
```

License
-------

MIT

Author Information
------------------

[Nate Coraor](https://github.com/natefoo)  
