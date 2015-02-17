#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from flask.ext.script import (
    Manager,
    Shell,
    Server,
)

from aggregatorcomparor import (
    actions,
    app,
    db,
    models,
)


manager = Manager(app)
TEST_CMD = "py.test tests"


def _add_namespace_to_context(namespace, context):
    for name, obj in namespace.__dict__.items():
        context[name] = obj
    return context


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
def init_db(*args, **kwargs):
    actions.init_db(*args, **kwargs)


@manager.option('-y', '--yes-really', help="'yes' for I'm sure I want to clear the database")
def wipe_all_data(*args, **kwargs):
    actions.wipe_all_data(*args, **kwargs)


@manager.option('-a', '--aggregators', help='Aggregators with source id (aggpage.txt)')
@manager.option('-s', '--sources', help='Source publications with ids (aggref.txt)')
def init_aggregator_data(*args, **kwargs):
    actions.init_aggregator_data(*args, **kwargs)


@manager.option('smiles', help="SMILES file from CSD")
def load_ligands(*args, **kwargs):
    actions.load_ligands(*args, **kwargs)


manager.add_command('server', Server(port=app.config.get('PORT', 8090), host='0.0.0.0'))
manager.add_command('shell', Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()
