from __future__ import absolute_import

import contextlib
from cStringIO import StringIO

from rdkit import Chem as C
from rdkit.Chem import inchi as Ci
from rdkit.Chem import Draw as CD

from rdalchemy.rdalchemy import tanimoto_threshold
from flask import(
    abort,
    json,
    render_template,
    request,
    send_file,
    url_for,
)


from .core import (
    app,
    db,
)
from .models import (
    coerse_to_mol,
    mol_from_agg_id,
    mol_from_lig_id,
)


IMAGE_FORMAT_MIME_TYPES = {
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
}

SEARCH_INPUT_FORMATS = [
    ('aggregator', mol_from_agg_id),
    ('ligand', mol_from_lig_id),
    ('smiles', C.MolFromSmiles),
    ('smarts', C.MolFromSmarts),
    ('inchi', Ci.MolFromInchi),
    ('sdf', C.MolFromMolBlock),
    ('mol2', C.MolFromMol2Block),
    ('pdb', C.MolFromPDBBlock),
]


def draw(mol, format='png'):
    if format not in IMAGE_FORMAT_MIME_TYPES:
        abort(404)
    image_size = app.config.get('MOLECULE_DISPLAY_IMAGE_SIZE', (200,200))
    image = CD.MolToImage(mol, size=image_size)
    image_data = image_to_buffer(image, format)
    mime_type = IMAGE_FORMAT_MIME_TYPES.get(format)

    return send_file(image_data, mime_type)


def get_molecules_for_view(molecules, page_num, sorting=None, config=app.config):
    per_page = config.get('MOLECULES_DISPLAY_PER_PAGE', 30)
    if sorting:
        ordered = molecules.order_by(sorting)
    else:
        ordered = molecules
    paginated = ordered.paginate(page_num, per_page)
    return paginated


def image_to_buffer(image, format='PNG'):
    buf = StringIO()
    image.save(buf, format.upper())
    buf.seek(0)
    return buf


def extract_query_mol(params, formats=SEARCH_INPUT_FORMATS, onerror_fail=True):
    mol, error = None, None
    for input_format, parser in formats:
        try:
            query = params[input_format]
            mol = parser(str(query))
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
        if onerror_fail:
            abort(400)
        else:
            error = "Query parameter missing (expected one of: {}"\
                        .format(', '.join(fmt for fmt, _ in SEARCH_INPUT_FORMATS))
    return mol, query, error


def get_similarity_parameters(this_request, onerror_fail=True, **kwargs):
    default_search_cutoff = app.config.get('MOLECULE_SEARCH_TANIMOTO_CUTOFF', 0.50)
    default_result_limit = app.config.get('MOLECULE_SEARCH_RESULT_LIMIT', None)
    search_cutoff = float(this_request.args.get('similarity_threshold', default_search_cutoff))
    result_limit = this_request.args.get('max_results', default_result_limit)
    query_structure, query_input, error = extract_query_mol(this_request.args, SEARCH_INPUT_FORMATS)

    if result_limit is not None:
        result_limit = int(result_limit)

    if query_structure is not None:
        query_molecule = coerse_to_mol(query_structure)
    else:
        query_molecule = None

    if 'override_limit' in kwargs:
        result_limit = kwargs['override_limit']

    if error is not None and onerror_fail:
        abort(400)
    else:
        return {
            'cutoff': search_cutoff,
            'limit': result_limit,
            'query': query_molecule,
            'mol': query_structure,
            'raw': query_input,
            'error': error,
        }



@contextlib.contextmanager
def run_similar_molecules_query(result_type, params):
    needle = params['query']

    needle_fp = needle.bind.rdkit_fp  # Force server-side fingerprint function
    haystack = result_type.query  # Searchable Aggregator dataset
    haystack_fps = result_type.structure.rdkit_fp  # Comparable fingerprint property

    # Construct structural query sorted and limited by similarity with tanimoto scores annotated
    similar = haystack.filter(haystack_fps.similar_to(needle_fp))  # Restrict to molecules with high Tc
    similar = similar.order_by(haystack_fps.tanimoto_nearest_neighbors(needle_fp))  # Put highest Tc's first
    similar = similar.add_columns(needle_fp.tanimoto(haystack_fps))  # Annotate results with Tc

    if 'limit' in params:
        similar = similar.limit(params['limit'])

    # Run query with specified tanimoto threshold
    if 'cutoff' in params:
        with tanimoto_threshold(db.engine, params['cutoff']):
            yield similar
    else:
        yield similar



def get_similar_molecules(result_type, query_structure=None, **params):
    params.setdefault('cutoff', app.config.get('MOLECULE_SEARCH_TANIMOTO_CUTOFF', 0.50))
    params.setdefault('limit', app.config.get('MOLECULE_SEARCH_RESULT_LIMIT', 10))
    if query_structure is not None:
        params.setdefault('mol', query_structure)
    if 'mol' in params:
        params.setdefault('query', coerse_to_mol(params['mol']))
    with run_similar_molecules_query(result_type, params) as results:
        annotated = annotate_tanimoto_similarity(results)
        return annotated


def annotate_tanimoto_similarity(molecules_with_tc, attribute='tanimoto_similarity'):
    for molecule, tc in molecules_with_tc:
        setattr(molecule, attribute, tc)
        setattr(molecule, attribute+'_percentage', int(100 * tc))
        yield  molecule