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
from aggregatoradvisor import (
    app,
    db,
)


# Import Flask-SQLAlchemy objects
Column = db.Column
Model = db.Model
Table = db.Table
backref = db.backref
relationship = db.relationship
# or use SQLAlchemy directly
#from sqlalchemy import Column, Table
#from sqlalchemy.orm import backref, relationship
#from sqlalchemy.ext.declarative import declarative_base
#Model = declarative_base()


class Aggregator(Model):
    __tablename__ = 'aggregator'

    id = Column('id', Integer, primary_key=True)
    structure = Column('smiles', Mol, nullable=False)
    name = Column('name', String, default='')
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
        if raw_structure is not None:
            kwargs['structure'] = coerse_to_mol(raw_struture)
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
    def inchi(self):
        return self.structure.as_inchi

    @property
    def inchikey(self):
        return self.structure.as_inchikey

    @property
    def fp(self):
        return self.structure.rdkit_fp

    def __repr__(self):
        return "Aggregator(id={0!r}, smiles={1!r} name={2!r})" \
            .format(self.id,
                    self.smiles,
                    self.name)

    def __unicode__(self):
        return u"#{0} < {1} >".format(self.id, self.smiles)

    def __str__(self):
        return "#{0} < {1} >".format(self.id, self.smiles)


class Citation(Model):
    __tablename__ = 'citation'

    id = Column('id', Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    full_reference = Column('full_reference', String, nullable=False)
    short_reference = Column('short_reference', String, nullable=False)
    doi = Column('doi', String, nullable=False)
    published = Column('published', Date,    # Can be approximate, only year will/should be displayed
                       default=lambda:datetime.now(),
                       nullable=False)

    aggregators = relationship(Aggregator,
                               secondary=lambda:ReportedAggregator.__table__,
                               lazy='dynamic',
                               backref=backref('citations',  
                                               lazy='dynamic'))

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
    __tablename__ = 'reported_aggregator'

    id = Column('id', Integer, primary_key=True)
    aggregator_fk = Column('aggregator_fk', Integer, ForeignKey(Aggregator.id), index=True, nullable=False)
    citation_fk = Column('citation_fk', Integer, ForeignKey(Citation.id), index=True, nullable=False)
    concentration = Column('concentration', String, default=u"10\u03BCM", nullable=True)

    citation = relationship(Citation, 
                            uselist=False,
                            backref=backref('reports', viewonly=True))
    aggregator = relationship(Aggregator, 
                              uselist=False,
                              backref=backref('reports', viewonly=True))

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


def coerse_to_mol(data, template=Aggregator.structure):
    """ Cast input to Mol element of same type as Aggregator.structure """
    return template.type.bind_expression(data)
