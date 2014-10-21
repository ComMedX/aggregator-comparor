from datetime import datetime
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Date,
)
from rdalchemy import Mol
import app


# Import Flask-SQLAlchemy objects
Column = app.db.Column
Model = app.db.Model
Table = app.db.Table
backref = app.db.backref
relationship = app.db.relationship
# or use SQLAlchemy directly
#from sqlalchemy import Column, Table
#from sqlalchemy.orm import backref, relationship
#from sqlalchemy.ext.declarative import declarative_base
#Model = declarative_base()


def to_structure(data):
    return Mol.bind_expression(data)


class Aggregator(Model):
    __tablename__ = 'aggregator'

    id = Column('id', Integer, primary_key=True)
    structure = Column('smiles', Mol, nullable=False)
    inchikey = Column('inchikey', String(27), nullable=False)
    name = Column('name', String, nullable=False, default='')
    added = Column('added', DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        # Create a GIST index for the RDKit chemical structure (sub/super structure)
        Index('aggregator_structure_idx', structure, postgresql_using='gist'),
        # Create an index on the fingerprint function, instead of explicitly
        # storing fingerprints
        Index('aggregator_fp_fn_idx', structure.rdkit_fp, postgresql_using='gist'),
        # Store a functional index of the InChI key as a unique constraint for molecules since RDKit's mol object
        # does not enforce uniqueness with stereochemistry
        Index('aggregator_inchikey_fn_idx', structure.inchikey, unique=True)
    )

    def __init__(self, **kwargs):
        raw_structure = kwargs.pop('smiles', kwargs.get('structure'))

        if 'id' not in kwargs and raw_structure is None:
            raise ValueError("Must provide a structure when creating a Aggregator without an existing ID")

        kwargs['structure'] = to_structure(raw_structure)
        super(Aggregator, self).__init__(**kwargs)

    @property
    def mwt(self):
        return self.structure.mwt

    @property
    def logp(self):
        return self.structure.logp

    @property
    def smiles(self):
        return self.structure.as_smiles

    @property
    def mol(self):
        return self.structure.as_mol

    @property
    def fp(self):
        return self.structure.rdkit_fp

    def __repr__(self):
        return "Aggregator(id={0!r}, smiles={1!r} fp={2!r})" \
            .format(self.id,
                    self.smiles,
                    self.fp)

    def __unicode__(self):
        return u"#1 < {} >".format(self.smiles)

    def __str__(self):
        return "#1 < {} >".format(self.smiles)


class Citation(Model):
    __tablename__ = 'citation'

    id = Column('id', Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    full_reference = Column('full_reference', String, nullable=False)
    short_reference = Column('short_reference', String, nullable=False)
    doi = Column('doi', String, nullable=False)
    published = Column('published', Date,    # Can be approximate, only year will/should be displayed
                       default=lambda:datetime.now().year,
                       nullable=False)

    aggregators = relationship(Aggregator,
                               viewonly=True,
                               secondary=lambda:ReportedAggregator.__table__,
                               backref=backref('citations', viewonly=True))

    @property
    def year(self):
        return self.published.year

    @property
    def doi_url(self):
        return u"http://dx.doi.org/{}".format(self.doi)

    def __repr__(self):
        return "Citation(id={0!r} doi={1!r} short_reference={2!r})" \
            .format(self.id,
                    self.doi,
                    self.short_reference)

    def __unicode__(self):
        return unicode(self.short_reference)

    def __str__(self):
        return str(self.short_reference)


class ReportedAggregator(Model):
    id = Column('id', Integer, primary_key=True)
    aggregator_fk = Column('aggregator_fk', Integer, ForeignKey(Aggregator.id), index=True, nullable=False)
    citation_fk = Column('citation_fk', Integer, ForeignKey(Citation.id), index=True, nullable=False)
    concentration = Column('concentration', String, nullable=True)  # Maybe should be float, log(float)?

    citation = relationship(Citation, backref='reports')
    aggregator = Column(Aggregator, backref='reports')

    def __repr__(self):
        return 'ReportedAggregator(id={0!r}, aggregator_fk={1!r}, citation_fk={2!r}, concentration={3!r})'\
            .format(self.id,
                    self.aggregator_fk,
                    self.citation_fk,
                    self.concentration)

    def __unicode__(self):
        return u"Aggregator #{0} < {1} > from {2}".format(self.aggregator_fk,
                                                          self.aggregator.smiles,
                                                          self.citation.short_reference)

    def __str__(self):
        return "Aggregator #{0} < {1} > from {2}".format(self.aggregator_fk,
                                                         self.aggregator.smiles,
                                                         self.citation.short_reference)
