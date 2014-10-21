# Database Configuration
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://agad:agadsecret@localhost/agad'


# Administrator Configuration
ADMINS = {
    # Username:  (PASSWORD_HASH, EMAIL_ADDRESS),
    'agadmin': ('frodo', 'email@address.com'),
}


# Forms Configuration
WTF_CSRF_ENABLED = True
SECRET_KEY = 'Shhh! This is a super secret key'


# Display Configuration
AGGREGATORS_DISPLAY_IMAGE_SIZE = (300,300)
