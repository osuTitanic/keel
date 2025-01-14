
import dotenv
import os

dotenv.load_dotenv(override=False)

API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', 8000))

API_RATELIMIT_ENABLED = eval(os.environ.get('API_RATELIMIT_ENABLED', 'True').capitalize())
API_RATELIMIT_WINDOW = int(os.environ.get('API_RATELIMIT_WINDOW', 60))
API_RATELIMIT_LIMIT = int(os.environ.get('API_RATELIMIT_LIMIT', 800))

POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_POOLSIZE = int(os.environ.get('POSTGRES_POOLSIZE', 10))
POSTGRES_POOLSIZE_OVERFLOW = int(os.environ.get('POSTGRES_POOLSIZE_OVERFLOW', 30))

S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_BASEURL    = os.environ.get('S3_BASEURL')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

APPROVED_MAP_REWARDS = eval(os.environ.get('APPROVED_MAP_REWARDS', 'False').capitalize())
FREE_SUPPORTER = eval(os.environ.get('FREE_SUPPORTER', 'True').capitalize())
ENABLE_SSL = eval(os.environ.get('ENABLE_SSL', 'False').capitalize())
S3_ENABLED = eval(os.environ.get('ENABLE_S3', 'True').capitalize())
DEBUG = eval(os.environ.get('DEBUG', 'False').capitalize())
RELOAD = eval(os.environ.get('RELOAD', str(DEBUG)).capitalize())
SCORE_RESPONSE_LIMIT = int(os.environ.get('SCORE_RESPONSE_LIMIT', 50))
DOMAIN_NAME = os.environ.get('DOMAIN_NAME')

EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', '')
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', '')
EMAIL_DOMAIN = EMAIL_SENDER.split('@')[-1]
EMAILS_ENABLED = bool(EMAIL_PROVIDER and EMAIL_SENDER)

SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT') or '587')
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
MAILGUN_URL = os.environ.get('MAILGUN_URL', 'api.eu.mailgun.net')

RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')

OFFICER_WEBHOOK_URL = os.environ.get('OFFICER_WEBHOOK_URL')
EVENT_WEBHOOK_URL = os.environ.get('EVENT_WEBHOOK_URL')
DATA_PATH = os.path.abspath('.data')

FRONTEND_SECRET_KEY = os.environ.get('FRONTEND_SECRET_KEY', 'somethingrandom')
FRONTEND_TOKEN_EXPIRY = int(os.environ.get('FRONTEND_TOKEN_EXPIRY', 3600))
FRONTEND_REFRESH_EXPIRY = int(os.environ.get('FRONTEND_REFRESH_EXPIRY', 3600*24*30))

OSU_BASEURL = f'http{"s" if ENABLE_SSL else ""}://osu.{DOMAIN_NAME}'
STATIC_BASEURL = f'http{"s" if ENABLE_SSL else ""}://s.{DOMAIN_NAME}'
VERSION = '1.0.0'