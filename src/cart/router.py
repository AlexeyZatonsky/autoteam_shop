from fastapi import APIRouter, Depends, HTTPException, status, Header, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Annotated
import uuid

from src.cart.schemas import (
    CartItemCreate, 
    CartItemUpdate, 
    CartItemResponse, 
    CartDetailResponse,
    CartItemDetailResponse
)
from src.cart.service import CartService
from src.database import get_async_session
from src.auth.router import get_current_user
from src.auth.models import Users


router = APIRouter(
    prefix="/api/cart",
    tags=["cart"]
)


def get_cart_service(session: AsyncSession = Depends(get_async_session)) -> CartService:
    """Зависимость для получения сервиса корзины"""
    return CartService(session)


@router.get("/", response_model=CartDetailResponse)
async def get_user_cart(
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Получает корзину текущего пользователя"""
    user_id = str(current_user.id)  # Используем ID пользователя из Telegram
    cart = await cart_service.get_user_cart_with_items(user_id)
    
    if not cart:
        cart = await cart_service.get_or_create_cart(user_id)
    
    # Преобразуем данные для ответа
    items = []
    for item in cart.items:
        items.append(CartItemDetailResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_add=item.price_at_add,
            product_name=item.product.name,
            product_description=item.product.description,
            product_image=item.product.images[0] if item.product.images else None
        ))
    
    total_price = await cart_service.calculate_cart_total(cart.id)
    
    return CartDetailResponse(
        id=cart.id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        is_active=cart.is_active,
        items=items,
        total_price=total_price
    )


@router.get("/count", response_model=int)
async def get_cart_items_count(
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Получает количество товаров в корзине пользователя"""
    user_id = str(current_user.id)
    return await cart_service.get_cart_items_count(user_id)


@router.post("/merge", response_model=CartDetailResponse)
async def merge_guest_cart(
    guest_user_id: str,
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Объединяет корзину гостя с корзиной авторизованного пользователя"""
    auth_user_id = str(current_user.id)
    cart = await cart_service.merge_guest_cart(guest_user_id, auth_user_id)
    
    # Преобразуем данные для ответа
    items = []
    for item in cart.items:
        items.append(CartItemDetailResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_add=item.price_at_add,
            product_name=item.product.name,
            product_description=item.product.description,
            product_image=item.product.images[0] if item.product.images else None
        ))
    
    total_price = await cart_service.calculate_cart_total(cart.id)
    
    return CartDetailResponse(
        id=cart.id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        is_active=cart.is_active,
        items=items,
        total_price=total_price
    )


@router.post("/items", response_model=CartItemResponse)
async def add_item_to_cart(
    item: CartItemCreate,
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Добавляет товар в корзину"""
    user_id = str(current_user.id)  # Используем ID пользователя из Telegram
    cart_item = await cart_service.add_item_to_cart(user_id, item)
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Продукт не найден"
        )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        price_at_add=cart_item.price_at_add
    )


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: uuid.UUID,
    item_data: CartItemUpdate,
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Обновляет элемент корзины"""
    user_id = str(current_user.id)  # Используем ID пользователя из Telegram
    cart_item = await cart_service.update_cart_item(user_id, item_id, item_data)
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент корзины не найден"
        )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        price_at_add=cart_item.price_at_add
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: uuid.UUID,
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Удаляет элемент из корзины"""
    user_id = str(current_user.id)  # Используем ID пользователя из Telegram
    success = await cart_service.remove_cart_item(user_id, item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Элемент корзины не найден"
        )


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: Users = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service)
):
    """Очищает корзину пользователя"""
    user_id = str(current_user.id)  # Используем ID пользователя из Telegram
    await cart_service.clear_cart(user_id)
