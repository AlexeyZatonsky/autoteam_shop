from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.settings.config import settings
from src.auth.router import router as auth_router
from src.products.router import router as products_router, upload_router
from src.categories.router import router as categories_router


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(upload_router)

