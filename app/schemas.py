from pydantic import BaseModel, Field, constr, condecimal, validator
from typing import Optional,List
from datetime import date
import re

# Pydantic model for User
class User(BaseModel):
    id: int
    name: str
    lastname: str
    email: str
    password: str

    class Config:
        orm_mode = True

class Fournisseur(BaseModel):
    id: int
    name: str
    lastname: str
    contact: str
    address: str
    code: str
    email: str
    
    class Config:
        orm_mode = True

class AOSchema(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')  # Validate date format YYYY-MM-DD
    budget: float = Field(...)

    @validator('name')
    def validate_name(cls, value):
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
            raise ValueError('Invalid name. Only alphabetic characters and spaces are allowed.')
        return value

    @validator('code')
    def validate_code(cls, value):
        if not re.match(r'^[A-Za-z0-9]+$', value):
            raise ValueError('Invalid code. Only alphanumeric characters are allowed.')
        return value

class AOBase(BaseModel):
    id: int
    code: str
    name: str
    date: str
    budget: float

    class Config:
        orm_mode = True

class CommandeResponse(BaseModel):
    id: int
    code: str
    name: str
    date: str
    objet: str
    file_urls: List[str]
    frs_id: int
    ao_id: int 
    acheteur_id: int
    acheteur: User
    fournisseur: Fournisseur
    AO: Optional[AOBase] = None

    class Config:
        orm_mode = True

class AvenantBase(BaseModel):
    id: int | None = None 
    code: str
    name: str
    budget: float
    date: str
    description: str
    commande: CommandeResponse  

    class Config:
        orm_mode = True