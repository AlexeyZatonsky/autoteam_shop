import enum



class OrderStatusEnum(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
class PaymentMethodEnum(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"
    
class DeliveryMethodEnum(str, enum.Enum):
    SDEK = "sdek"
    PEK = "pek"
    BAIKAL = "baikal"
    KIT = "kit"
    BUSINESS_LINES = "business_lines"
    PICKUP = "pickup"
    POST = "post"
