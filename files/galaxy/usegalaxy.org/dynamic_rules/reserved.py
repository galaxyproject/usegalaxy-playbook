##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'outreach@galaxyproject.org',
)

def reserved_single( user_email ):
    if user_email in USERS:
        return 'rodeo_normal'
    return 'rodeo_normal'
