import enum



class OrderStatusEnum(str, enum.Enum):
    NEW = "Новый"
    PROCESSING = "Передано в доставку"
    READY = "Готов к выдаче"
    CANCELLED = "Отменён"
    COMPLETED = "Завершённый"
    
    
class PaymentStatusEnum(str, enum.Enum):
    PAID = "Оплачено"
    NOT_PAID = "Не оплачено"
    PAYMENT_ON_DELIVERY = "Оплата при получении" 
    
class DeliveryMethodEnum(str, enum.Enum):
    SDEK = "СДЭК"
    PEK = "ПЭК"
    BAIKAL = "Байкал"
    KIT = "Кит"
    BUSINESS_LINES = "Деловые линии"
    PICKUP = "Самовывоз"
    POST = "Почта"


class PaymentMethodEnum(str, enum.Enum):
    PAYMENT_ON_DELIVERY = "Оплата при получении"
    ONLINE_PAYMENT = "Оплата онлайн"
