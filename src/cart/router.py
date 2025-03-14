
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID

from ..database import get_async_session
from ..auth.router import get_current_user
from ..auth.schemas import UserResponse
from ..cart.service import CartService

from ..auth.router import get_current_user
from ..auth.schemas import UserResponse

from .service import CartService
from .schemas import CartItemCreate, CartItemUpdate



router = APIRouter(
    prefix="/cart",
    tags=["cart"]
)
async def get_cart_service(
    session: AsyncSession = Depends(get_async_session),
) -> CartService:
    return CartService(session)

@router.get("/")
async def get_cart(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    cart_service: CartService = Depends(get_cart_service)
):
    '''Получение или создание корзины для пользователя'''
    return await cart_service.get_or_create_cart(current_user)


@router.post("/add")
async def add_item_to_cart(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    cart_service: CartService = Depends(get_cart_service),
    cart_item: CartItemCreate = Body(..., embed=True)
):
    '''Добавление товара в корзину, в случае отсутствия корзины для пользователя, создается новая корзина и товар добавляется в нее'''
    return await cart_service.add_item_to_cart(current_user, cart_item)


@router.put("/update")
async def update_item_in_cart(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    cart_service: CartService = Depends(get_cart_service),
    cart_item: CartItemUpdate = Body(..., embed=True)
):
    '''Обновление количества товара в корзине'''
    return await cart_service.update_item_in_cart(current_user, cart_item)


@router.delete("/delete")
async def delete_cart(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    cart_service: CartService = Depends(get_cart_service)
):
    '''Удаление корзины'''
    return await cart_service.delete_cart(current_user)