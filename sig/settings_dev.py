from .settings import *
from .keep_safe import DEV_SECRET_KEY, DEV_DATABASE_PASSWORD


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = DEV_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SITE_NAME = 'SICS NASARA DEV'

SITE_DOMAIN = 'sics-dev-cl.nasaraperilburkina.org'
ALLOWED_HOSTS.append('sics-dev-cl.nasaraperilburkina.org')
SECRET_KEY = DEV_SECRET_KEY

DATABASES['default']['PASSWORD'] = DEV_DATABASE_PASSWORD
DATABASES['default']['NAME'] = 'sicsnasara_dev'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '/dbsig.sqlite3',
    }
}

CSRF_TRUSTED_ORIGINS = ['https://sics-dev-cl.nasaraperilburkina.org']

LOGGING_BASE_DIR = '/var/log/sicsnasara/dev/'
for h in LOGGING["handlers"]:
    if 'filename' in LOGGING["handlers"][h]:
        LOGGING["handlers"][h]["filename"] = "%s%s" % (LOGGING_BASE_DIR,
                                                       LOGGING["handlers"][h]["filename"].split("/")[-1])

