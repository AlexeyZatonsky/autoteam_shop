from .product_create import router as product_create_router
from .product_view import router as product_view_router
from .product_edit import router as product_edit_router
from .product_list import router as product_list_router

__all__ = [
    'product_create_router',
    'product_view_router',
    'product_edit_router',
    'product_list_router',
] 