from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey

DATABASE_URL = "sqlite+aiosqlite:///./botdata.db"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock = Column(Integer)
    description = Column(String)
    category = Column(String)
    image = Column(String)
    location_image = Column(String)
    location_caption = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    join_date = Column(DateTime)
    balance = Column(Float, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime)

# Add more models as needed (Deliveries, Profits, etc.)


class Profit(Base):
    __tablename__ = "profits"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String)
    product = Column(String)
    quantity = Column(Integer)
    amount = Column(Float)
    stock_id = Column(String)
    datetime = Column(DateTime)

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String)
    order_id = Column(String)
    product_name = Column(String)
    location_image = Column(String)
    location_caption = Column(String)
    stock_id = Column(String)
    delivered_at = Column(DateTime)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)