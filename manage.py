#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import itertools
import os
import sys
import subprocess
from flask.ext.script import (
    Manager,
    Shell,
    Server,
)

from aggregatorcomparor.core import (
    app,
    db,
)
from aggregatorcomparor import models


manager = Manager(app)
TEST_CMD = "py.test tests"


def _add_namespace_to_context(namespace, context):
    for name, obj in namespace.__dict__.items():
        context[name] = obj
    return context


def _grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def _make_context():
    """Return context dict for a shell session so you can access
    app, db, and the User model by default.
    """
    context = {}
    _add_namespace_to_context(models, context)
    context.update(app=app, db=db)
    return context


@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main(['tests', '--verbose'])
    return exit_code


@manager.command
def init_db():
    db.create_all()


@manager.option('-y', '--yes-really', help="'yes' for I'm sure I want to clear the database")
def wipe_all_data(yes_really=False):
    models.Citation.query.delete()
    models.Aggregator.query.delete()
    models.AggregatorReport.query.delete()
    models.CsdCompound.query.delete()
    if yes_really == 'yes':
        db.session.commit()
    else:
        db.session.rollback()
        print("Make sure you really mean it!")


@manager.option('-a', '--aggregators', help='Aggregators with source id (aggpage.txt)')
@manager.option('-s', '--sources', help='Source publications with ids (aggref.txt)')
def init_aggregator_data(sources, aggregators):
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



@manager.option('smiles', help="SMILES file from CSD")
def load_csd(smiles):
    with open(smiles) as f:
        try:
            numbered = enumerate(f, start=1)
            groups = _grouper(numbered, 10000, None)
            for group_idx, group in enumerate(groups, start=1):
                for idx, line in group:
                    if line is None:
                        continue
                    try:
                        compound, extra = models.smiles_line_to_molecule_extra(models.CsdCompound, line)
                    except ValueError as e:
                        print("\nIgnoring compound #{0:d} because {1!s}".format(idx, e))
                        continue
                    else:
                        if compound.mol is None:
                            print("\nIgnoring compound #{0:d} because structure is invalid".format(idx, e))
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


manager.add_command('server', Server(port=app.config.get('PORT', 8090)))
manager.add_command('shell', Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()