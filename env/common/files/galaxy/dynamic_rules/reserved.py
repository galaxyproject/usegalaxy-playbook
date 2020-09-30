##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

USERS = (
    'outreach@galaxyproject.org',
    'jen@bx.psu.edu',
    'anton@bx.psu.edu',
    'marius@galaxyproject.org',
)

NORM_USERS = [u.lower() for u in USERS]


def __dynamic_reserved(key, user_email):
    if user_email is not None and user_email.lower() in NORM_USERS:
        return 'reserved_' + key
    return 'slurm_' + key


def dynamic_normal_reserved(user_email):
    return __dynamic_reserved('normal', user_email)


def dynamic_normal_16gb_reserved(user_email):
    return __dynamic_reserved('normal_16gb', user_email)


def dynamic_normal_16gb_long_reserved(user_email):
    return __dynamic_reserved('normal_16gb_long', user_email)


def dynamic_normal_32gb_reserved(user_email):
    return __dynamic_reserved('normal_32gb', user_email)


def dynamic_normal_64gb_reserved(user_email):
    return __dynamic_reserved('normal_64gb', user_email)


def dynamic_multi_reserved(user_email):
    return __dynamic_reserved('multi', user_email)
