#!/usr/bin/env bash
# https://stackoverflow.com/questions/20983217/how-to-display-the-subject-alternative-name-of-a-certificate
sed -ne 's/^\( *\)Subject:/\1/p;/X509v3 Subject Alternative Name/{N;s/^.*\n//;:a;s/^\( *\)\(.*\), /\1\2\n\1/;ta;p;q; }' < <(openssl x509 -in $1 -noout -text) | sed 's/\s*CN=//g;s/\s*DNS://' | sort -u
