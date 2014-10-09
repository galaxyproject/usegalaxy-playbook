##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'outreach@galaxyproject.org',
)

def reserved_single( user_email ):
    if user_email in USERS:
        return 'slurm_reserved_single'
    return 'slurm_normal_single'
