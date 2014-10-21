from flask.ext import admin
import app
from models import (
    Aggregator,
    Citation,
    ReportedAggregator,
)


class AuthenticatedModelView(admin.ModelView):
    def is_accessible(self):
        return app.login.current_user.is_authenticated()


class AggregatorView(AuthenticatedModelView):
    # TODO: Add special rendering for Aggregators to include images & computed properties
    pass


app.admin.add_view(AggregatorView(Aggregator, app.db.session))
app.admin.add_view(AuthenticatedModelView(Citation, app.db.session))
app.admin.add_view(AuthenticatedModelView(ReportedAggregator, app.db.session))
