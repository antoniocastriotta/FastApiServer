from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import List
import logging
import random

# Inizializza l'app FastAPI
app = FastAPI()

# Configura il logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configura l'URL del database 
DATABASE_URL = "mysql://admin:P47#$53PNde@mydb.czqucuuf76q6.eu-central-1.rds.amazonaws.com/Pazientidatabase"  

# Configurazione del motore del database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dichiarazione della base per i modelli SQLAlchemy
Base = declarative_base()

# Definizione del modello per la tabella dei pazienti
class Paziente(Base):
    __tablename__ = "pazienti"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), index=True)
    cognome = Column(String(50), index=True)
    data_nascita = Column(String(20))
    codice_fiscale = Column(String(16), unique=True)
    patologia = Column(String(100))
    sesso = Column(String(10))
    id_medico = Column(Integer, ForeignKey("medici.id"))

    medico = relationship("Medico", back_populates="pazienti")

    acquisizioni = relationship("Acquisizione", back_populates="paziente")

# Definizione del modello per la tabella delle acquisizioni
class Acquisizione(Base):
    __tablename__ = "acquisizioni"
    acquisizione_id = Column(Integer, primary_key=True, index=True)
    id_paziente = Column(Integer, ForeignKey("pazienti.id"))
    hb_value = Column(String(50))
    acquisition_date = Column(String(20))
    acquisition_uri = Column(String(255))
    tipologia = Column(String(255))

    paziente = relationship("Paziente", back_populates="acquisizioni")

# Definizione del modello per la tabella dei medici
class Medico(Base):
    __tablename__ = "medici"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))

    pazienti = relationship("Paziente", back_populates="medico")

# Crea le tabelle nel database
Base.metadata.create_all(bind=engine)

# Modello Pydantic per il DTO del Paziente con ID
class PazienteDtoWithId(BaseModel):
    id: int
    nome: str
    cognome: str
    data_nascita: str
    codice_fiscale: str
    patologia: str
    sesso: str

# Modello Pydantic per il DTO del Paziente 
class PazienteDto(BaseModel):
    nome: str
    cognome: str
    data_nascita: str
    codice_fiscale: str
    patologia: str
    sesso: str

# Modello Pydantic per il DTO dell'Acquisizione
class AcquisizioneDto(BaseModel):
    hb_value: str
    acquisition_date: str
    acquisition_uri: str
    tipologia: str

# Modello Pydantic per il DTO del Medico
class MedicoDto(BaseModel):
    username: str
    password: str

# Modello Pydantic per il DTO dell'Acquisizione con ID
class AcquisizioneDtoWithId(AcquisizioneDto):
    acquisizione_id: int
    hb_value: str
    acquisition_date: str
    acquisition_uri: str
    tipologia: str

# Funzione di dipendenza per ottenere la sessione del database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Implementazione delle richieste
@app.post("/salva_paziente/{medicoId}")
def salva_paziente(medicoId: int, pazienteDto: PazienteDto, db: Session = Depends(get_db)):
    # Effettua la logica per salvare il paziente nel database con l'ID del medico
    nuovo_paziente = Paziente(id_medico=medicoId, **pazienteDto.dict())
    db.add(nuovo_paziente)
    db.commit()
    db.refresh(nuovo_paziente)

    return {"message": "Paziente salvato con successo"}

# Implementazione della richiesta per ottenere la lista dei pazienti di un medico
@app.get("/get_pazienti_by_medico/{medicoId}", response_model=List[PazienteDtoWithId])
def get_pazienti_by_medico(medicoId: int, db: Session = Depends(get_db)):
    pazienti = db.query(Paziente).filter(Paziente.id_medico == medicoId).all()

    pazienti_dto = [
        PazienteDtoWithId(
            id=paziente.id,
            nome=paziente.nome,
            cognome=paziente.cognome,
            data_nascita=paziente.data_nascita,
            codice_fiscale=paziente.codice_fiscale,
            patologia=paziente.patologia,
            sesso=paziente.sesso
        ) for paziente in pazienti
    ]

    return pazienti_dto

# Implementazione della richiesta di salvataggio di un'acquisizione
@app.post("/salva_acquisizione/{pazienteId}")
def salva_acquisizione(pazienteId: int, acquisizioneDto: AcquisizioneDto, db: Session = Depends(get_db)):
    # Verifica se il paziente esiste nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()
    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Logica per salvare l'acquisizione nel database
    nuova_acquisizione = Acquisizione(id_paziente=pazienteId, **acquisizioneDto.dict())
    db.add(nuova_acquisizione)
    db.commit()
    db.refresh(nuova_acquisizione)

    return {"message": "Acquisizione salvata con successo"}

# Implementazione della richiesta per ottenere i dati di un paziente
@app.get("/get_paziente/{pazienteId}", response_model=PazienteDto)
def get_paziente(pazienteId: int, db: Session = Depends(get_db)):
    # Cerca il paziente nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Converte il modello SQLAlchemy in DTO Pydantic per la risposta API
    paziente_dto = PazienteDto(
        nome=paziente.nome,
        cognome=paziente.cognome,
        data_nascita=paziente.data_nascita,
        codice_fiscale=paziente.codice_fiscale,
        patologia=paziente.patologia,
        sesso=paziente.sesso
    )

    return paziente_dto

# Implementazione della richiesta per aggiornare i dati di un paziente
@app.put("/update_paziente/{pazienteId}")
def update_paziente(pazienteId: int, pazienteDto: PazienteDto, db: Session = Depends(get_db)):
    # Cerca il paziente nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Aggiorna i dati del paziente con quelli ricevuti dal client
    paziente.nome = pazienteDto.nome
    paziente.cognome = pazienteDto.cognome
    paziente.data_nascita = pazienteDto.data_nascita
    paziente.codice_fiscale = pazienteDto.codice_fiscale
    paziente.patologia = pazienteDto.patologia
    paziente.sesso = pazienteDto.sesso

    db.commit()

    return {"message": "Dati del paziente aggiornati con successo"}

# Implementazione della richiesta per ottenere le acquisizioni di un paziente
@app.get("/get_acquisizioni/{pazienteId}", response_model=List[AcquisizioneDtoWithId])
def get_acquisizioni_by_paziente(pazienteId: int, db: Session = Depends(get_db)):
    # Cerca il paziente nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Ottieni le acquisizioni del paziente
    acquisizioni = paziente.acquisizioni

    # Converti le acquisizioni in formato DTO con ID
    acquisizioni_dto = [
        AcquisizioneDtoWithId(
            acquisizione_id=acq.acquisizione_id,
            hb_value=acq.hb_value,
            acquisition_date=acq.acquisition_date,
            acquisition_uri=acq.acquisition_uri
        ) for acq in acquisizioni
    ]

    return acquisizioni_dto

# Implementazione della richiesta per cancellare un paziente
@app.delete("/delete_paziente/{pazienteId}")
def delete_paziente(pazienteId: int, db: Session = Depends(get_db)):
    # Cerca il paziente nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Elimina tutte le acquisizioni associate al paziente
    db.query(Acquisizione).filter(Acquisizione.id_paziente == pazienteId).delete()

    # Rimuovi il paziente e commit
    db.delete(paziente)
    db.commit()

    return {"message": "Paziente e relative acquisizioni eliminate con successo"}

# Implementazione della richiesta per ottenere il valore di hb
@app.get("/get_hb_value")
def get_hb_value():
    # Genera un valore di hb randomico nel range da 8 a 17
    hb_value = round(random.uniform(8, 17), 1)
    return str(hb_value)

# Implementazione della richiesta per ottenere il numero totale di acquisizioni per un paziente
@app.get("/get_total_acquisizioni/{pazienteId}")
def get_total_acquisizioni(pazienteId: int, db: Session = Depends(get_db)):
    # Cerca il paziente nel database
    paziente = db.query(Paziente).filter(Paziente.id == pazienteId).first()

    if not paziente:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Conta il numero totale di acquisizioni per il paziente
    total_acquisizioni = db.query(Acquisizione).filter(Acquisizione.id_paziente == pazienteId).count()

    return total_acquisizioni

# Implementazione della richiesta di registrazione per il medico
@app.post("/registra_medico")
def registra_medico(medicoDto: MedicoDto, db: Session = Depends(get_db)):
    # Verifica se esiste già un medico con lo stesso username
    existing_medico = db.query(Medico).filter(Medico.username == medicoDto.username).first()
    if existing_medico:
        raise HTTPException(status_code=400, detail="Username già in uso")

    # Crea un nuovo medico nel database
    nuovo_medico = Medico(**medicoDto.dict())
    db.add(nuovo_medico)
    db.commit()
    db.refresh(nuovo_medico)

    return {"message": "Medico registrato con successo"}

# Implementazione della richiesta di login per il medico
@app.post("/login_medico")
def login_medico(medicoDto: MedicoDto, db: Session = Depends(get_db)):
    # Cerca il medico nel database
    medico = db.query(Medico).filter(
        Medico.username == medicoDto.username,
        Medico.password == medicoDto.password
    ).first()

    if not medico:
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    # Ritorna l'ID del medico
    return medico.id
