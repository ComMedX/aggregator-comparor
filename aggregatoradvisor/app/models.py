from sqlalchemy import (
    backref,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    relationship,
    String,
)
from rdkit.Chem.rdMolDescriptors import RDKFingerprint
from rdalchemy import (
    Mol,  
    Bfp,
)
from aggregateadvisor.app import (
    app,
    db,
)


Column = db.Column
Model = db.Model
Table= db.Table

    
class Aggregator(Model):
    __tablename__ = 'aggregator'

    FP_MAX_PATH = 7
    FP_NUM_BITS = 2048

    @staticmethod
    def MAKE_FINGERPRINT_FOR_MOL(mol):
        mol = getattr(mol, 'as_mol', mol)
        return RDKFingerprint(mol, maxPath=FP_MAX_PATH, fpSize=FP_NUM_BITS)

    id = Column('id', Integer, primary_key=True)
    smiles = Column('smiles', Mol, nullable=False)
    fp = Column('fp', Bfp(size=FP_NUM_BITS, method=MAKE_FINGERPRINT_FOR_MOL), nullable=False)

    __table_args__ = (
        Index('aggregator_smiles_idx', smiles, postgresql_using='gist'),
        Index('aggregator_fp_idx', fp, postgresql_using='gist'),
    )

    def __repr__(self):
        return "Aggregator(id={0!r}, smiles={1!r} fp={2!r})"\
                    .format(self.id, 
                            getattr(self.smiles, 'as_smiles', None),
                            self.fp)


class Citation(Model):
    __tablename__ = 'citation'

    id = Column('id', Integer, primary_key=True)
    
    

class ReportedAggregator(Model):
    id = Column('id', Integer, primary_key=True)
    aggregator_fk = Column('aggregator_fk', Integer, ForeignKey(Aggregator.id), index=True)
    citation_fk = Column('citation_fk', Integer, ForeignKey(Citation.id), index=True)

    concentration = Column('concentration', String, nullable=True)  # Maybe should be float, log(float)?

    def __repr__(self):
        return "ReportedAggregator(id={0!r}, aggregator_fk={1!r}, citation_fk={2!r}, concentration="{3!r})"\
                    .format(self.id,
                            self.aggregator_fk,
                            self.citation_fk,
                            self.concentration)

