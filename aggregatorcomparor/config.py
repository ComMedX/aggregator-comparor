PORT = 8080
DEBUG = True

# Database Configuration
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://aggcomp:aggcomp@localhost/aggcomp'
SQLALCHEMY_ECHO = False

# Administrator Configuration { Username: (PASSWORD_HASH, EMAIL_ADDRESS), }
ADMINS = {
    'agadmin': ('frodo', 'email@address.com'),
}

# Forms Configuration
WTF_CSRF_ENABLED = True
SECRET_KEY = 'Shhh! This is a super secret key'

DOI_URL_TPL = u"http://dx.doi.org/{0.doi}"
LIGAND_SOURCE_NAME = "CSD"
LIGAND_SOURCE_URL_TPL = u"https://summary.ccdc.cam.ac.uk/structure-summary?refcode={0.refcode!s}"

# Display Configuration
MOLECULES_DISPLAY_IMAGE_SIZE = (300,300)
MOLECULES_DISPLAY_PER_PAGE = 30
MOLECULE_SEARCH_RESULT_LIMIT = None