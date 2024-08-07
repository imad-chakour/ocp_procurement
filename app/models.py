from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import ARRAY

Base = declarative_base()

class Commande(Base):
    __tablename__ = "commandes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)
    objet = Column(String)
    frs_id = Column(Integer, ForeignKey("fournisseur.id"))
    ao_id = Column(Integer, ForeignKey("ao.id"))
    acheteur_id = Column(Integer, ForeignKey("users.id"))
    file_urls = Column(ARRAY(String))

    # Relations
    fournisseur = relationship("Fournisseur", back_populates="commandes")
    AO = relationship("AO", back_populates="commandes")
    acheteur = relationship("Users", back_populates="commandes")
    avenants = relationship("Avenant_Commande", back_populates="commande")

class Fournisseur(Base):
    __tablename__ = 'fournisseur'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lastname = Column(String, index=True)
    contact = Column(String, index=True)
    address = Column(String, index=True)
    code = Column(String, unique=True, index=True)  # Assuming 'code' should be unique and is a string
    email = Column(String, unique=True, index=True)  # New email column
    
    # Relations
    commandes = relationship("Commande", back_populates="fournisseur")

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    
    # Relations
    commandes = relationship("Commande", back_populates="acheteur")

class AO(Base):
    __tablename__ = 'ao'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)
    budget = Column(Float)
    
    # Relations
    commandes = relationship("Commande", back_populates="AO")

class Avenant_Commande(Base):
    __tablename__ = 'avenant_commande'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    budget = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    commande_id = Column(Integer, ForeignKey('commandes.id'), nullable=False)

    commande = relationship("Commande", back_populates="avenants")
