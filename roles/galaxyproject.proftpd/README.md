proftpd
=======

An [Ansible][ansible] role for installing and managing [proftpd][proftpd] servers. This role is designed to facilitate
the installation of ProFTPD for [Galaxy][galaxy] servers, and can configure ProFTPD to authenticate users against the
Galaxy PostgreSQL database. It can also configure TLS for FTPS (**note: NOT SFTP**).

[ansible]: http://www.ansible.com/
[proftpd]: http://www.proftpd.org/
[galaxy]: http://galaxyproject.org/

Requirements
------------

This role installs ProFTPD from APT on Debian systems, EPEL on Enterprise Linux systems.  Other systems and installation
methods are not supported.

Role Variables
--------------

### Required variables ###

**Variables required if `proftpd_galaxy_auth` is set**:

- `proftpd_sql_db`: Database name to connect to for authentication info. Can include host information, see the [ProFTPD
  SQLConnectInfo documentation for the "connection-info" parameter][proftpd-sql-connect-info] for details.
- `galaxy_user`: The name of the user running the Galaxy server.
- `galaxy_ftp_upload_dir`: Path to the Galaxy FTP upload directory, should match `ftp_upload_dir` in your Galaxy config.
- Additionally, you should set `User` and `Group` in `proftpd_options` to the user and group names of your Galaxy user.

[proftpd-sql-connect-info]: http://www.proftpd.org/docs/contrib/mod_sql.html#SQLConnectInfo

### Optional variables ###

**Configuration**

- `proftpd_options`: Set arbitrary options in the server config context of `proftpd.conf` (they will actually be set
  in an included config file). This is a list of hashes (dictionaries) where keys are ProFTPD config options and values
  are the option's value. Block tags such as `<IfModule>` are not supported. Options set in `proftpd_options` will
  cause matching options in the base `proftpd.conf` file to be commented out.
- `proftpd_global_options`: Set arbitrary options in the `<Global>` context, same format as `proftpd_options`. Options
  set in `proftpd_global_options` will ***NOT*** cause matching options in the base `proftpd.conf` file to be commented
  out.

**Enabling/disabling optional features**

- `proftpd_galaxy_auth`: Attempt to authenticate users against a [Galaxy][galaxy] database.
- `proftpd_conf_ssl_certificate` and `proftpd_conf_ssl_certificate_key`: If set, enables TLS autoconfiguration. See
  **FTP over SSL/TLS** below.

**Display-on-connect message**

- `proftpd_display_connect`: Message to display when users connect to the FTP server. This should be the message, not
  the path to a file (this role will create the file and set [DisplayConnect][proftpd-display-connect] accordingly.
- `proftpd_display_connect_context` (default: `server`): If set to `global`, place the `ServerConnect` directive into a
  `<Global>` block. If set to `server`, it is placed in the server context.

[proftpd-display-connect]: http://www.proftpd.org/docs/directives/linked/config_ref_DisplayConnect.html

**FTP over SSL/TLS**

These variables control the use of TLS. If unset, TLS will not be enabled. See [mod_tls documentation][proftpd-mod-tls]
and Example Playbook for usage.

- `proftpd_ssl_src_dir`: Where to copy SSL certificates from.
- `proftpd_conf_ssl_certificate`: Path on the remote host where the SSL certificate file should be placed.
- `proftpd_conf_ssl_certificate_key`: Path on the remote host where the SSL private key file should be placed.
- `proftpd_conf_ssl_ca_certificate`: Path on the remote host where the SSL CA certificate chain should be placed. See
  the [TLSCertificateChainFile][proftpd-tls-certificate-chain-file] documentation for the format of this file.
- `sslkeys`: A hash (dictionary) containing private keys. Keys are the filenames (without leading path elements)
  matching `proftpd_conf_ssl_certificate_key`.
  `proftpd_tls_protocol` (default: `TLSv1.1 TLSv1.2`): Set `TlSProtocol`.
- `proftpd_tls_cipher_suite` (default:
  `EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EECDH+aRSA+SHA256:EECDH:EDH+aRSA:!RC4:!aNULL:!eNULL:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS`):
  Set `TLSCipherSuite`
- `proftpd_tls_context` (default: `server`): If set to `global`, place TLS configuration directives that are
  valid in the `<Global>` context into a `<Global>` block. If set to `server`, they are placed in the server context.
- `proftpd_tls_sesscache_path` (default: `/run/proftpd/sesscache`): Path to ProFTPD shm TLS session cache.
- `proftpd_tls_sesscache_timeout` (default: `300`): TLS session cache timeout (in seconds).
- `proftpd_tls_renegotiate`: (default: unset): TLS renegotation time (in seconds).


[proftpd-mod-tls]: http://www.proftpd.org/docs/contrib/mod_tls.html
[proftpd-tls-certificate-chain-file]: http://www.proftpd.org/docs/directives/linked/config_ref_TLSCertificateChainFile.html

**Galaxy authentication options**

These options are used if `proftpd_galaxy_auth` is set.

- `proftpd_galaxy_options`: Additional options to set in the Galaxy authentication include file. Options set in
  `proftpd_galaxy_options` will cause matching options in the base `proftpd.conf` file to be commented out.
- `proftpd_galaxy_default_options`: Default options set in the Galaxy authentication include file, you should only need
  to explicitly set this if you need to remove items from the defaults. Matching options set in
  `proftpd_galaxy_options` override the defaults. The defaults can be found in `defaults/main.yml`.
- `proftpd_sql_user` (default: the value of `galaxy_user`): Value of the `username` parameter to
  [SQLConnectInfo][proftpd-sql-connect-info].
- `proftpd_sql_password` (default: empty): Value of the `password` parameter to [SQLConnectInfo][proftpd-sql-connect-info].
- `galaxy_user_uid` (default: looked up automatically): UID of the user running the Galaxy server.
- `galaxy_user_gid` (default: looked up automatically): GID of the user running the Galaxy server.
- `proftpd_galaxy_modules`: Default list of modules that will be loaded (uncommented in the base `proftpd.conf`) to
  support Galaxy authentication, you should only need to explicitly set this if you need to change the default list.
  The defaults can be found in `defaults/main.yml`.
- `proftpd_galaxy_auth_context` (default: `server`): If set to `global`, place Galaxy authentication directives
  into a `<Global>` block. If set to `server`, they are placed in the server context.

**Virtual servers/hosts**

- `proftpd_virtualhosts`: Defines [ProFTPD virtual servers/hosts][proftpd-vhost]. If set, this should be a list where
  each item is a hash (dict) with keys `id` (used in the vhost config file name), `address` (used in `<VirtualHost
  ADDRESS>`) and `options`, a list in the same format as `proftpd_options` below. Block tags such as `<IfModule>` are
  not supported.

It may be helpful to set `Port: 0` in `proftpd_options` to disable the server context when using virtual servers.

[proftpd-vhost]: http://www.proftpd.org/docs/howto/Vhost.html

Dependencies
------------

Although not a requirement, [geerlingguy.repo-epel][repo-epel] can be used to enable EPEL with Ansible.

[repo-epel]: https://galaxy.ansible.com/geerlingguy/repo-epel/

Example Playbook
----------------

Install ProFTPD for Galaxy with TLS:

```yaml
- name: Install and configure ProFTPD
  hosts: ftpservers
  remote_user: root
  vars:
    galaxy_user: galaxy
    galaxy_ftp_upload: /srv/galaxy/ftp
    proftpd_display_connect: |
      example.org FTP server

      Unauthorized access is prohibited
    proftpd_galaxy_auth: yes
    proftpd_options:
      - User: galaxy
      - Group: galaxy
    proftpd_sql_db: galaxy@/var/run/postgresql
    proftpd_sql_user: galaxy
    sslkeys:
      'snakeoil_privatekey.pem': |
        -----BEGIN PRIVATE KEY-----
        MIIE...
        -----END PRIVATE KEY-----
    proftpd_conf_ssl_certificate: snakeoil_cert.pem
    proftpd_conf_ssl_certificate_key: snakeoil_privatekey.pem
    proftpd_ssl_src_dir: files/ssl

  roles:
    - galaxyprojectdotorg.proftpd
```

If using virtual servers in conjunction with Galaxy authentication, [DefaultRoot][proftpd-default-root]'s `chroot(2)`
will fail when used inside of a `<VirtualHost>`. In this case, [mod_vroot][proftpd-mod-vroot] should be used (you may
find that it's already enabled for the server config context anyway).  The following variables accomplish this:

```yaml
proftpd_galaxy_auth_context: global
proftpd_galaxy_modules:
  - mod_sql.c
  - mod_sql_passwd.c
  - mod_sql_postgres.c
  - mod_vroot.c
proftpd_galaxy_options:
  - VRootEngine: 'on'
```

[proftpd-default-root]: http://www.proftpd.org/docs/directives/linked/config_ref_DefaultRoot.html
[proftpd-mod-vroot]: http://www.castaglia.org/proftpd/modules/mod_vroot.html

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

[Nate Coraor](https://github.com/natefoo)  
