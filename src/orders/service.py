from fastapi import HTTPException
from .models import Order, OrderItem
from .schemas import OrderCreate, OrderUpdate
from ..cart.service import CartService
from .enums import OrderStatusEnum, PaymentStatusEnum, DeliveryMethodEnum
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID
from decimal import Decimal
from ..auth.schemas import UserResponse
from ..auth.models import Users

class OrderService:
    def __init__(self, session, cart_service: CartService):
        self.session = session
        self.cart_service = cart_service

    async def create_order_from_cart(self, user: UserResponse, order_data: OrderCreate) -> Order:
        """
        Создает заказ на основе корзины пользователя
        
        Args:
            user: Объект пользователя
            order_data: Данные для создания заказа
            
        Returns:
            Order: Созданный заказ
            
        Raises:
            HTTPException: 
                - 400: Если корзина пуста
                - 404: Если корзина не найдена
                - 500: Если произошла ошибка при создании заказа
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Начало создания заказа для пользователя {user.id}")
        
        try:
            # Получаем корзину пользователя со всеми товарами
            cart = await self.cart_service.get_or_create_cart(user)
            if not cart:
                raise HTTPException(status_code=404, detail="Корзина не найдена")
            
            # Проверяем наличие товаров в корзине
            cart_items = getattr(cart, 'items', [])
            if not cart_items or len(cart_items) == 0:
                raise HTTPException(status_code=400, detail="Корзина пуста")
            
            logger.info(f"Найдено {len(cart_items)} товаров в корзине")
            
            # Рассчитываем общую стоимость
            total_amount = await self.cart_service.calculate_cart_total(cart.id)
            logger.info(f"Общая стоимость заказа: {total_amount}")
            
            
            # Проверяем наличие обязательных данных
            phone_number = user.phone
            delivery_address = user.default_delivery_address
            
            if not phone_number:
                raise HTTPException(status_code=400, detail="Укажите номер телефона в профиле")
            
            # Начинаем транзакцию
            async with self.session.begin_nested():
                # Создаем заказ
                order = Order(
                    user_id=user.id,
                    total_amount=total_amount,
                    status=OrderStatusEnum.NEW,
                    payment_status=PaymentStatusEnum.NOT_PAID,
                    delivery_method=order_data.delivery_method,
                    phone_number=phone_number,
                    delivery_address=delivery_address,
                    telegram_username=user.tg_name
                )
                self.session.add(order)
                await self.session.flush()  # Получаем id заказа
                
                logger.info(f"Создан заказ с ID: {order.id}")
                
                # Создаем элементы заказа из элементов корзины
                for cart_item in cart_items:
                    # Проверяем наличие необходимых данных
                    if not hasattr(cart_item, 'product') or not cart_item.product:
                        logger.warning(f"Пропуск элемента корзины без продукта: {cart_item}")
                        continue
                    
                    product = cart_item.product
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=cart_item.product_id,
                        product_name=product.name,
                        quantity=cart_item.quantity,
                        price=Decimal(str(product.price))
                    )
                    self.session.add(order_item)
                    logger.info(f"Добавлен товар в заказ: {product.name}, количество: {cart_item.quantity}")
            
            # Очищаем корзину
            await self.cart_service.clear_cart(user)
            logger.info("Корзина очищена")
            
            # Фиксируем транзакцию
            await self.session.commit()
            logger.info("Транзакция зафиксирована")
            
            # Получаем заказ со всеми связанными данными
            result = await self.session.execute(
                select(Order)
                .where(Order.id == order.id)
                .options(joinedload(Order.items))
            )
            return result.unique().scalar_one()
            
        except HTTPException as he:
            logger.error(f"HTTP ошибка: {he.detail}")
            await self.session.rollback()
            raise he
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            await self.session.rollback()
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Трассировка: {error_details}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при создании заказа: {str(e)}"
            )

    async def get_user_orders(self, user: UserResponse, skip: int = 0, limit: int = 10):
        """
        Получает список заказов пользователя
        
        Args:
            user: Объект пользователя
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user.id)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.unique().scalars().all()

    async def get_order_with_items(self, order_id: UUID):
        """
        Получает заказ со всеми его товарами
        
        Args:
            order_id: ID заказа
            
        Returns:
            Order: Заказ с товарами или None, если заказ не найден
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(joinedload(Order.items))
        )
        return result.unique().scalar_one_or_none()

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
        
        # Получаем обновленный заказ со всеми связанными данными
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(joinedload(Order.items))
        )
        return result.unique().scalar_one()
    
    async def get_all_orders(self, skip: int = 0, limit: int = 10):
        """
        Получает список всех заказов с пагинацией
        
        Args:
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        result = await self.session.execute(
            select(Order)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.unique().scalars().all()
    
    async def get_orders_by_username(self, username: str, skip: int = 0, limit: int = 10):
        """
        Получает список заказов по имени пользователя в Telegram
        
        Args:
            username: Имя пользователя в Telegram
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.telegram_username == username)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.unique().scalars().all()
    
    async def get_orders_by_status(self, status: OrderStatusEnum, skip: int = 0, limit: int = 10):
        """
        Получает список заказов по статусу
        
        Args:
            status: Статус заказа
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.status == status)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.unique().scalars().all()
    
    async def get_orders_by_date_range(self, start_date, end_date, skip: int = 0, limit: int = 10):
        """
        Получает список заказов за указанный период
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            skip: Сколько заказов пропустить
            limit: Максимальное количество заказов
            
        Returns:
            List[Order]: Список заказов
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.created_at >= start_date, Order.created_at <= end_date)
            .options(joinedload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.unique().scalars().all()
    
    async def delete_order(self, order_id: UUID):
        """
        Удаляет заказ
        
        Args:
            order_id: ID заказа
            
        Raises:
            HTTPException: Если заказ не найден
        """
        order = await self.get_order_with_items(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        await self.session.delete(order)
        await self.session.commit()
        
    async def delete_completed_orders(self):
        """
        Удаляет все завершенные заказы
        
        Returns:
            int: Количество удаленных заказов
        """
        # Получаем все завершенные заказы
        result = await self.session.execute(
            select(Order)
            .where(Order.status == OrderStatusEnum.COMPLETED)
        )
        completed_orders = result.scalars().all()
        
        # Удаляем каждый заказ
        count = 0
        for order in completed_orders:
            await self.session.delete(order)
            count += 1
        
        await self.session.commit()
        return count
    
