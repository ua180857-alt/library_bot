from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint, select
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = "sqlite+aiosqlite:///library.db"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    author = Column(String(500), nullable=False)
    description = Column(Text)
    language = Column(String(100), default="O'zbekcha")
    cover = Column(String(500))
    pdf_file_id = Column(Text)
    audio_file_id = Column(Text)  # JSON: ["file_id1", "file_id2", ...]
    type = Column(String(20), nullable=False)  # read / audio / both
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book"),)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

CATEGORIES = [
    "Badiiy adabiyot", "Diniy va ma'naviy", "Tarix",
    "Psixologiya va shaxsiy rivojlanish", "Biznes va moliya",
    "Ilm-fan va texnologiya", "Bolalar adabiyoti",
    "Darsliklar va o'quv qo'llanmalar",
]

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        existing = set((await session.execute(select(Category.name))).scalars().all())
        for name in CATEGORIES:
            if name not in existing:
                session.add(Category(name=name))
        await session.commit()
