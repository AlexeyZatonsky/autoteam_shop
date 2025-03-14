from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from typing import Optional
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import joinedload

from ..auth.models import Users
from ..auth.schemas import UserResponse
from ..auth.router import get_current_user

from ..products.models import Product
from .models import Cart, CartItem
from .schemas import CartItemCreate, CartItemUpdate

class CartService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_cart(self, user: UserResponse) -> Cart:
        '''Получение или создание корзины для пользователя'''
        cart = await self.session.execute(select(Cart).where(Cart.user_id == user.id))
        cart = cart.scalar_one_or_none()
        
        if cart is None:
            cart = Cart(user_id=user.id, user_tg_name=user.tg_name)
            self.session.add(cart)
            await self.session.commit()
        
        return cart


    async def add_item_to_cart(self, user: UserResponse, cart_item: CartItemCreate) -> Optional[CartItem]:
        '''Добавление товара в корзину, в случае отсутствия корзины для пользователя, создается новая корзина'''
        cart = await self.get_or_create_cart(user)
        
        item = CartItem(cart_id=cart.id, product_id=cart_item.product_id, quantity=cart_item.quantity)    
        
        product = await self.session.execute(
            select(Product)
            .where(Product.id == cart_item.product_id))
        
        if product.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Проверка на наличие товара в корзине
        existing_item = await self.session.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.id, CartItem.product_id == cart_item.product_id)
            )
        
        if existing_item.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Product already in cart")
        
        self.session.add(item)
        await self.session.commit()
        
        return item
    
    async def update_item_in_cart(self, user: UserResponse, cart_item: CartItemUpdate) -> Optional[CartItem]:
        '''Обновление количества товара в корзине'''
        cart = await self.get_or_create_cart(user)
        
        item = await self.session.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.id, CartItem.product_id == cart_item.product_id))
        item = item.scalar_one_or_none()
        
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if cart_item.quantity == 0:
            # Удаляем только конкретный товар
            await self.session.delete(item)
            await self.session.commit()
            return None
        else:
            item.quantity = cart_item.quantity
            await self.session.commit()
            return item
    
    async def delete_cart(self, user: UserResponse) -> None:
        '''Удаление корзины'''
        cart = await self.get_or_create_cart(user)
        await self.session.delete(cart)
        await self.session.commit()
        
    async def get_user_cart_with_items(self, user_id: str) -> Optional[Cart]:
        '''Получение корзины пользователя со всеми товарами'''
        cart = await self.session.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        return cart.scalar_one_or_none()
    
    async def calculate_cart_total(self, cart_id: UUID) -> Decimal:
        '''Расчет общей стоимости корзины'''
        cart = await self.session.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        cart = cart.scalar_one_or_none()
        if not cart:
            return Decimal('0')
        
        total = Decimal('0')
        for item in cart.items:
            total += item.product.price * item.quantity
        return total
    
    async def clear_cart(self, user_id: str) -> None:
        '''Очистка корзины пользователя'''
        cart = await self.get_user_cart_with_items(user_id)
        if cart:
            await self.session.delete(cart)
            await self.session.commit()
        

