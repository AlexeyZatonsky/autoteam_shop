from fastapi import HTTPException
from .models import Order, OrderItem
from .schemas import OrderCreate, OrderUpdate
from ..cart.service import CartService
from .enums import OrderStatusEnum
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

class OrderService:
    def __init__(self, session, cart_service: CartService):
        self.session = session
        self.cart_service = cart_service

    async def create_order_from_cart(self, user_id: str, order_data: OrderCreate) -> Order:
        """
        Создает заказ на основе корзины пользователя
        
        Args:
            user_id: ID пользователя
            order_data: Данные для создания заказа
            
        Returns:
            Order: Созданный заказ
            
        Raises:
            HTTPException: 
                - 400: Если корзина пуста
                - 404: Если корзина не найдена
                - 500: Если произошла ошибка при создании заказа
        """
        # Получаем корзину пользователя со всеми товарами
        cart = await self.cart_service.get_user_cart_with_items(user_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        if not cart.items:
            raise HTTPException(status_code=400, detail="Корзина пуста")
        
        try:
            # Рассчитываем общую стоимость
            total_amount = await self.cart_service.calculate_cart_total(cart.id)
            
            # Создаем заказ
            order = Order(
                user_id=user_id,
                total_amount=total_amount,
                status=OrderStatusEnum.NEW,
                payment_status=order_data.payment_status,
                delivery_method=order_data.delivery_method,
                phone_number=order_data.phone_number,
                delivery_address=order_data.delivery_address,
                telegram_username=order_data.telegram_username
            )
            self.session.add(order)
            await self.session.flush()  # Получаем id заказа
            
            # Создаем элементы заказа из элементов корзины
            for cart_item in cart.items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                self.session.add(order_item)
            
            # Очищаем корзину и сохраняем заказ
            await self.cart_service.clear_cart(user_id)
            await self.session.commit()
            
            # Обновляем объект заказа, чтобы получить все связанные данные
            await self.session.refresh(order)
            return order
            
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при создании заказа: {str(e)}"
            )

    async def get_user_orders(self, user_id: str, skip: int = 0, limit: int = 10):
        """
        Получает список заказов пользователя
        
        Args:
            user_id: ID пользователя
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_order_with_items(self, order_id: UUID):
        """
        Получает заказ со всеми его товарами
        
        Args:
            order_id: ID заказа
            
        Returns:
            Order: Заказ с товарами или None, если заказ не найден
        """
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(joinedload(Order.items))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update_order(self, order_id: UUID, order_data: OrderUpdate):
        """
        Обновляет информацию о заказе
        
        Args:
            order_id: ID заказа
            order_data: Новые данные заказа
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            HTTPException: Если заказ не найден
        """
        order = await self.get_order_with_items(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Обновляем поля заказа
        for key, value in order_data.model_dump(exclude_unset=True).items():
            setattr(order, key, value)
        
        await self.session.commit()
        await self.session.refresh(order)
        return order
