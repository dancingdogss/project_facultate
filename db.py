from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
import os
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///e:/project_facultate-project-facultate-betterUI-stillstubs/botdata.db"
print("DATABASE_URL:", DATABASE_URL)

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
    location_img_count = Column(Integer, default=0)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    join_date = Column(DateTime)
    balance = Column(Float, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String)
    product_id = Column(String, ForeignKey("products.id"))
    product_name = Column(String)
    quantity = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime)
    location_photo_id = Column(String, ForeignKey("location_photos.id"), nullable=True)
    delivered_count = Column(Integer, default=0)

class LocationPhoto(Base):
    __tablename__ = "location_photos"
    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    file_id = Column(String)
    caption = Column(String)
    is_delivered = Column(Boolean, default=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)

class DeliveredPhoto(Base):
    __tablename__ = "delivered_photos"
    id = Column(String, primary_key=True, index=True)
    file_id = Column(String)
    product_id = Column(String)
    order_id = Column(String)
    delivered_at = Column(DateTime, default=datetime.utcnow)

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

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def init_db():
    await create_tables()