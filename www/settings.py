config = {
	  'webapp2_extras.auth': {
	    'user_model': 'models.User',
	    'user_attributes': ['name']
	  },
	  'webapp2_extras.sessions': {
	    'secret_key': 'EventM'
	  },

    # application name
    'app_name': "Sportcambodia",

    # the default language code for the application.
    # should match whatever language the site uses when i18n is disabled
    'app_lang': 'en',

    # Locale code = <language>_<territory> (ie 'en_US')
    # to pick locale codes see http://cldr.unicode.org/index/cldr-spec/picking-the-right-language-code
    # also see http://www.sil.org/iso639-3/codes.asp
    # Language codes defined under iso 639-1 http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    # Territory codes defined under iso 3166-1 alpha-2 http://en.wikipedia.org/wiki/ISO_3166-1
    # disable i18n if locales array is empty or None
    'locales': ['en_US'],

    # contact page email settings
    'contact_sender': "SENDER_EMAIL_HERE",
    'contact_recipient': "RECIPIENT_EMAIL_HERE",

    # Password AES Encryption Parameters
    # aes_key must be only 16 (*AES-128*), 24 (*AES-192*), or 32 (*AES-256*) bytes (characters) long.
    'aes_key': "9c20576a4330bbe719b23ac8bf3bb8a1",
    'salt': "RdbkETeF$<^>%%X^8|e[9td62`dobFL[V&F&**@`UP6vqjGL,>v+k@ma^zd6WdG0;H>o-SGG9ynk",

    # get your own consumer key and consumer secret by registering at https://dev.twitter.com/apps
    # callback url must be: http://[YOUR DOMAIN]/login/twitter/complete
    'twitter_consumer_key': 'TWITTER_CONSUMER_KEY',
    'twitter_consumer_secret': 'TWITTER_CONSUMER_SECRET',

    #Facebook Login
    # get your own consumer key and consumer secret by registering at https://developers.facebook.com/apps
    #Very Important: set the site_url= your domain in the application settings in the facebook app settings page
    # callback url must be: http://[YOUR DOMAIN]/login/facebook/complete
    # 'fb_api_key': 1608914109337384,
    # 'fb_secret': 'a3f33e363bb7e79c346102a5a5608c66',
    'fb_api_key': 588186611367815,
    'fb_secret': '090dd23d69edc0e42939c795dee71d50',
    
    #SMS Gateway    
    'sms_url': 'http://alerts.solutionsinfini.com/api/v3/index.php',
    'sms_method': 'sms',
    'sms_sender': 'SPTIND',
    'sms_api_key': 'Af421eaae7d416475631787567133a62c',
    
    #Instamojo Payment Gateway
    'pay_api_key': 'ab7696bec8e48112cd5c97e845cd94c2',
    'pay_auth_token': '5abb41c403ccf8a8490d5a8b14972481',
    'pay_salt': '5e3a81a16a38a18b302165a15a310848',
    
    #Linkedin Login
    #Get you own api key and secret from https://www.linkedin.com/secure/developer
    'linkedin_api': 'LINKEDIN_API',
    'linkedin_secret': 'LINKEDIN_SECRET',

    # Github login
    # Register apps here: https://github.com/settings/applications/new
    'github_server': 'github.com',
    'github_redirect_uri': 'http://www.example.com/social_login/github/complete',
    'github_client_id': 'GITHUB_CLIENT_ID',
    'github_client_secret': 'GITHUB_CLIENT_SECRET',

    # get your own recaptcha keys by registering at http://www.google.com/recaptcha/
    #'captcha_public_key': "6LcYVQkTAAAAAJNFJIxRbmGWdGJhrkpebiS33owm",
    #'captcha_private_key': "6LcYVQkTAAAAAAyn9eSic5bOEkE7OUmNPhsM4Xw1",

    'captcha_public_key': "6LflphMUAAAAAG2JC78JsG9PQpw_kjUji0-AMcC5",
    'captcha_private_key': "6LflphMUAAAAAMQBegp1o2E3PavZZLyrJ-6-aNhT",

    # Use a complete Google Analytics code, no just the Tracking ID
    # In config/boilerplate.py there is an example to fill out this value
    'google_analytics_code': "",

    # add status codes and templates used to catch and display errors
    # if a status code is not listed here it will use the default app engine
    # stacktrace error page or browser error page
    'error_templates': {
        403: 'errors/default_error.html',
        404: 'errors/default_error.html',
        500: 'errors/default_error.html',
    },

    # Enable Federated login (OpenID and OAuth)
    # Google App Engine Settings must be set to Authentication Options: Federated Login
    'enable_federated_login': True,

    # jinja2 base layout template
    'base_layout': 'base.html',

    # send error emails to developers
    'send_mail_developer': False,

    # fellas' list
    'developers': (
        ('Balamurugan B', 'bala@sportindia.in'),
    ),

    # If true, it will write in datastore a log of every otp sent
    'log_otp': True,
    
    # If true, it will write in datastore a log of every email sent
    'log_email': True,

    # If true, it will write in datastore a log of every visit
    'log_visit': True,

    # ----> ADD MORE CONFIGURATION OPTIONS HERE <----
    'send_mails': False
}

FLAG_BASIC=1 # Bit 0 - Basic
ROLE_BASIC=1

FLAG_BUSINESS=2 # Bit 1- Business User
ROLE_BUSINESS = FLAG_BASIC | FLAG_BUSINESS #3

FLAG_ADMIN=4 # Bit 2  - Admin User

ROLE_ADMIN=FLAG_BASIC | FLAG_BUSINESS  | FLAG_ADMIN #7
ROLE_FLAG_DICT = { 'basic':1, 'business':2, 'admin':4}

STATUS_DICT = {'pending_creation':0, 'pending_approval':1, 'approved':2}

GOOGLE_GEOENCODE_API_KEY = 'AIzaSyBjY5Qr_thE9YBgKCIQTj5bmBejOVScVWw'
#GOOGLE_MAPS_API_KEY = 'AIzaSyCa8ZkxYvy8RTATSXhyvbh0Wy1t4ogotTU'
GOOGLE_MAPS_API_KEY = 'AIzaSyDwDbVI4aakERW_vW0iwUXW7qReWbEwEN8'

DEFAULT_CITY = 'phnom penh'

ENABLE_GZIP=False

ENV_PROD=False

#TODO: Sender not enabled until we verify the sender email above , so gae platform can send emails
SENDER_ENABLED=False

DEFAULT_CACHE_EXPIRATION=5

ENTITY_CACHE_EXPIRATION = 86400

STATIC_CACHE_EXPIRATION = 86400*30

PAGE_SIZE = 3

# STATIC_URL="static/sportcambodia"

# STATIC_ROOT="SportCambodia/eventm"
