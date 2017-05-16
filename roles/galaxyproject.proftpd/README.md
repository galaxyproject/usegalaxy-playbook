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
  ConnectInfo documentation for the "connection-info" parameter][proftpd-connect-info] for details.
- `galaxy_user`: The name of the user running the Galaxy server.
- `galaxy_ftp_upload_dir`: Path to the Galaxy FTP upload directory, should match `ftp_upload_dir` in your Galaxy config.
- Additionally, you should set `User` and `Group` in `proftpd_options` to the user and group names of your Galaxy user.

[proftpd-connect-info]: http://www.proftpd.org/docs/contrib/mod_sql.html#SQLConnectInfo

### Optional variables ###

- `proftpd_display_connect`: Message to display when users connect to the FTP server. This should be the message, not
  the path to a file (this role will create the file and set [DisplayConnect][proftpd-display-connect] accordingly.
- `proftpd_galaxy_auth`: Attempt to authenticate users against a [Galaxy][galaxy] database.
- `proftpd_options`: Set arbitrary options in the server config context of `proftpd.conf` (they will actually be set
  in an included config file). This is a list of hashes (dictionaries) where keys are ProFTPD config options and values
  are the option's value.
- `proftpd_galaxy_default_options`: Default options that are set in `proftpd.conf` that are overridden when
  `proftpd_galaxy_auth` is set. The defaults can be found in `defaults/main.yml`.
- `proftpd_galaxy_options`: Additional options that are set in the server config context if `proftpd_galaxy_auth` is
  set.
- `proftpd_sql_user` (default: the value of `galaxy_user`): Value of the `username` parameter to
  [SQLConnectInfo][sql-connect-info].
- `proftpd_sql_password` (default: empty): Value of the `password` parameter to [SQLConnectInfo][sql-connect-info].
- `galaxy_user_uid` (default: looked up automatically): UID of the user running the Galaxy server.
- `galaxy_user_gid` (default: looked up automatically): GID of the user running the Galaxy server.

These variables control the use of TLS. If unset, TLS will not be enabled. See [mod-tls documentation][mod_tls] and
Example Playbook for usage.

- `proftpd_ssl_src_dir`: Where to copy SSL certificates from.
- `proftpd_conf_ssl_certificate`: Path on the remote host where the SSL certificate file should be placed.
- `proftpd_conf_ssl_certificate_key`: Path on the remote host where the SSL private key file should be placed.
- `sslkeys`: A hash (dictionary) containing private keys. Keys are the filenames (without leading path elements)
  matching `proftpd_conf_ssl_certificate_key`.
  `proftpd_tls_protocol` (default: `TLSv1.1 TLSv1.2`): Set `TlSProtocol`.
- `proftpd_tls_cipher_suite` (default:
  `EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EECDH+aRSA+SHA256:EECDH:EDH+aRSA:!RC4:!aNULL:!eNULL:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS`):
  Set `TLSCipherSuite`
- 

[mod-tls]: http://www.proftpd.org/docs/contrib/mod_tls.html
[display-connect]: http://www.proftpd.org/docs/directives/linked/config_ref_DisplayConnect.html

Dependencies
------------

Although not a requirement, [geerlingguy.repo-epel][repo-epel] can be used to enable EPEL with Ansible.

[repo-epel]: https://galaxy.ansible.com/geerlingguy/repo-epel/

Example Playbook
----------------

Install ProFTPD for Galaxy with TLS:

```
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
    - galaxyproject.proftpd
```

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

[Nate Coraor](https://github.com/natefoo)  
