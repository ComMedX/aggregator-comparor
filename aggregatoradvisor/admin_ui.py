from flask import request
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext import login
from wtforms.fields import (
    TextAreaField,
    TextField,
)
from rdalchemy.rdalchemy import SmilesMolElement
from aggregatoradvisor import (
    admin,
    app,
    db,
)
from aggregatoradvisor.models import (
    Aggregator,
    Citation,
    ReportedAggregator,
)


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated()


class AggregatorView(AuthenticatedModelView):
    column_list = ('id', 'smiles', 'logp', 'added', 'name')

    form_columns = ('structure', 'added', 'name', 'citations')
    #form_columns = ('structure', 'inchikey', 'added', 'name', 'citations')
    #form_extra_columns = ('inchikey',)
    form_exclude_columns = ('reports',)
    form_overrides = {'structure': TextField}


class CitationView(AuthenticatedModelView):
    column_list = ('id', 'short_reference', 'title')
    form_columns = ('title', 'short_reference', 'full_reference', 'doi', 'published', 'aggregators')
    form_exclude_columns = ('reports',)
    form_overrides = {'full_refrence': TextAreaField}


admin.add_view(AggregatorView(Aggregator, db.session))
admin.add_view(CitationView(Citation, db.session))
admin.add_view(AuthenticatedModelView(ReportedAggregator, db.session))
