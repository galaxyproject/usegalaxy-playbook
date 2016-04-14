nginx
=====

An [Ansible][ansible] role for installing and managing [nginx][nginx] servers.
This role does **not** install a version of nginx that includes the nginx
upload module, which [Galaxy][galaxy] uses. Adding support for the Galaxy
builds of nginx is a TODO item.

[ansible]: http://www.ansible.com/
[nginx]: http://nginx.org/
[galaxy]: http://galaxyproject.org/

Requirements
------------

This role installs nginx from APT on Debian systems, or EPEL on Enterprise
Linux systems.  Other systems and installation methods are not supported.

Role Variables
--------------

### Optional variables ###

- `nginx_flavor` (default: `full`): nginx package to install (for choices, see
  the `nginx` metapackage providers for your Debian-based distribution). On
  RedHat-based distributions, this can either be `galaxy` (for "Galaxy nginx",
  which includes the nginx upload and pam modules), or any other value for EPEL
  nginx.
- `nginx_configs`: A list of virtualhosts (relative to `templates/nginx/`). 
- `nginx_conf_http`: Set arbitrary options in the `http{}` section of
  `nginx.conf`. This is a hash (dictionary) where keys are nginx config options
  and values are the option's value.
- `nginx_default_redirect_uri`: When using nginx from EPEL, a default
  virtualhost is enabled. This option controls what URI the default virtualhost
  should be redirected to. nginx variables are supported.
- `nginx_supervisor`: Run nginx under supervisor (requires setting certain
  supervisor variables).

These variables control the use of SSL. If unset, SSL will not be enabled. See
Example Playbook for usage.

- `nginx_ssl_src_dir`: Where to copy SSL certificates from.
- `nginx_conf_ssl_certificate`: Path on the remote host where the SSL
  certificate file should be placed.
- `nginx_conf_ssl_certificate_key`: Path on the remote host where the SSL
  private key file should be placed.
- `sslkeys`: A hash (dictionary) containing private keys. Keys are the
  filenames (without leading path elements) matching
  `nginx_conf_ssl_certificate_key`.
- `nginx_conf_ssl_ciphers`: The `ssl_ciphers` option in `nginx.conf`.

Dependencies
------------

Although not a requirement, [geerlingguy.repo-epel][repo-epel] can be used to
enable EPEL with Ansible.

[repo-epel]: https://galaxy.ansible.com/geerlingguy/repo-epel/

Example Playbook
----------------

Install nginx with SSL:

```
- name: Install and configure nginx
  hosts: webservers
  remote_user: root
  vars:
    sslkeys:
      'snakeoil_privatekey.pem': |
        -----BEGIN PRIVATE KEY-----
        MIIE...
        -----END PRIVATE KEY-----
    nginx_conf_ssl_certificate: snakeoil_cert.pem
    nginx_conf_ssl_certificate_key: snakeoil_privatekey.pem
    nginx_ssl_src_dir: files/ssl
    nginx_configs:
      - vhost1
      - vhost2
    nginx_conf_http:
      client_max_body_size: 1g
  roles:
    - galaxyprojectdotorg.nginx
```

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

[Nate Coraor](https://github.com/natefoo)  
