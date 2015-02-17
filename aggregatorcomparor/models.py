import datetime as dt
from flask import current_app
from sqlalchemy import (
    cast,
    Column,
    Date,
    DateTime,
    extract,
    ForeignKey,
    func,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from rdalchemy import Mol
from aggregatorcomparor import db


# Import Flask-SQLAlchemy objects
Model = db.Model
backref = db.backref
relationship = db.relationship


class MoleculeMixin(object):
    structure = Column('smiles', Mol, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            # Create a GIST index for the RDKit chemical structure (sub/super structure)
            Index('{}_structure_idx'.format(cls.__tablename__),
                  cls.structure,
                  postgresql_using='gist'),
            # Create an index on the fingerprint function, instead of explicitly
            # storing fingerprints
            Index('{}_fp_fn_idx'.format(cls.__tablename__),
                  cls.structure.rdkit_fp,
                  postgresql_using='gist'),
            # Store a functional index of the InChI key as a unique constraint for molecules since RDKit's mol object
            # does not enforce uniqueness with stereochemistry
            Index('{}_inchikey_fn_idx'.format(cls.__tablename__),
                  cls.structure.inchikey),
        )

    def _normalize_kwargs_structure(self, kwargs):
        raw_structure = kwargs.pop('smiles', kwargs.get('structure'))
        if raw_structure is not None:
            kwargs['structure'] = coerse_to_mol(raw_structure)
        return kwargs

    def _smiles_line(self, name='', delimiter=' '):
        return u"{0}{1}{2}".format(self.smiles, delimiter, name).strip()

    @declared_attr
    def mwt(cls_):
        @hybrid_property
        def mwt(self):
            return self.structure.mwt
        @mwt.comparator
        def mwt(cls):
            return cls.structure.mwt
        return mwt

    @declared_attr
    def num_heavy_atoms(cls_):
        @hybrid_property
        def num_heavy_atoms(self):
            return self.structure.num_heavy_atoms

        @num_heavy_atoms.comparator
        def num_heavy_atoms(cls):
            return cls.structure.num_heavy_atoms

        return num_heavy_atoms

    @hybrid_property
    def logp(self):
        return self.structure.logp

    @logp.comparator
    def logp(cls):
        return cls.structure.logp

    @declared_attr
    def smiles(cls_):
        @hybrid_property
        def smiles(self):
            return self.structure.as_smiles

        @smiles.comparator
        def smiles(cls):
            return cls.structure

        return smiles

    @hybrid_property
    def mol(self):
        return self.structure.as_mol

    @mol.comparator
    def mol(cls):
        return cls.strucutre

    @hybrid_property
    def inchi(self):
        return self.structure.as_inchi

    @inchi.comparator
    def inchi(cls):
        return cls.structure.inchi.collate('ASCII')

    @declared_attr
    def inchikey(cls_):
        @hybrid_property
        def inchikey(self):
            return self.structure.as_inchikey

        @inchikey.comparator
        def inchikey(cls):
            return cls.structure.inchikey.collate('C')

        return inchikey

    @declared_attr
    def fp(cls_):
        @hybrid_property
        def fp(self):
            return self.structure.rdkit_fp

        @hybrid_property
        def fp(cls):
            return cls.structure.rdkit_fp

        return fp


class Aggregator(MoleculeMixin, Model):
    __tablename__ = 'aggregator'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, default='')
    structure = Column('smiles', Mol, nullable=False)
    added = Column('added', DateTime, default=dt.datetime.now, server_default=text('NOW()'), nullable=False)

    def __init__(self, **kwargs):
        raw_structure = kwargs.pop('smiles', kwargs.get('structure'))
        if raw_structure is not None:
            kwargs['structure'] = coerse_to_mol(raw_structure)
        super(Aggregator, self).__init__(**kwargs)

    def __repr__(self):
        return "<Aggregator(id={0.id!r}, mame={0.name!r}, smiles={0.smiles!r})>".format(self)

    def __unicode__(self):
        return self._smiles_line(self.name)

    def __str__(self):
        return str(unicode(self))


class Citation(Model):
    __tablename__ = 'citation'

    id = Column('id', Integer, primary_key=True)
    doi = Column('doi', String, nullable=False)
    original_reference = Column('original_reference', String, nullable=False)

    authors = Column('authors', ARRAY(String, as_tuple=True), nullable=True)
    journal = Column('journal', String, nullable=True)
    volume = Column('volume', Integer, nullable=True)
    pages = Column('pages', String, nullable=True)
    published = Column('published', Date, nullable=True)  # Approximate (year only

    aggregators = relationship(Aggregator,
                               secondary=lambda:AggregatorReport.__table__,
                               lazy='dynamic',
                               backref=backref('citations',
                                               lazy='dynamic',
                                               order_by=lambda: Citation.year))

    @hybrid_property
    def year(self):
        if self.published:
            return self.published.year
        else:
            return None

    @year.setter
    def year(self, year):
        self.published = dt.date(year, 1, 1)

    @year.comparator
    def year(cls):
        return extract('YEAR', cls.published)

    @year.expression
    def year(cls):
        return extract('YEAR', cls.published)

    @property
    def doi_url(self):
        tpl = unicode(current_app.config.get("DOI_URL_TPL", u"http://dx.doi.org/{0.doi}"))
        return tpl.format(self)

    def __repr__(self):
        return "<Citation(id={0.id!r} doi={0.doi!r}, authors={0.authors!r}, year={0.year!r})".format(self)

    def __unicode__(self):
        return unicode(self.short_reference)

    def __str__(self):
        return str(self.short_reference)


class AggregatorReport(Model):
    __tablename__ = 'reported_aggregator'

    id = Column('id', Integer, primary_key=True)
    aggregator_fk = Column('aggregator_fk', ForeignKey(Aggregator.id), index=True, nullable=False)
    citation_fk = Column('citation_fk', ForeignKey(Citation.id), index=True, nullable=False)
    concentration = Column('concentration', String, nullable=True)

    citation = relationship(Citation, 
                            uselist=False,
                            backref=backref('reports', order_by=aggregator_fk))
    aggregator = relationship(Aggregator, 
                              uselist=False,
                              backref=backref('reports', order_by=citation_fk))

    def __repr__(self):
        return '<ReportedAggregator(id={0.id!r}, '\
                                   'aggregator_fk={0.aggregator_fk!r}, '\
                                   'citation_fk={0.citation_fk!r})>'.format(self)


class Ligand(MoleculeMixin, Model):
    __tablename__ = 'csdcompound'

    id = Column('id', Integer, primary_key=True)
    refcode = Column('refcode', String, nullable=False)
    serial = Column('serial', Integer, nullable=True)
    structure = Column('smiles', Mol, nullable=True)  # Null can mean failure

    def _normalize_kwargs_name(self, kwargs):
        name = kwargs.pop('name', None)
        if not name:
            return kwargs
        if '.' in name:
            refcode, serial = name.split('.', 1)
            serial = int(serial)
        else:
            refcode = name
            serial = None
        kwargs.setdefault('refcode', refcode)
        if serial is not None:
            kwargs.setdefault('serial', serial)
        return kwargs

    def __init__(self, **kwargs):
        self._normalize_kwargs_structure(kwargs)
        self._normalize_kwargs_name(kwargs)
        super(Ligand, self).__init__(**kwargs)

    @property
    def source_database_name(self):
        return current_app.config.get("LIGAND_SOURCE_NAME", 'Original')

    @property
    def source_url(self):
        tpl = current_app.config.get("LIGAND_SOURCE_URL_TPL", '')
        return tpl.format(self)

    @hybrid_property
    def name(self):
        return u"{0.refcode}.{0.serial:d}".format(self)

    @name.comparator
    def name(cls):
        return func.concat(cls.refcode, '.', cls.serial)

    def __repr__(self):
        return "<Ligand(id={0.id!r}, refcode={0.refcode!r}, serial={0.serial!r}, smiles={0.smiles!r})>".format(
            self)

    def __unicode__(self):
        return self._smiles_line(self.name)

    def __str__(self):
        return str(unicode(self))


def coerse_to_mol(data, template=MoleculeMixin.structure):
    """ Cast input to Mol element of same type as Aggregator.structure """
    return template.type.bind_expression(data)


def smiles_line_to_molecule_extra(factory, line):
    parts = line.split(None)
    smiles, name, extra = parts[0], parts[1], parts[2:]
    compound = factory(smiles=smiles, name=name)
    return compound, extra


def ref_line_to_citation(line):
    line = line.strip()
    cite_id, doi, original_ref = line.split('\t', 2)
    citation = Citation(id=cite_id, doi=doi, original_reference=original_ref)

    authors, extra = original_ref.split('.', 1)
    authors = map(str.strip, authors.split(','))
    extra = map(str.strip, extra.split(','))
    if '(' in extra[-1]:
        pages, year = map(str.strip, extra[-1].split('(', 1))
        year = int(year.strip(')'))
        extra[-1] = pages
        citation.year = year
    if authors:
        citation.authors = authors
    if len(extra) > 0:
        citation.journal = extra[0]
    if len(extra) > 1:
        citation.volume = extra[1]
    if len(extra) > 2:
        citation.pages = extra[2]
    return citation


def mol_from_agg_id(agg_id):
    return Aggregator.query.get_or_404(agg_id).mol


def mol_from_lig_id(lig_id):
    return Ligand.query.get_or_404(lig_id).mol