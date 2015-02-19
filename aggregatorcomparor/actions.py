from __future__ import absolute_import, print_function

import itertools
import sys

from rdkit.RDLogger import logger, CRITICAL

from .core import db
from . import models


def init_db():
    db.create_all()


def wipe_all_data(yes_really=False):
    models.AggregatorReport.query.delete()
    models.Citation.query.delete()
    models.Aggregator.query.delete()
    models.Ligand.query.delete()
    if yes_really == 'yes':
        db.session.commit()
    else:
        db.session.rollback()
        print("Make sure you really mean it!")


def init_aggregator_data(sources, aggregators):
    print("Loading citation sources", file=sys.stderr)
    with open(sources) as f:
        try:
            for line in f:
                citation = models.ref_line_to_citation(line)
                db.session.add(citation)
                print("\rAdding {!r}".format(citation), end='', file=sys.stderr)
        except Exception as e:
            print("\nReverting because {0!s}".format(e))
            db.session.rollback()
            raise
        else:
            db.session.commit()
            print("\nAll changes saved", file=sys.stderr)

    print("Loading aggregators and reports", file=sys.stderr)
    with open(aggregators) as f:
        try:
            idx = 0
            for idx, line in enumerate(f):
                try:
                    compound, extra = models.smiles_line_to_molecule_extra(models.Aggregator, line)
                except ValueError as e:
                    print("\nIgnoring aggregator #{0:d} because {1!s}".format(idx, e))
                    continue

                if len(extra) > 0:
                    citation_fk = int(extra[0])
                    report = models.AggregatorReport(citation_fk=citation_fk)
                    compound.reports.append(report)
                db.session.add(compound)
                print("\rAdding {!r}".format(compound), end='', file=sys.stderr)
        except Exception as e:
            print("\nReverting because {0!s}".format(e))
            db.session.rollback()
            raise
        else:
            db.session.commit()
            print("\nAll changes saved", file=sys.stderr)


def load_ligands(smiles, verbose=False):
    if not verbose:
        logger().setLevel(CRITICAL)
    print("Loading ligands", file=sys.stderr)
    with open(smiles) as f:
        try:
            numbered = enumerate(f, start=1)
            groups = _grouper(numbered, 10000, None)
            for group_idx, group in enumerate(groups, start=1):
                group = (item for item in group if item is not None)
                for idx, line in group:
                    try:
                        compound, extra = models.smiles_line_to_molecule_extra(models.Ligand, line)
                    except ValueError as e:
                        print("\nIgnoring compound #{0:d} because {1!s}".format(idx, e))
                        continue
                    else:
                        if compound.mol is None:
                            print("\nIgnoring compound #{0:d} because structure is invalid ({1!s}".format(idx, e))
                            continue
                        else:
                            db.session.add(compound)
                            print("\r(Group: {:d}) Adding {!r}".format(group_idx, compound), end='', file=sys.stderr)
                # For memory efficiency
                db.session.flush()
                db.session.expunge_all()
        except Exception as e:
            print("\nReverting because {0!s}".format(e), file=sys.stderr)
            db.session.rollback()
            raise
        else:
            db.session.commit()
            print("\nAll changes saved", file=sys.stderr)


def _grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)