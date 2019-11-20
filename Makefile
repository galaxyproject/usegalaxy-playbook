#
# Basic usage:
#   Run `update.yml` in env `<env>`:
#     $ make <env>`
#
# Advanced usage:
#   Run `<playbook>.yml` with `--tags=<TAGS>` and `--limit=<LIMIT>` in env `<env>`:
#     $ make TAGS=<tag[,tag ...]> LIMIT=<host_or_group[,host_or_group ...]> <env>-<playbook>

ifneq ($(strip $(TAGS)),)
TAGS_ARG = "--tags=$(TAGS)"
endif
ifneq ($(strip $(LIMIT)),)
LIMIT_ARG = "--limit=$(LIMIT)"
endif
PLAYBOOK := update

# These targets are automatically generated
main-backup: PLAYBOOK = backup
main-backup: main
main-client: PLAYBOOK = client
main-client: main
main-config: PLAYBOOK = config
main-config: main
main-gie: PLAYBOOK = gie
main-gie: main
main-pulsar: PLAYBOOK = pulsar
main-pulsar: main
main-restart: PLAYBOOK = restart
main-restart: main
main-snapshot: PLAYBOOK = snapshot
main-snapshot: main
main-stack: PLAYBOOK = stack
main-stack: main
main-static: PLAYBOOK = static
main-static: main
main-update: PLAYBOOK = update
main-update: main
test-backup: PLAYBOOK = backup
test-backup: test
test-client: PLAYBOOK = client
test-client: test
test-config: PLAYBOOK = config
test-config: test
test-gie: PLAYBOOK = gie
test-gie: test
test-pulsar: PLAYBOOK = pulsar
test-pulsar: test
test-restart: PLAYBOOK = restart
test-restart: test
test-snapshot: PLAYBOOK = snapshot
test-snapshot: test
test-stack: PLAYBOOK = stack
test-stack: test
test-static: PLAYBOOK = static
test-static: test
testtoolshed-stack_extras: PLAYBOOK = stack_extras
testtoolshed-stack_extras: testtoolshed
testtoolshed-stack: PLAYBOOK = stack
testtoolshed-stack: testtoolshed
testtoolshed-update: PLAYBOOK = update
testtoolshed-update: testtoolshed
test-update: PLAYBOOK = update
test-update: test
toolshed-stack: PLAYBOOK = stack
toolshed-stack: toolshed
toolshed-update: PLAYBOOK = update
toolshed-update: toolshed


test main testtoolshed toolshed:
	ansible-playbook -i env/$@/inventory env/$@/$(PLAYBOOK).yml $(TAGS_ARG) $(LIMIT_ARG)

Makefile: Makefile.in
	sed "s/^## AUTOGEN TARGETS/$$(bash ./.support/targets.sh)/" Makefile.in > Makefile

.PHONY: test main testtoolshed toolshed
