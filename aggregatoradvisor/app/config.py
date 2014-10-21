# Database Configuration
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://agad:@localhost/agad'


# Administrator Configuration
ADMINS = {
    # Username:  (PASSWORD_HASH, EMAIL_ADDRESS),
    'agadmin': ('frodo', 'email@address.com'),
}


# Forms Configuration
WTF_CSRF_ENABLED = True
SECRET_KEY = 'Shhh! This is a super secret key'


# Display Configuration
AGGREGATORS_DISPLAY_PER_PAGE = 15
AGGREGATORS_DISPLAY_PER_ROW = 3
AGGREGATORS_DISPLAY_IMAGE_SIZE = (300,300)
CITATIONS_DISPLAY_PER_PAGE = 10
