from cStringIO import StringIO
import operator
from rdkit.Chem import (
    MolFromSmiles,
    MolFromSmarts,
)
from rdkit.Chem.inchi import MolFromInchi
from rdkit.Chem.Draw import MolToImage
from rdalchemy.rdalchemy import tanimoto_threshold
from flask import(
    abort,
    json,
    render_template,
    request,
    send_file,
    url_for,
)
from aggregatoradvisor import (
    app,
    db,
)
from aggregatoradvisor.models import (
    Aggregator,
    Citation,
    coerse_to_mol,
)

IMAGE_FORMAT_MIME_TYPES = {
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
}

SEARCH_INPUT_FORMATS = [
    ('smiles', MolFromSmiles),
    ('smarts', MolFromSmarts),
    ('inchi', MolFromInchi),
]


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', request=request)

@app.route('/images/<int:agg_id>.png')
@app.route('/images/<int:agg_id>.<format>')
def draw(agg_id, format='png'):
    if format not in IMAGE_FORMAT_MIME_TYPES:
        abort(404)

    image_size = app.config.get('AGGREGATORS_DISPLAY_IMAGE_SIZE', (200,200))
    aggregator = Aggregator.query.get_or_404(agg_id)
    image = MolToImage(aggregator.mol, size=image_size)
    image_data = image_to_buffer(image, format)
    mime_type = IMAGE_FORMAT_MIME_TYPES.get(format)

    return send_file(image_data, mime_type)


@app.route('/search')
def search():
    default_search_cutoff = app.config.get('AGGREGATOR_SEARCH_TANIMOTO_CUTOFF', 0.50)
    search_cutoff = float(request.args.get('similarity_threshold', default_search_cutoff))

    query_mol, error = extract_query_mol(request.args, SEARCH_INPUT_FORMATS)

    if error is not None:
        return error, 400

    # Bind input to the same type as aggregator structure
    query = coerse_to_mol(query_mol)
    query_fp = query.bind.rdkit_fp                  # Force server-side fingerprint function
    query_logp = round(query.logp, 3)               # Get "pretty" logp
    aggregators = Aggregator.query                  # Searchable Aggregator dataset
    aggregator_fps = Aggregator.structure.rdkit_fp  # Comparable fingerprint property
    
    # Construct structural query sorted and limited by similarity with tanimoto scores annotated
    similar = aggregators.filter(aggregator_fps.similar_to(query_fp))  # Restrict to aggregators with high Tc
    similar = similar.order_by(aggregator_fps.tanimoto_nearest_neighbors(query_fp))  # Put highest Tc's first
    similar = similar.add_columns(query_fp.tanimoto(aggregator_fps))  # Annotate results with Tc

    # Run query with specified tanimoto threshold
    with tanimoto_threshold(db.engine, search_cutoff):
        nearest_tc = similar.all()

    # Split out aggregators and Tc scores
    try:
        similar_aggregators, aggregator_tcs = zip(*nearest_tc)
    except ValueError:
        similar_aggregators, aggregator_tcs = [],[]
    aggregator_tcs = [round(tc, 2) for tc in aggregator_tcs]
    max_tc = max(aggregator_tcs + [0])  # Add dummy score in event none found
    num_similar = len(similar_aggregators)

    # Determine aggregator summary 
    if max_tc == 1.0:
        summary = "known" 
    if num_similar > 0 and query_logp > 3:
        summary = "likely"
    elif num_similar > 0:
        summary = "maybe"
    elif query_logp > 3:
        summary = "maybe"
    else:
        summary = "unlikely (but test anyways)"

    report = {
        'summary': summary,
        'logp': query_logp,
        'maxtc': max_tc,
        'num_similar': num_similar,
        'similar_smiles': [aggregator.smiles for aggregator in similar_aggregators],
    }

    return json.jsonify(**report)


@app.route('/browse', defaults={'page_num': 1})
@app.route('/browse/<int:page_num>')
def browse_aggregators(page_num=1):
    aggregators = get_aggregators_for_view(Aggregator.query, page_num, config=app.config)
    return render_template('browse_aggregators.html',
                           request=request,
                           aggregators=aggregators)


@app.route('/sources', defaults={'page_num': 1})
@app.route('/sources/<int:page_num>')
def browse_citations(page_num=1):
    per_page = app.config.get('CITATIONS_DISPLAY_PER_PAGE', 10)
    ordering = Citation.published
    paginated = Citation.query.order_by(ordering).paginate(page_num, per_page)
    return render_template('browse_citations.html', 
                           request=request,
                           citations=paginated)


@app.route('/reference/<int:cite_id>', defaults={'page_num': 1})
@app.route('/reference/<int:cite_id>/<int:page_num>')
def browse_citation_aggregators(cite_id, page_num=1):
    citation = Citation.query.get_or_404(cite_id)
    aggregators = get_aggregators_for_view(citation.aggregators, page_num, config=app.config)
    return render_template('browse_citation_aggregators.html',
                           request=request,
                           citation=citation,
                           aggregators=aggregators)


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


def extract_query_mol(params, formats):
    mol, error = None, None
    for input_format, parser in formats:
        try:
            query_input = params[input_format]
            mol = parser(str(query_input))
            if mol is None:
                raise ValueError("Failed to parse {}".format(input_format))
        except KeyError:
            pass
        except ValueError as e:
            error = "Invalid query term (reason: {})".format(str(e))
            break
        else:
            break
    else:
        error = "Query parameter missing (expected one of: {}"\
                    .format(', '.join(fmt for fmt, _ in SEARCH_INPUT_FORMATS))
    return mol, error
