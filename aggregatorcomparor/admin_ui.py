from flask import request
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext import login
from wtforms.fields import (
    TextAreaField,
    TextField,
)
from rdalchemy.rdalchemy import SmilesMolElement
from aggregatorcomparor import (
    admin,
    app,
    db,
)
from aggregatorcomparor.models import (
    Aggregator,
    Citation,
    Ligand,
    AggregatorReport,
)


# Require administrator access to admin forms (trivial but important)
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated()


class AggregatorView(AuthenticatedModelView):
    column_list = ('id', 'smiles', 'logp', 'added', 'inchikey')
    form_columns = ('structure', 'added', 'name', 'citations')
    form_exclude_columns = ('reports',)        # Don't show report mappings
    form_overrides = {'structure': TextField}  # Structure should be input as SMILES


class LigandView(AuthenticatedModelView):
    column_list = ('id', 'smiles', 'name', 'serial', 'inchikey')
    form_columns = ('structure', 'refcode', 'serial')
    form_overrides = {'structure': TextField}  # Structure should be input as SMILES


class CitationView(AuthenticatedModelView):
    column_list = ('id', 'authors', 'date')
    form_columns = ('original_reference', 'doi', 'published', 'aggregators')
    form_exclude_columns = ('reports',)                 # Don't show report mappings
    form_overrides = {'full_reference': TextAreaField}  # Allow full_reference as multi-line


#admin.add_view(CitationView(Citation, db.session))
#admin.add_view(AggregatorView(Aggregator, db.session))
#admin.add_view(AuthenticatedModelView(AggregatorReport, db.session))
#admin.add_view(LigandView(Ligand, db.session))
