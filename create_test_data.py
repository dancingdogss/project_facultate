import asyncio
import uuid
from datetime import datetime
from db import SessionLocal
from db_utils import add_product, set_user_balance

async def add_test_data():
    # Sample products
    products = [
        {"name": "Cox Top", "price": 500, "stock": 510, "category": "Energy Drinks"},
        {"name": "Klein", "price": 150, "stock": 500, "category": "Mellow Drinks"},
        {"name": "Shrooms", "price": 100, "stock": 10200, "category": "Horticulture"},
        {"name": "Spliff", "price": 50, "stock": 100, "category": "Horticulture"},
        {"name": "Test", "price": 500, "stock": 20872, "category": "Test Category"}
    ]
    
    # Sample user balances
    balances = {
        "12345678": 2000,
        "87654321": 1500
    }
    
    async with SessionLocal() as session:
        # Add products
        for p in products:
            await add_product(
                session, 
                p["name"], 
                p["price"], 
                p["stock"], 
                p["category"]
            )
            print(f"Added product: {p['name']}")
            
        # Add balances
        for user_id, balance in balances.items():
            await set_user_balance(session, user_id, balance)
            print(f"Added balance for user: {user_id}")

if __name__ == "__main__":
    asyncio.run(add_test_data())