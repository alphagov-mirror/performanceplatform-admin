COOKIE_SECRET_KEY = 'placeholder_cookie_secret_key'

ADMIN_HOST = 'https://admin-beta.development.performance.service.gov.uk'

BACKDROP_HOST = 'http://www.development.performance.service.gov.uk'
STAGECRAFT_HOST = 'http://stagecraft.development.performance.service.gov.uk'

SIGNON_OAUTH_ID = 'oauth_id'
SIGNON_OAUTH_SECRET = 'oauth_secret'
SIGNON_BASE_URL = 'http://signon.dev.gov.uk'

DEBUG = True

# You can use development_local_overrides.py in this directory to set config
# that is unique to your development environment, like OAuth IDs and secrets.
# It is not in version control.
try:
    from development_local_overrides import *
except ImportError as e:
    pass
