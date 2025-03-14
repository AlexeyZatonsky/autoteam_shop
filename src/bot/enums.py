from enum import Enum


class OrderStatusEnum(str, Enum):
    """Статусы заказа"""
    NEW = "Новый"
    PROCESSING = "Передано в доставку"
    READY = "Готов к выдаче"
    CANCELLED = "Отменён"
    COMPLETED = "Завершённый"


class PaymentStatusEnum(str, Enum):
    """Статусы оплаты"""
    PAID = "Оплачено"
    NOT_PAID = "Не оплачено"
    PAYMENT_ON_DELIVERY = "Оплата при получении"


class DeliveryMethodEnum(str, Enum):
    """Методы доставки"""
    SDEK = "СДЭК"
    PEK = "ПЭК"
    BAIKAL = "Байкал"
    KIT = "Кит"
    BUSINESS_LINES = "Деловые линии"
    PICKUP = "Самовывоз"
    POST = "Почта" 