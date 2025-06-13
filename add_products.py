from db import SessionLocal, Product
import asyncio
import uuid

async def add_products():
    async with SessionLocal() as session:
        products = [
            Product(
                id=str(uuid.uuid4()),
                name="Cox",
                price=100,
                stock=10,
                category="Cox",
                image="products_pics/cox.png",
                description="Best Cox product."
            ),
            Product(
                id=str(uuid.uuid4()),
                name="Klein",
                price=120,
                stock=8,
                category="Klein",
                image="products_pics/klein.png",
                description="Premium Klein."
            ),
            Product(
                id=str(uuid.uuid4()),
                name="Shrooms",
                price=90,
                stock=15,
                category="Shrooms",
                image="products_pics/shrooms.png",
                description="Fresh Shrooms."
            ),
            Product(
                id=str(uuid.uuid4()),
                name="Spliff",
                price=70,
                stock=20,
                category="Spliff",
                image="products_pics/spliff.png",
                description="Classic Spliff."
            ),
        ]
        session.add_all(products)
        await session.commit()

asyncio.run(add_products())