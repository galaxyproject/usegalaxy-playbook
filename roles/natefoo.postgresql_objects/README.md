PostgreSQL Objects
==================

PostgreSQL Objects is an [Ansible][ansible] role for managing PostgreSQL users,
groups databases, and privileges. It is a small wrapper around the
[`postgresql_user`][pguser], [`postgresql_db`][pgdb] and
[`postgresql_privs`][pgprivs] standard modules provided with Ansible. Many
PostgreSQL roles exist in [Ansible Galaxy][ansiblegalaxy] but none exist for
only managing database objects without managing the server installation and
configuration.

Ansible >= 1.8 is required due to the use of the `default( omit )` construct in
module parameter templating.

[ansible]: http://www.ansible.com
[pguser]: http://docs.ansible.com/postgresql_user_module.html
[pgdb]: http://docs.ansible.com/postgresql_db_module.html
[pgprivs]: http://docs.ansible.com/postgresql_privs_module.html
[ansiblegalaxy]: https://galaxy.ansible.com
[shell]: http://docs.ansible.com/shell_module.html

Requirements
------------

This role has the same dependencies as the `postgresql_*` modules, namely, The
Python [`psycopg2`][psycopg2] module. This can easily be installed via a
pre-task in the same play as this role:

    - hosts: dbservers
        pre_tasks:
          - name: Install psycopg2
            apt: pkg=python-psycopg2 state=installed
            become: yes
            when: ansible_os_family = 'Debian'
          - name: Install psycopg2
            yum: pkg=python-psycopg2 state=installed
            become: yes
            when: ansible_os_family = 'RedHat'
        roles:
          - postgresql_objects

[psycopg2]: http://initd.org/psycopg/

Role Variables
--------------

Objects are configured via the following variables:

- `postgresql_objects_users`: A list of PostgreSQL users to create or drop.
  List items are dictionaries, keys match the [`postgresql_user`][pguser]
  module parameters.
- `postgresql_objects_groups`: A list of PostgreSQL groups to create or drop.
  List items are dictionaries, keys match the [`postgresql_user`][pguser]
  module parameters with the addition of the `users` key, which should itself
  be a list of users to add to the group. List items are dictionaries which
  should have the `name` key (required) and optionally the `state` key (whose
  values are either `present` (default) or `absent`).
- `postgresql_objects_databases`: A list of databases to create or drop. List
  items are dictionaries, keys match the [`postgresql_db`][pgdb] module
  parameters.
- `postgresql_objects_privileges`: A list of privileges to grant or revoke.
  List items are dictionaries, keys match the [`postgresql_privs`][pgprivs]
  module parameters.
- `postgresql_objects_ignore_revoke_failure`: True or false. Revoking
  privileges from a nonexistent user, database, or table would normally cause a
  failure since PostgreSQL will return an error on such an operation. If not
  handled, this would prevent this role from being used idempotently. See
  caveats below.

Additional variables (`postgresql_objects_login_host`,
`postgresql_objects_login_user`, `postgresql_objects_login_password` and
`postgresql_objects_port`) control how to connect to the database as a user
that has privileges to perform the requested changes. However, these can be
left unset if you use a system user with administrative privileges in
PostgreSQL, (such as with `sudo: yes` and `sudo_user: postgres` in your play).

**`postgresql_objects_groups` caveats**: Managing group membership **does not
use Ansible modules** because the existing set of provided modules do not
provide the needed functionality for managing groups. Instead, groups are
managed by piping SQL to the `psql(1)` command line utility with Ansible's
[`shell`][shell] module, so extra care should be taken when using the group
functionality. Also, the `postgresql_objects_login_password` option cannot be
used with group membership management.

**`postgresql_objects_ignore_revoke_failure` caveats**: If you typo a user, db,
or table to revoke, this will happily indicate that revoking was successful
(the named user does not have the listed privilege(s) on the provided db, after
all) and continue on. This optional also only works if your roles parameter in
postgresql_privileges only contains one role, since the entire revoke will fail
and roll back if any of the listed roles don't exist, and that's a condition
that we don't want to treat as successful. The PostgreSQL error string is
checked for the text 'does not exist', so if your PostgreSQL server returns
messages in a different locale, this feature probably won't work.

Example Playbook
----------------

Set up a user for remote administration. The user gets a database so connecting
as that user does not fail (the `postgresql_*` modules do not provide a
mechanism to control what database to connect to as the login user):

    - hosts: dbservers
      vars:
        postgresql_objects_users:
          - name: pgadmin
            password: shrubbery
            role_attr_flags: SUPERUSER
        postgresql_objects_databases:
          - name: pgadmin
            owner: pgadmin
      roles:
        - role: postgresql_objects
          become: yes
          become_user: postgres

Create a passwordless user (for use with unix domain socket connections) with a
database of the same name:

    - hosts: dbservers
      vars:
        postgresql_objects_users:
          - name: foo
        postgresql_objects_databases:
          - name: foo
            owner: foo
        postgresql_objects_login_user: pgadmin
        postgresql_objects_login_password: shrubbery
      roles:
        - role: postgresql_objects

Grant all privileges on table `bar` in database `foo` to new user `baz`, and
SELECT privileges to `baz` on sequence `bar_quux_seq` in database `foo`:

    - hosts: dbservers
      vars:
        postgresql_objects_users:
          - name: baz
            db: foo
            priv: "bar:ALL"
        postgresql_objects_privileges:
          - database: foo
            roles: baz
            objs: bar_quux_seq
            type: sequence
            privs: SELECT
      roles:
        - role: postgresql_objects
          become: yes
          become_user: postgres

Create a group `plugh` and add `foo` and `baz` to this group:

    - hosts: dbservers
      vars:
        postgresql_objects_groups:
          - name: plugh
            users:
              - name: foo
              - name: baz
      roles:
        - role: postgresql_objects
          become: yes
          become_user: postgres

Revoke specific privileges for user `foo`, remove user `baz` from group
`plugh`, and delete user `baz`:

    - hosts: dbservers
      vars:
        postgresql_objects_users:
          - name: baz
            state: absent
        postgresql_objects_groups:
          - name: plugh
            users:
              - name: baz
                state: absent
        postgresql_objects_privileges:
          - database: foo
            roles: foo
            objs: bar_quux_seq
            type: sequence
            privs: ALL
            state: absent
          - database: foo
            roles: baz
            objs: bar
            privs: ALL
            state: absent
          - database: foo
            roles: baz
            objs: bar_quux_seq
            type: sequence
            privs: ALL
            state: absent
      roles:
        - role: postgresql_objects
          become: yes
          become_user: postgres

Dependencies
------------

None

License
-------

[MIT](https://opensource.org/licenses/MIT)

Author Information
------------------

[Contributors on GitHub](https://github.com/natefoo/ansible-postgresql-objects/graphs/contributors)
