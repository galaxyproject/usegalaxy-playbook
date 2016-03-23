##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'outreach@galaxyproject.org',
    'jen@bx.psu.edu',
    'anton@bx.psu.edu',
)

NORM_USERS = [ u.lower() for u in USERS ]

def dynamic_normal_reserved( user_email ):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved'
    return 'slurm_normal'

def dynamic_normal_reserved_16gb( user_email ):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved_16gb'
    return 'slurm_normal_16gb'

def dynamic_normal_reserved_32gb( user_email ):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved_32gb'
    return 'slurm_normal_32gb'

def dynamic_normal_reserved_64gb( user_email ):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved_64gb'
    return 'slurm_normal_64gb'

def dynamic_multi_reserved( user_email ):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved_multi'
    return 'slurm_multi'
