from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.settings.config import settings
from src.auth.router import router as auth_router
from src.products.router import router as products_router, upload_router
from src.categories.router import router as categories_router
from src.cart.router import router as cart_router
from src.orders.router import router as orders_router
from fastapi.openapi.utils import get_openapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Autoteam Shop API",
    description="API для магазина автозапчастей",
    version="0.1.0",
    lifespan=lifespan,
)

# # Добавляем информацию о безопасности
# app.swagger_ui_init_oauth = {
#     "usePkceWithAuthorizationCodeGrant": False,
#     "useBasicAuthenticationWithAccessCodeGrant": False
# }

# Добавляем компонент безопасности в OpenAPI-схему
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем информацию о безопасности в OpenAPI-схему
# app.openapi = lambda: {
#     **get_openapi(
#         title=app.title,
#         version=app.version,
#         description=app.description,
#         routes=app.routes,
#     ),
#     "components": {
#         "securitySchemes": {
#             "BearerAuth": {
#                 "type": "http",
#                 "scheme": "bearer",
#                 "bearerFormat": "JWT",
#                 "description": "Введите JWT-токен, полученный после авторизации через Telegram"
#             }
#         }
#     },
#     "security": [{"BearerAuth": []}]
# }

# Регистрируем маршруты с префиксом /api
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(orders_router, prefix="/api")

