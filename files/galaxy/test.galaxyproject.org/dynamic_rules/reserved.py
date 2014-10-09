##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'outreach@galaxyproject.org',
)

def reserved_single( user_email ):
    if user_email in USERS:
        return 'roundup_single_reserved'
    return 'rodeo_normal'

def reserved_multi( user_email ):
    if user_email in USERS:
        return 'roundup_multi_reserved'
    return 'roundup_multi_static_walltime'
