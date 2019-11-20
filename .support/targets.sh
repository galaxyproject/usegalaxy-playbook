#!/bin/bash

for f in env/*/*.yml; do
    read env pbfile < <(echo "$f" | awk -F/ '$2 != "common" && $3 !~ /^_/ {print $2, $3}')
    [ -n "$env" ] || continue
    pb="${pbfile%%.*}"
    echo -n "${env}-${pb}: PLAYBOOK = ${pb}\\n"
    echo -n "${env}-${pb}: ${env}\\n"
done
