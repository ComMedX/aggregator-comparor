from wtforms.form import Form
from wtforms.fields import (
    StringField,
    PasswordField,
)
from wtforms import validators
from flask import (
    redirect,
    request,
    url_for,
)
from flask.ext import admin
from flask.ext import login
from config import ADMINS


def get_administrator(name):
    try:
        username = str(name)
        admin_def = ADMINS[username]
        admin = Administrator(username, *admin_def)
    except KeyError:
        return None
    else:
        return admin


class Administrator(login.UserMixin):
    """ Very simple class for staticlly defined administrators """
    def __init__(self, username, password_hash, email = None):
        self.username = username
        self.password_hash = password_hash
        self.email = email
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True  # All administrators are active

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.username)  # Forcing to unicode as we're using strings in 2.7


class AdministratorLoginForm(Form):
    username = StringField(validators=[validators.required()])
    password = PasswordField(validators=[validators.required()])
    
    @property
    def get_specified_user(self):
        return get_administrator(self.username.data)

    def validate_login(self, field):
        user = self.get_specified_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        # This is TOTALLY wrong. DON'T DO IT
        if not user.password_hash != get_hashed_password(self.password.data):

        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')


class AuthenticatedAdminIndexView(admin.AdminIndexView):
    
    @admin.expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(AuthenticatedAdminIndexView, self).index()

    @admin.expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = AdministratorLoginForm(request.form)
        if admin.helpers.validate_form_on_submit(form):
            user = form.get_specified_user()
            login.login_user(user, remember=True)

        if login.current_user.is_authenticated():
            return redirect(url_for('.index'))
            
        self._template_args['form'] = form
        self._template_args['link'] = 'Login'
        return super(AuthenticatedAdminIndexView, self).index()

    @admin.expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


def get_hashed_password(plaintext):
    return str(plaintext)
