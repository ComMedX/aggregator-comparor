
from rdalchemy.rdalchemy import tanimoto_threshold
from flask import(
    json,
    render_template,
    request,
)
from .core import (
    app,
    db,
)
from .models import (
    Aggregator,
    Citation,
    Ligand,
    func,
    coerse_to_mol,
)
from .helpers import (
    annotate_tanimoto_similarity,
    draw,
    extract_query_mol,
    get_molecules_for_view,
    get_similarity_parameters,
    get_similar_molecules,
    SEARCH_INPUT_FORMATS,
    run_similar_molecules_query,
)


@app.route('/')
@app.route('/index')
def index():
    return render_template('home.html', request=request)

@app.route('/aggregators/<int:agg_id>.png')
def aggregator_image(agg_id, format='png'):
    aggregator = Aggregator.query.get_or_404(agg_id)
    return draw(aggregator.mol, format=format)


@app.route('/ligands/<int:lig_id>.png')
def ligand_image(lig_id, format='png'):
    compound = Ligand.query.get_or_404(lig_id)
    return draw(compound.mol, format=format)


@app.route('/search')
def search():


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


@app.route('/aggregators/<int:agg_id>')
def aggregator_detail(agg_id):
    aggregator = Aggregator.query.get_or_404(agg_id)
    similar_ligands = list(get_similar_molecules(Ligand, aggregator.structure, limit=6))
    return render_template('aggregators/detail.html',
                           aggregator=aggregator,
                           similar_ligands=similar_ligands)


@app.route('/aggregators/', defaults={'page': 1})
@app.route('/aggregators/page:<int:page>')
def aggregator_list(page=1):
    query = Aggregator.query
    sorting = Aggregator.id
    if 'name' in request.args:
        query = query.filter(func.lower(Aggregator.name).contains(request.args['name'].lower()))
        sorting = Aggregator.name
    if request.args.get('format') == 'json':
        suggestions = [agg.name for agg in query.limit(20)]
        return json.dumps(suggestions), 'application/javascript'
    else:
        aggregators = get_molecules_for_view(query, page, sorting=sorting, config=app.config)
        return render_template('aggregators/list.html', molecules=aggregators)


@app.route('/aggregators/similar', defaults={'page': 1})
@app.route('/aggregators/similar/page:<int:page>')
def aggregators_similar_to(page=1):
    params = get_similarity_parameters(this_request=request)
    if page == 0:
        del params['limit']
    with run_similar_molecules_query(Aggregator, params) as query:
        pagination = get_molecules_for_view(query, page, sorting=None, config=app.config)
        pagination.items = annotate_tanimoto_similarity(pagination.items)
        return render_template('aggregators/similar-list.html',
                               molecules=pagination,
                               page_query_args=request.args)


@app.route('/ligands/<int:lig_id>')
def ligand_detail(lig_id):
    ligand = Ligand.query.get_or_404(lig_id)
    similar_aggregators = list(get_similar_molecules(Aggregator, ligand.structure, limit=6))
    return render_template('ligands/detail.html',
                           ligand=ligand,
                           similar_aggregators=similar_aggregators)


@app.route('/ligands/', defaults={'page': 1})
@app.route('/ligands/page:<int:page>')
def ligand_list(page=1):
    query = Ligand.query
    sorting = Ligand.id
    if 'name' in request.args:
        query = query.filter(func.lower(Ligand.refcode).contains(request.args['name'].lower()))
        sorting = Ligand.refcode
    if request.args.get('format') == 'json':
        suggestions = [lig.refcode for lig in query.limit(20)]
        return json.dumps(suggestions), 'application/javascript'
    ligands = get_molecules_for_view(query, page, sorting=sorting, config=app.config)
    return render_template('ligands/list.html', molecules=ligands)


@app.route('/ligands/similar', defaults={'page': 1})
@app.route('/ligands/similar/page:<int:page>')
def ligands_similar_to(page=1):
    params = get_similarity_parameters(this_request=request)
    if page == 0:
        del params['limit']
    with run_similar_molecules_query(Ligand, params) as query:
        pagination = get_molecules_for_view(query, page, sorting=None, config=app.config)
        pagination.items = annotate_tanimoto_similarity(pagination.items)
        return render_template('ligands/similar-list.html',
                               molecules=pagination,
                               page_query_args=request.args)


@app.route('/sources', defaults={'page_num': 1})
@app.route('/sources/page:<int:page_num>')
def browse_citations(page_num=1):
    per_page = app.config.get('CITATIONS_DISPLAY_PER_PAGE', 10)
    ordering = Citation.published
    paginated = Citation.query.order_by(ordering).paginate(page_num, per_page)
    return render_template('browse_citations.html', 
                           request=request,
                           citations=paginated)


@app.route('/reference/<int:cite_id>', defaults={'page_num': 1})
@app.route('/reference/<int:cite_id>/page:<int:page_num>')
def browse_citation_aggregators(cite_id, page_num=1):
    citation = Citation.query.get_or_404(cite_id)
    aggregators = get_molecules_for_view(citation.aggregators, page_num, config=app.config)
    return render_template('browse_citation_aggregators.html',
                           request=request,
                           citation=citation,
                           aggregators=aggregators)


# Helper functions belo