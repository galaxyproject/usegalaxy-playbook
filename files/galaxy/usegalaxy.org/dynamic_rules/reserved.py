##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'usinggalaxy2@gmail.com',
)

def dynamic_normal_reserved( user_email ):
    if user_email in USERS:
        return 'reserved'
    return 'slurm_normal'

def dynamic_normal_reserved_16gb( user_email ):
    if user_email in USERS:
        return 'reserved_16gb'
    return 'slurm_normal_16gb'

def dynamic_normal_reserved_64gb( user_email ):
    if user_email in USERS:
        return 'reserved_64gb'
    return 'slurm_normal_64gb'

def dynamic_multi_reserved( user_email ):
    if user_email in USERS:
        return 'reserved_multi'
    return 'slurm_multi'
