from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Настройка базы данных (SQLite для примера)
DATABASE_URL = "sqlite:///./doggen.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Инициализация FastAPI приложения
app = FastAPI(
    title="DogNFT API",
    description="API для управления NFT-токенами DogNFT.",
    version="1.0.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любого домена
    allow_credentials=True,  # Разрешить отправку cookies
    allow_methods=["*"],  # Разрешить все HTTP методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Модели базы данных
class NFT(Base):
    __tablename__ = "nfts"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    dogKey = Column(String, nullable=False, unique=True)
    walletAddress = Column(String, nullable=False)
    attributes = Column(JSON, nullable=True)
    status = Column(String, default="generating")
    progress = Column(Integer, default=0)  # Progress in percentage (0-100)
    imageUrl = Column(String, nullable=True)
    contractAddress = Column(String, nullable=True)
    tokenId = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    mintedAt = Column(DateTime, nullable=True)

# Pydantic модели для валидации данных
class CheckNameRequest(BaseModel):
    name: str
    walletAddress: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CryptoDog #1",
                "walletAddress": "0x123...abc",
            }
        }

class CheckNameResponse(BaseModel):
    available: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "available": True,
                "message": "NFT name is available",
            }
        }

class CheckKeyRequest(BaseModel):
    dogKey: str
    walletAddress: str

    class Config:
        json_schema_extra = {
            "example": {
                "dogKey": "KEY_123456",
                "walletAddress": "0x123...abc",
            }
        }

class CheckKeyResponse(BaseModel):
    valid: bool
    unique: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "unique": True,
                "message": "Dog key is valid and unique",
            }
        }

class GenerateNFTRequest(BaseModel):
    name: str
    description: Optional[str] = None
    dogKey: str
    walletAddress: str
    attributes: Optional[List[dict]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CryptoDog #1",
                "description": "A unique crypto dog NFT",
                "dogKey": "KEY_123456",
                "walletAddress": "0x123...abc",
                "attributes": [
                    {"type": "Rarity", "value": "Legendary"},
                    {"type": "Level", "value": "50"},
                ],
            }
        }

class GenerateNFTResponse(BaseModel):
    id: str
    status: str
    name: str
    description: Optional[str] = None
    dogKey: str
    walletAddress: str
    contractAddress: Optional[str] = None
    tokenId: Optional[str] = None
    attributes: Optional[List[dict]] = None
    createdAt: str
    mintedAt: Optional[str] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "nft_1",
                "status": "generating",
                "name": "CryptoDog #1",
                "description": "A unique crypto dog NFT",
                "dogKey": "KEY_123456",
                "walletAddress": "0x123...abc",
                "contractAddress": None,
                "tokenId": None,
                "attributes": [
                    {"type": "Rarity", "value": "Legendary"},
                    {"type": "Level", "value": "50"},
                ],
                "createdAt": "2024-03-15T10:30:00Z",
                "mintedAt": None,
                "message": "NFT generation started",
            }
        }

class NFTStatusResponse(BaseModel):
    id: str
    status: str
    progress: int
    imageUrl: Optional[str] = None
    walletAddress: str
    contractAddress: Optional[str] = None
    tokenId: Optional[str] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "nft_1",
                "status": "ready",
                "progress": 100,
                "imageUrl": "https://example.com/nft/nft_1.png",
                "walletAddress": "0x123...abc",
                "contractAddress": None,
                "tokenId": None,
                "message": "NFT status retrieved",
            }
        }

class NFTCollectionResponse(BaseModel):
    nfts: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "nfts": [
                    {
                        "id": "nft_1",
                        "name": "CryptoDog #1",
                        "status": "ready",
                        "imageUrl": "https://example.com/nft/nft_1.png",
                        "dogKey": "KEY_123456",
                        "walletAddress": "0x123...abc",
                        "contractAddress": None,
                        "tokenId": None,
                        "attributes": [
                            {"type": "Rarity", "value": "Legendary"},
                            {"type": "Level", "value": "50"},
                        ],
                        "createdAt": "2024-03-15T10:30:00Z",
                        "mintedAt": None,
                    }
                ]
            }
        }

# Dependency для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Корневой маршрут
@app.get("/", tags=["General"])
def read_root():
    """
    Добро пожаловать в DogNFT API!

    Для просмотра документации перейдите по адресу `/docs` или `/redoc`.
    """
    return {"message": "Welcome to DogNFT API! Visit /docs for API documentation."}

# POST /api/nft/check-name
@app.post("/api/nft/check-name", response_model=CheckNameResponse, tags=["NFT Management"])
def check_name(request: CheckNameRequest, db: Session = Depends(get_db)):
    """
    Проверяет доступность имени NFT.

    - **name**: Имя NFT для проверки.
    - **walletAddress**: Адрес кошелька пользователя.
    """
    existing_nft = db.query(NFT).filter(NFT.name == request.name).first()
    if existing_nft:
        return {"available": False, "message": "NFT name is already taken"}
    return {"available": True, "message": "NFT name is available"}

# POST /api/nft/check-key
@app.post("/api/nft/check-key", response_model=CheckKeyResponse, tags=["NFT Management"])
def check_key(request: CheckKeyRequest, db: Session = Depends(get_db)):
    """
    Проверяет уникальность и валидность ключа собаки.

    - **dogKey**: Ключ собаки для проверки.
    - **walletAddress**: Адрес кошелька пользователя.
    """
    existing_key = db.query(NFT).filter(NFT.dogKey == request.dogKey).first()
    if existing_key:
        return {"valid": True, "unique": False, "message": "Dog key is valid but not unique"}
    return {"valid": True, "unique": True, "message": "Dog key is valid and unique"}

# POST /api/nft/generate
@app.post("/api/nft/generate", response_model=GenerateNFTResponse, tags=["NFT Management"])
def generate_nft(request: GenerateNFTRequest, db: Session = Depends(get_db)):
    """
    Генерирует новый NFT.

    - **name**: Имя NFT (обязательно).
    - **description**: Описание NFT (опционально).
    - **dogKey**: Уникальный ключ собаки (обязательно).
    - **walletAddress**: Адрес кошелька пользователя (обязательно).
    - **attributes**: Атрибуты NFT (опционально).
    """
    existing_key = db.query(NFT).filter(NFT.dogKey == request.dogKey).first()
    if existing_key:
        raise HTTPException(status_code=400, detail={"error": "Dog key must be unique", "code": "DUPLICATE_KEY"})

    new_nft = NFT(
        id=f"nft_{len(db.query(NFT).all()) + 1}",
        name=request.name,
        description=request.description,
        dogKey=request.dogKey,
        walletAddress=request.walletAddress,
        attributes=request.attributes,
        status="generating",
        progress=0,
    )
    db.add(new_nft)
    db.commit()
    db.refresh(new_nft)

    new_nft.progress = 50
    db.commit()

    return {
        "id": new_nft.id,
        "status": new_nft.status,
        "name": new_nft.name,
        "description": new_nft.description,
        "dogKey": new_nft.dogKey,
        "walletAddress": new_nft.walletAddress,
        "contractAddress": new_nft.contractAddress,
        "tokenId": new_nft.tokenId,
        "attributes": new_nft.attributes,
        "createdAt": new_nft.createdAt.isoformat(),
        "mintedAt": new_nft.mintedAt.isoformat() if new_nft.mintedAt else None,
        "message": "NFT generation started",
    }

# GET /api/nft/status/:id
@app.get("/api/nft/status/{id}", response_model=NFTStatusResponse, tags=["NFT Management"])
def get_nft_status(id: str, walletAddress: str = Query(...), db: Session = Depends(get_db)):
    """
    Получает текущий статус генерации NFT.

    - **id**: ID NFT для проверки.
    - **walletAddress**: Адрес кошелька пользователя (параметр запроса).
    """
    nft = db.query(NFT).filter(NFT.id == id, NFT.walletAddress == walletAddress).first()
    if not nft:
        raise HTTPException(status_code=404, detail={"error": "NFT not found", "code": "NFT_NOT_FOUND"})

    if nft.status == "generating":
        nft.progress = min(nft.progress + 25, 100)
        if nft.progress == 100:
            nft.status = "ready"
            nft.imageUrl = f"https://example.com/nft/{id}.png"
        db.commit()

    return {
        "id": nft.id,
        "status": nft.status,
        "progress": nft.progress,
        "imageUrl": nft.imageUrl,
        "walletAddress": nft.walletAddress,
        "contractAddress": nft.contractAddress,
        "tokenId": nft.tokenId,
        "message": "NFT status retrieved",
    }

# GET /api/nft/collection/:walletAddress
@app.get("/api/nft/collection/{walletAddress}", response_model=NFTCollectionResponse, tags=["NFT Management"])
def get_nft_collection(walletAddress: str, db: Session = Depends(get_db)):
    """
    Получает коллекцию NFT, принадлежащую указанному кошельку.

    - **walletAddress**: Адрес кошелька пользователя.
    """
    nfts = db.query(NFT).filter(NFT.walletAddress == walletAddress).all()
    if not nfts:
        raise HTTPException(status_code=404, detail={"error": "No NFTs found for this wallet", "code": "NO_NFTS"})

    nft_list = [
        {
            "id": nft.id,
            "name": nft.name,
            "status": nft.status,
            "imageUrl": nft.imageUrl,
            "dogKey": nft.dogKey,
            "walletAddress": nft.walletAddress,
            "contractAddress": nft.contractAddress,
            "tokenId": nft.tokenId,
            "attributes": nft.attributes,
            "createdAt": nft.createdAt.isoformat(),
            "mintedAt": nft.mintedAt.isoformat() if nft.mintedAt else None,
        }
        for nft in nfts
    ]

    return {"nfts": nft_list}
