from fastapi import FastAPI, Request, Depends, Form, status, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from datetime import date
# Import your models and schemas
from app import models, schemas
from app.database import engine, get_db_conn
from pydantic import ValidationError

load_dotenv()  # Load environment variables from .env file
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/assets", StaticFiles(directory="templates/assets"), name="assets")
models.Base.metadata.create_all(bind=engine)
app.mount("/pdfs", StaticFiles(directory="pdfs"), name="pdfs")
# Ensure the 'pdfs' directory exists
if not os.path.exists("pdfs"):
    os.makedirs("pdfs")
    
# Define the secret key and password context
SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Add SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/gestion_fournisseur", response_class=HTMLResponse)
async def gestion_fournisseur(request: Request):
    return templates.TemplateResponse("gestion_fournisseur.html", {"request": request})

@app.get("/gestion_AO", response_class=HTMLResponse)
async def gestion_ao(request: Request):
    return templates.TemplateResponse("gestion_AO.html", {"request": request})

@app.get("/gestion_commande")
async def gestion_commande(request: Request, db: Session = Depends(get_db_conn)):
    acheteurs = db.query(models.Users).all()
    ao = db.query(models.AO).all()  # Assuming you have an AO model
    fournisseur = db.query(models.Fournisseur).all()  # Assuming you have a Fournisseur model
    return templates.TemplateResponse("gestion_commande.html", {"request": request, "users": acheteurs, "ao": ao, "fournisseur": fournisseur})

@app.get("/gestion_avenant", response_class=HTMLResponse)
async def gestion_avenant(request: Request, db: Session = Depends(get_db_conn)):
    commande = db.query(models.Commande).all()
    return templates.TemplateResponse("gestion_avenant.html", {"request": request, "commandes":commande})

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/sign_up", response_class=HTMLResponse)
async def get_sign_up(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})


@app.get("/gestion_acheteur", response_class=HTMLResponse)
async def sign_up_admin(request: Request):
    return templates.TemplateResponse("gestion_acheteur.html", {"request": request})

def get_current_user(request: Request):
    user = request.session.get("user")
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/api/fournisseur", response_model=schemas.List[schemas.Fournisseur])
async def read_fournisseurs(db: Session = Depends(get_db_conn)):
    return db.query(models.Fournisseur).all()

@app.get("/api/AO", response_model=schemas.List[schemas.AOBase])
async def get_ao(db: Session = Depends(get_db_conn)):
    aos = db.query(models.AO).all()
    return [
        {
            "id": ao.id,  # Include all required fields
            "code": ao.code,
            "name": ao.name,
            "date": ao.date.isoformat(),  # Convert date to ISO format
            "budget": ao.budget
        } for ao in aos
    ]

@app.get("/api/avenant", response_model=schemas.List[schemas.AvenantBase])
async def get_avenants(db: Session = Depends(get_db_conn)):
    try:
        avenants = db.query(models.Avenant_Commande).all()
        return [
            {
                "id": avn.id,
                "code": avn.code,
                "name": avn.name,
                "description": avn.description,
                "date": avn.date.isoformat() if isinstance(avn.date, date) else avn.date,
                "budget": avn.budget,
                "commande": schemas.CommandeResponse(
                    id=avn.commande.id,
                    code=avn.commande.code,
                    name=avn.commande.name,
                    date=avn.commande.date.isoformat() if isinstance(avn.commande.date, date) else avn.commande.date,
                    objet=avn.commande.objet,
                    frs_id=avn.commande.frs_id,
                    ao_id=avn.commande.ao_id,
                    acheteur_id=avn.commande.acheteur_id,
                    acheteur=schemas.User(
                        id=avn.commande.acheteur.id,
                        name=avn.commande.acheteur.name,
                        lastname=avn.commande.acheteur.lastname,
                        email=avn.commande.acheteur.email,
                        password=avn.commande.acheteur.password
                    ),
                    fournisseur=schemas.Fournisseur(
                        id=avn.commande.fournisseur.id,
                        name=avn.commande.fournisseur.name,
                        lastname=avn.commande.fournisseur.lastname,
                        contact=avn.commande.fournisseur.contact,
                        address=avn.commande.fournisseur.address,
                        code=avn.commande.fournisseur.code,
                        email=avn.commande.fournisseur.email
                    ),
                    AO=schemas.AOBase(
                        id=avn.commande.AO.id,
                        code=avn.commande.AO.code,
                        name=avn.commande.AO.name,
                        date=avn.commande.AO.date.isoformat() if isinstance(avn.commande.AO.date, date) else avn.commande.AO.date,
                        budget=avn.commande.AO.budget
                    ) if avn.commande.AO else None
                )
            }
            for avn in avenants
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", response_class=HTMLResponse)
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_conn)
):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    
    if not user or not pwd_context.verify(password, user.password):
        error_message = "Invalid email or password"
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})
    
    request.session["user"] = {"name": user.name, "email": user.email}
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@app.post("/sign_up")
async def post_sign_up(
    name: str = Form(...),
    lastname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_conn)
):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    hashed_password = pwd_context.hash(password)
    new_user = models.Users(name=name, lastname=lastname, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"data": new_user}

@app.post("/add_fournisseur", response_class=HTMLResponse)
async def add_fournisseur(
    request: Request,
    name: str = Form(...),
    lastname: str = Form(...),
    contact: str = Form(...),
    address: str = Form(...),
    code: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db_conn)
):
    # Check if fournisseur with the same code already exists
    existing_fournisseur_code = db.query(models.Fournisseur).filter(models.Fournisseur.code == code).first()
    
    # Check if fournisseur with the same email already exists
    existing_fournisseur_email = db.query(models.Fournisseur).filter(models.Fournisseur.email == email).first()
    
    if existing_fournisseur_code:
        return templates.TemplateResponse("gestion_fournisseur.html", {"request": request, "error": "Fournisseur with this code already exists."})
    
    if existing_fournisseur_email:
        return templates.TemplateResponse("gestion_fournisseur.html", {"request": request, "error": "Fournisseur with this email already exists."})
    
    # If no duplicates, proceed to add the new fournisseur
    new_frs = models.Fournisseur(name=name, lastname=lastname, contact=contact, address=address, code=code, email=email)
    db.add(new_frs)
    try:
        db.commit()
        db.refresh(new_frs)
    except Exception as e:
        db.rollback()
        raise e  # or handle the error accordingly
    
    return RedirectResponse(url="/gestion_fournisseur", status_code=status.HTTP_302_FOUND)


@app.post("/add_AO", response_class=HTMLResponse)
async def add_ao(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    date: str = Form(...),
    budget: float = Form(...),
    db: Session = Depends(get_db_conn)
):
    # Validate the form data using AOSchema
    try:
        ao_data = schemas.AOSchema(code=code, name=name, date=date, budget=budget)
    except ValidationError as e:
        return templates.TemplateResponse("gestion_AO.html", {"request": request, "errors": e.errors()})
    
    # Check if AO already exists
    existing_ao = db.query(models.AO).filter(models.AO.code == code).first()
    if existing_ao:
        return templates.TemplateResponse("gestion_AO.html", {"request": request, "error": "AO with this code already exists."})
    
    # Create a new AO instance
    new_ao = models.AO(code=ao_data.code, name=ao_data.name, date=ao_data.date, budget=ao_data.budget)
    db.add(new_ao)
    db.commit()
    db.refresh(new_ao)
    
    return RedirectResponse(url="/gestion_AO", status_code=status.HTTP_302_FOUND)

@app.post("/add_Avenant")
async def add_avenant(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    budget: float = Form(...),
    date: str = Form(...),
    description: str = Form(...),
    commande_id: int = Form(...),
    db: Session = Depends(get_db_conn)
):
    existing_avn = db.query(models.Avenant_Commande).filter(models.Avenant_Commande.code == code).first()
    
    if existing_avn:
        commandes = db.query(models.Commande).all()
        return templates.TemplateResponse("gestion_avenant.html", {"request": request, "error": "Avenant with this code already exists.", "commandes": commandes})
    
    new_avn = models.Avenant_Commande(
        code=code,
        name=name,
        date=date,
        budget=budget,
        description=description,
        commande_id=commande_id
    )
    db.add(new_avn)
    db.commit()
    db.refresh(new_avn)
    
    return RedirectResponse(url="/gestion_avenant", status_code=status.HTTP_302_FOUND)

@app.post("/add_commande", response_class=HTMLResponse)
async def add_commande(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    ao_id: int = Form(...),
    frs_id: int = Form(...),
    acheteur_id: int = Form(...),
    date: str = Form(...),
    objet: str = Form(...),
    commandeFiles: schemas.List[UploadFile] = File(...),
    db: Session = Depends(get_db_conn)
):
    existing_cmd = db.query(models.Commande).filter(models.Commande.code == code).first()
    
    if existing_cmd:
        return templates.TemplateResponse("gestion_commande.html", {"request": request, "error": "Commande with this code already exists."})
    
    # Save the files
    file_urls = []
    for file in commandeFiles:
        file_location = f"pdfs/{file.filename}"
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        file_urls.append(file_location)
    
    # Create and add the new commande to the database
    new_commande = models.Commande(
        code=code,
        name=name,
        ao_id=ao_id,
        frs_id=frs_id,
        acheteur_id=acheteur_id,
        date=date,
        objet=objet,
        file_urls=file_urls  # Ensure your model has a column to handle this
    )
    
    db.add(new_commande)
    db.commit()
    db.refresh(new_commande)
    
    return RedirectResponse(url="/gestion_commande", status_code=status.HTTP_303_SEE_OTHER)

@app.delete("/api/fournisseur/{fournisseur_id}", status_code=204)
async def delete_fournisseur(fournisseur_id: int, db: Session = Depends(get_db_conn)):
    fournisseur = db.query(models.Fournisseur).filter(models.Fournisseur.id == fournisseur_id).first()
    
    if fournisseur is None:
        raise HTTPException(status_code=404, detail="Fournisseur not found")
    
    db.delete(fournisseur)
    db.commit()
    return

@app.delete("/api/AO/{ao_id}", status_code=204)
async def delete_ao(ao_id: int, db: Session = Depends(get_db_conn)):
    ao = db.query(models.AO).filter(models.AO.id == ao_id).first()
    
    if ao is None:
        raise HTTPException(status_code=404, detail="AO not found")
    
    db.delete(ao)
    db.commit()
    return {"detail": "AO deleted successfully"}
    

@app.post("/add_user", response_class=RedirectResponse)
async def add_user(request: Request, name: str = Form(...), lastname: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_conn)):
    user = db.query(models.Users).filter(models.Users.email == email).first()
    
    if user:
        # Handle the case where the AO already exists
        return templates.TemplateResponse("gestion_acheteur.html", {"request": request, "error": "acheteur with this email already exists."})
    
    hashed_password = pwd_context.hash(password)
    new_user = models.Users(name=name, lastname=lastname, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/gestion_acheteur", status_code=status.HTTP_302_FOUND)


@app.get("/api/users", response_model=schemas.List[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_conn)):
    users = db.query(models.Users).offset(skip).limit(limit).all()
    return users

@app.delete("/api/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db_conn)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user

@app.get("/api/commande", response_model=schemas.List[schemas.CommandeResponse])
async def get_commandes(db: Session = Depends(get_db_conn)):
    commandes = db.query(models.Commande).all()
    response = [
        schemas.CommandeResponse(
            id=commande.id,
            code=commande.code,
            name=commande.name,
            date=commande.date.isoformat(),  # Convert date to string if needed
            objet=commande.objet,
            frs_id=commande.frs_id,
            ao_id=commande.ao_id,
            acheteur_id=commande.acheteur_id,
            acheteur=schemas.User(
                id=commande.acheteur.id,
                name=commande.acheteur.name,
                lastname=commande.acheteur.lastname,
                email=commande.acheteur.email,
                password=commande.acheteur.password
            ),
            fournisseur=schemas.Fournisseur(
                id=commande.fournisseur.id,
                name=commande.fournisseur.name,
                lastname=commande.fournisseur.lastname,
                contact=commande.fournisseur.contact,
                address=commande.fournisseur.address,
                code=commande.fournisseur.code,
                email=commande.fournisseur.email
            ),
            AO=schemas.AOBase(
                id=commande.AO.id,
                code=commande.AO.code,
                name=commande.AO.name,
                date=commande.AO.date.isoformat(),  # Convert date to string if needed
                budget=commande.AO.budget
            ) if commande.AO else None,
              file_urls=commande.file_urls or []
        )
        for commande in commandes
    ]
    return response

@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    searchType: str = Form(...),
    fournisseurName: str = Form(None),
    fournisseurCode: str = Form(None),
    commandeName: str = Form(None),
    commandeCode: str = Form(None),
    aoName: str = Form(None),
    aoCode: str = Form(None),
    objet: str = Form(None),
    db: Session = Depends(get_db_conn)
):
    results = db.query(models.Commande).options(
        joinedload(models.Commande.fournisseur),
        joinedload(models.Commande.AO)
    )

    if searchType == "fournisseur":
        if fournisseurName or fournisseurCode:
            results = results.join(models.Fournisseur).filter(
                models.Fournisseur.name.contains(fournisseurName) if fournisseurName else True,
                models.Fournisseur.code.contains(fournisseurCode) if fournisseurCode else True
            )

    elif searchType == "commande":
        if commandeName or commandeCode:
            results = results.filter(
                models.Commande.name.contains(commandeName) if commandeName else True,
                models.Commande.code.contains(commandeCode) if commandeCode else True
            )

    elif searchType == "appelOffre":
        if aoName or aoCode:
            results = results.join(models.AO).filter(
                models.AO.name.contains(aoName) if aoName else True,
                models.AO.code.contains(aoCode) if aoCode else True
            )
    elif searchType == "objet":
        if objet:
            results = results.filter(
                models.Commande.objet.contains(objet) if objet else True
            )
    results = results.all()

    return templates.TemplateResponse("show_commande.html", {"request": request, "results": results, "searchType": searchType})