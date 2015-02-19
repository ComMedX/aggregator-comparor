from urllib import quote
from flask import url_for
from flask.ext.admin import form
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext import login
from jinja2 import Markup
from wtforms import fields
from aggregatorcomparor import (
    admin,
    db,
)
from aggregatorcomparor.models import (
    Aggregator,
    Citation,
    Ligand,
    AggregatorReport,
)
from aggregatorcomparor.helpers import image_url_for


# Require administrator access to admin forms (trivial but important)
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated()


class MoleculeView(object):
    def _thumbnail(self, context, model, name):
        return Markup('<img src="{0}">'.format(image_url_for(model)))


class AggregatorView(AuthenticatedModelView, MoleculeView):
    column_list = ('id', 'smiles', 'logp', 'added', 'structure')
    form_columns = ('structure',  'inchikey', 'logp', 'added', 'name', 'citations')
    form_exclude_columns = ('reports',)        # Don't show report mappings
    form_overrides = {
        'structure': fields.StringField
    }
    column_formatters = {
        'structure': MoleculeView._thumbnail,
    }
    form_extra_fields = {
        'inchikey': fields.StringField(),
        'logp': fields.FloatField(),
    }
    form_widget_args = {
        #'structure': {'disabled': True},
        'inchikey': {'disabled': True},
        'logp': {'disabled': True},
    }


class LigandView(AuthenticatedModelView, MoleculeView):
    column_list = ('id', 'smiles', 'name', 'serial', 'logp', 'structure')
    form_columns = ('structure', 'inchikey', 'logp', 'refcode', 'serial')
    form_overrides = {'structure': fields.StringField}  # Structure should be input as SMILES
    column_formatters = {
        'structure': MoleculeView._thumbnail,
    }
    form_extra_fields = {
        'inchikey': fields.StringField(),
        'logp': fields.FloatField(),
    }
    form_widget_args = {
        #'structure': {'disabled': True},
        'inchikey': {'disabled': True},
        'logp': {'disabled': True},
    }


class CitationView(AuthenticatedModelView):
    def _string_list(self, context, model, name):
        return ', '.join(map(str, getattr(model, name)))
    column_list = ('id', 'authors', 'year')
    form_columns = ('original_reference', 'doi', 'published')
    form_exclude_columns = ('reports',)                 # Don't show report mappings
    form_overrides = {'original_reference': fields.TextAreaField}  # Allow full_reference as multi-line
    column_formatters = {
        'authors': _string_list,
    }


admin.add_view(CitationView(Citation, db.session))
admin.add_view(AggregatorView(Aggregator, db.session))
admin.add_view(AuthenticatedModelView(AggregatorReport, db.session))
admin.add_view(LigandView(Ligand, db.session))
