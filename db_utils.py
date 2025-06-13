from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import User, Delivery, Product, Order, Profit, LocationPhoto, DeliveredPhoto
import uuid
from sqlalchemy import update as sql_update
from datetime import datetime

 ## User Management
async def get_user(session: AsyncSession, user_id: str):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user_if_not_exists(session, user_id, join_date, balance):
    user = await get_user(session, user_id)
    if not user:
        user = User(id=user_id, join_date=join_date, balance=balance)
        session.add(user)
        await session.commit()
    return user



# Order Management

async def add_order(session, user_id, product_id, product_name, quantity, status, created_at):
    order = Order(
        id=str(uuid.uuid4()),
        user_id=user_id,
        product_id=product_id,
        product_name=product_name,
        quantity=quantity,
        status=status,
        created_at=created_at
    )
    session.add(order)
    await session.commit()
    return order

async def get_order_by_id(session, order_id):
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()

async def get_orders_by_user(session, user_id):
    result = await session.execute(select(Order).where(Order.user_id == user_id))
    return result.scalars().all()

async def get_order_by_id(session, order_id):
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_orders(session, limit=30):
    result = await session.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
    return result.scalars().all()

async def get_user_orders_count(session, user_id):
    result = await session.execute(select(Order).where(Order.user_id == user_id))
    return len(result.scalars().all())


async def get_order_by_id(session, order_id):
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()



async def update_order_status(session, order_id, new_status):
    order = await get_order_by_id(session, order_id)
    if not order:
        return None
    if order.status == "completed":
        return "completed"
    order.status = new_status
    await session.commit()
    return order



# Delivery Management

async def get_all_deliveries(session):
    result = await session.execute(select(Delivery))
    return result.scalars().all()

async def remove_delivery(session, delivery_id):
    result = await session.execute(select(Delivery).where(Delivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    if delivery:
        await session.delete(delivery)
        await session.commit()
        return True
    return False

async def get_delivery_by_id(session, delivery_id):
    result = await session.execute(select(Delivery).where(Delivery.id == delivery_id))
    return result.scalar_one_or_none()

async def get_delivered_location_photos(session):
    result = await session.execute(
        select(LocationPhoto).where(LocationPhoto.is_delivered == True)
    )
    return result.scalars().all()

async def get_available_location_photos(session):
    result = await session.execute(
        select(LocationPhoto).where(LocationPhoto.is_delivered == False)
    )
    return result.scalars().all()
async def archive_delivered_photo(session, photo, order_id):
    delivered = DeliveredPhoto(
        id=str(uuid.uuid4()),
        file_id=photo.file_id,
        product_id=photo.product_id,
        order_id=order_id,
        delivered_at=datetime.utcnow()
    )
    session.add(delivered)
    await session.commit()




# Product Management

async def add_product(session, name, price, stock, category):
    new_product = Product(
        id=str(uuid.uuid4()),
        name=name,
        price=int(price),
        stock=int(stock),
        category=category,
        image="",
        description=""
    )
    session.add(new_product)
    await session.commit()
    return new_product

async def add_location_photo(session, product_id, file_id, caption=""):
    photo = LocationPhoto(
        id=str(uuid.uuid4()),
        product_id=product_id,
        file_id=file_id,
        caption=caption,
        is_delivered=False
    )
    session.add(photo)
    await session.commit()
    return photo


async def get_unused_location_photo(session, product_id):
    result = await session.execute(
        select(LocationPhoto).where(
            LocationPhoto.product_id == product_id,
            LocationPhoto.is_delivered == False
        ).limit(1)
    )
    return result.scalar_one_or_none()

async def mark_location_photo_delivered(session, photo_id, order_id):
    result = await session.execute(select(LocationPhoto).where(LocationPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if photo:
        photo.is_delivered = True
        photo.order_id = order_id
        await session.commit()

async def get_product(session: AsyncSession, product_id: str):
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_product_by_name(session, name):
    result = await session.execute(select(Product).where(Product.name == name))
    return result.scalar_one_or_none()


async def get_products_by_category(session, category):
    result = await session.execute(select(Product).where(Product.category == category))
    return result.scalars().all() 

async def get_all_products(session):
    result = await session.execute(select(Product))
    return result.scalars().all()


async def search_products(session, text):
    result = await session.execute(select(Product).where(Product.name.ilike(f"%{text}%")))
    return result.scalars().all()

async def update_product_stock(session, product_id, new_stock):
    product = await session.execute(select(Product).where(Product.id == product_id))
    product = product.scalar_one_or_none()
    if product:
        product.stock = new_stock
        await session.commit()
    return product

async def set_product_stock(session: AsyncSession, product_id: str, stock: int):
    product = await get_product(session, product_id)
    if product:
        product.stock = stock
    else:
        product = Product(id=product_id, stock=stock)
        session.add(product)
    await session.commit()
    return product


async def remove_product(session, product_id):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        await session.delete(product)
        await session.commit()
        return True
    return False

async def edit_product(session, product_id, field, new_value):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return False
    if field in ["price", "stock"]:
        setattr(product, field, int(new_value))
    elif hasattr(product, field):
        setattr(product, field, new_value)
    else:
        return False
    await session.commit()
    return True

async def get_all_products(session):
    result = await session.execute(select(Product))
    return result.scalars().all()





# Profit Management

async def add_profit(session, user_id, product, quantity, amount, stock_id, dt):
    profit = Profit(
        id=str(uuid.uuid4()),
        user_id=user_id,
        product=product,
        quantity=quantity,
        amount=amount,
        stock_id=stock_id,
        datetime=dt
    )
    session.add(profit)
    await session.commit()
    return profit

async def get_profits(session, limit=30):
    result = await session.execute(select(Profit).order_by(Profit.datetime.desc()).limit(limit))
    return result.scalars().all()

async def get_all_profits(session):
    result = await session.execute(select(Profit))
    return result.scalars().all()

async def get_all_users(session):
    result = await session.execute(select(User))
    return result.scalars().all()

async def get_top_users(session, limit=10):
    result = await session.execute(select(User).order_by(User.balance.desc()).limit(limit))
    return result.scalars().all()

async def get_all_orders(session):
    result = await session.execute(select(Order))
    return result.scalars().all()

async def set_user_balance(session, user_id, balance):
    from db_utils import get_user
    user = await get_user(session, user_id)
    if user:
        user.balance = balance
    else:
        from db import User
        user = User(id=user_id, balance=balance)
        session.add(user)
    await session.commit()
    return user

async def add_user_balance(session, user_id, amount):
    from db_utils import get_user
    user = await get_user(session, user_id)
    if user:
        user.balance += amount
    else:
        from db import User
        user = User(id=user_id, balance=amount)
        session.add(user)
    await session.commit()
    return user

async def archive_delivered_photo(session, photo, order_id):
    delivered = DeliveredPhoto(
        id=str(uuid.uuid4()),
        file_id=photo.file_id,
        product_id=photo.product_id,
        order_id=order_id,
        delivered_at=datetime.utcnow()
    )
    session.add(delivered)
    await session.commit()