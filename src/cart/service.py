from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
import uuid

from src.cart.models import Cart, CartItem
from src.cart.schemas import CartCreate, CartItemCreate, CartItemUpdate
from src.products.models import Product


class CartService:
    """Сервис для работы с корзиной"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_cart(self, user_id: str) -> Cart:
        """Получает активную корзину пользователя или создает новую"""
        # Ищем активную корзину пользователя
        query = select(Cart).where(
            Cart.user_id == user_id,
            Cart.is_active == True
        )
        result = await self.session.execute(query)
        cart = result.scalars().first()
        
        # Если корзина не найдена, создаем новую
        if not cart:
            cart = Cart(user_id=user_id)
            self.session.add(cart)
            await self.session.commit()
            await self.session.refresh(cart)
        
        return cart
    
    async def get_cart_with_items(self, cart_id: Union[str, uuid.UUID]) -> Optional[Cart]:
        """Получает корзину с элементами"""
        query = select(Cart).where(Cart.id == cart_id).options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_user_cart_with_items(self, user_id: str) -> Optional[Cart]:
        """Получает активную корзину пользователя с элементами"""
        query = select(Cart).where(
            Cart.user_id == user_id,
            Cart.is_active == True
        ).options(
            joinedload(Cart.items).joinedload(CartItem.product)
        )
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def add_item_to_cart(self, user_id: str, item_data: CartItemCreate) -> Optional[CartItem]:
        """Добавляет товар в корзину"""
        # Получаем или создаем корзину
        cart = await self.get_or_create_cart(user_id)
        
        # Проверяем существование продукта
        product_query = select(Product).where(Product.id == item_data.product_id)
        product_result = await self.session.execute(product_query)
        product = product_result.scalars().first()
        
        if not product:
            return None
        
        # Проверяем, есть ли уже такой товар в корзине
        item_query = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id
        )
        item_result = await self.session.execute(item_query)
        existing_item = item_result.scalars().first()
        
        if existing_item:
            # Если товар уже есть, увеличиваем количество
            existing_item.quantity += item_data.quantity
            await self.session.commit()
            await self.session.refresh(existing_item)
            return existing_item
        else:
            # Если товара нет, создаем новый элемент корзины
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price_at_add=float(product.price)
            )
            self.session.add(cart_item)
            await self.session.commit()
            await self.session.refresh(cart_item)
            return cart_item
    
    async def update_cart_item(self, user_id: str, item_id: Union[str, uuid.UUID], 
                              item_data: CartItemUpdate) -> Optional[CartItem]:
        """Обновляет элемент корзины"""
        # Получаем активную корзину пользователя
        cart = await self.get_or_create_cart(user_id)
        
        # Проверяем, есть ли такой элемент в корзине
        item_query = select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
        item_result = await self.session.execute(item_query)
        cart_item = item_result.scalars().first()
        
        if not cart_item:
            return None
        
        # Обновляем количество
        if item_data.quantity is not None:
            cart_item.quantity = item_data.quantity
        
        await self.session.commit()
        await self.session.refresh(cart_item)
        return cart_item
    
    async def remove_cart_item(self, user_id: str, item_id: Union[str, uuid.UUID]) -> bool:
        """Удаляет элемент из корзины"""
        # Получаем активную корзину пользователя
        cart = await self.get_or_create_cart(user_id)
        
        # Удаляем элемент
        delete_query = delete(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
        result = await self.session.execute(delete_query)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def clear_cart(self, user_id: str) -> bool:
        """Очищает корзину пользователя"""
        # Получаем активную корзину пользователя
        cart = await self.get_or_create_cart(user_id)
        
        # Удаляем все элементы
        delete_query = delete(CartItem).where(CartItem.cart_id == cart.id)
        await self.session.execute(delete_query)
        await self.session.commit()
        
        return True
    
    async def calculate_cart_total(self, cart_id: Union[str, uuid.UUID]) -> float:
        """Рассчитывает общую стоимость корзины"""
        # Получаем все элементы корзины
        query = select(CartItem).where(CartItem.cart_id == cart_id)
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        # Рассчитываем общую стоимость
        total = sum(item.price_at_add * item.quantity for item in items)
        return total
    
    async def get_cart_items_count(self, user_id: str) -> int:
        """Получает количество товаров в корзине пользователя"""
        cart = await self.get_or_create_cart(user_id)
        
        # Получаем все элементы корзины
        query = select(CartItem).where(CartItem.cart_id == cart.id)
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        # Считаем общее количество товаров
        return sum(item.quantity for item in items)
    
    async def merge_guest_cart(self, guest_user_id: str, authenticated_user_id: str) -> Cart:
        """Объединяет корзину гостя с корзиной авторизованного пользователя"""
        # Получаем корзины
        guest_cart = await self.get_user_cart_with_items(guest_user_id)
        auth_cart = await self.get_or_create_cart(authenticated_user_id)
        
        if not guest_cart or not guest_cart.items:
            return auth_cart
        
        # Переносим товары из гостевой корзины в корзину авторизованного пользователя
        for guest_item in guest_cart.items:
            # Проверяем, есть ли такой товар в корзине авторизованного пользователя
            item_query = select(CartItem).where(
                CartItem.cart_id == auth_cart.id,
                CartItem.product_id == guest_item.product_id
            )
            item_result = await self.session.execute(item_query)
            existing_item = item_result.scalars().first()
            
            if existing_item:
                # Если товар уже есть, увеличиваем количество
                existing_item.quantity += guest_item.quantity
            else:
                # Если товара нет, создаем новый элемент корзины
                new_item = CartItem(
                    cart_id=auth_cart.id,
                    product_id=guest_item.product_id,
                    quantity=guest_item.quantity,
                    price_at_add=guest_item.price_at_add
                )
                self.session.add(new_item)
        
        # Очищаем гостевую корзину
        await self.clear_cart(guest_user_id)
        
        # Сохраняем изменения
        await self.session.commit()
        
        # Возвращаем обновленную корзину
        return await self.get_user_cart_with_items(authenticated_user_id)
