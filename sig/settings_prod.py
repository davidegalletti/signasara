from .settings import *
from .keep_safe import PROD_SECRET_KEY, PROD_DATABASE_PASSWORD
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = PROD_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SITE_NAME = 'SICS NASARA PROD'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Directory for collected static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Directory for app-specific static files
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Directory for uploaded media files

SITE_DOMAIN = 'sicscl.nasaraperilburkina.org'
ALLOWED_HOSTS.append('sicscl.nasaraperilburkina.org')
SECRET_KEY = PROD_SECRET_KEY

DATABASES['default']['PASSWORD'] = PROD_DATABASE_PASSWORD
DATABASES['default']['NAME'] = 'sicsnasara_prod'

CSRF_TRUSTED_ORIGINS = ['https://sicscl.nasaraperilburkina.org']

LOGGING_BASE_DIR = '/var/log/sicsnasara/prod/'
for h in LOGGING["handlers"]:
    if 'filename' in LOGGING["handlers"][h]:
        LOGGING["handlers"][h]["filename"] = "%s%s" % (LOGGING_BASE_DIR,
                                                       LOGGING["handlers"][h]["filename"].split("/")[-1])

