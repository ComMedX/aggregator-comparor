from cStringIO import StringIO
from rdkit.Chem.Draw import MolToImage
from flask import(
    abort,
    render_template,
    send_file,
    url_for,
)
import app
from models import (
    Aggregator,
    Citation,
)

IMAGE_FORMAT_MIME_TYPES = {
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
}


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/images/<int:agg_id>.<format>', defaults={'format': 'png'})
def draw(agg_id, format='png'):
    if format not in IMAGE_FORMAT_MIME_TYPES:
        abort(404)

    image_size = app.config.get('AGGREGATORS_DISPLAY_IMAGE_SIZE', (200,200))
    aggregator = Aggregator.query.get_or_404(agg_id)
    image = MolToImage(aggregator.mol, size=image_size)
    image_data = image_to_buffer(image, format)
    mime_type = IMAGE_FORMAT_MIME_TYPES.get(format)

    return send_file(image_data, mime_type)


@app.route('/aggregators', defaults={'page_num': 1})
@app.route('/aggregators/<int:page_num>')
def browse_aggregators(page_num=1):
    aggregator_rows = get_aggregators_for_view(Aggregator.query, page_num, config=app.config)
    return render_template('browse_aggregators.html',
                           aggregator_rows=aggregator_rows)


@app.route('/sources', defaults={'page_num': 1})
@app.route('/sources/<int:page_num>')
def browse_citations(page_num=1):
    per_page = app.config.get('CITATIONS_DISPLAY_PER_PAGE', 10)
    ordering = Citation.published
    paginated = Citation.query.order_by(ordering).paginate(page_num, per_page)
    return render_template('browse_citations.html', citations=paginated)


@app.route('/sources/<int:cite_id>', defaults={'page_num': 1})
@app.route('/sources/<int:cite_id>/<page_num>')
def browse_citation_aggregators(cite_id, page_num=1):
    citation = Citation.query.get_or_404(cite_id)
    aggregator_rows = get_aggregators_for_view(citation.aggregators, page_num, config=app.config)
    return render_template('browse_aggregators.html',
                           citation=citation,
                           aggregator_rows=aggregator_rows)


# Helper functions below


def get_aggregators_for_view(aggregators, page_num, sorting=Aggregator.id, config=app.config):
    per_page = config.get('AGGREGATORS_DISPLAY_PER_PAGE', 15)
    ordered = aggregators.order_by(sorting)
    paginated = ordered.paginate(page_num, per_page)
    return paginated


def image_to_buffer(image, format='PNG'):
    buf = StringIO()
    image.save(buf, format.upper())
    buf.seek(0)
    return buf
