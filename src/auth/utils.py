import hmac
import hashlib
import time
from urllib.parse import parse_qs, unquote
import json
from typing import Dict

from .schemas import TelegramAuthData, TelegramUser
from ..settings.config import settings


def verify_telegram_hash(auth_data: Dict[str, str], bot_token: str) -> bool:
    """Verify telegram authentication data hash."""
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(
            auth_data.items(),
            key=lambda x: x[0]
        ) if k != 'hash'
    )
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hash == auth_data['hash']


def parse_telegram_data(data: str) -> TelegramAuthData:
    """Parse telegram authentication data from URL parameters."""
    # Decode URL-encoded data
    parsed = parse_qs(data)
    
    # Convert single-item lists to scalar values
    auth_data = {k: v[0] for k, v in parsed.items()}
    
    # Parse user data from JSON string
    user_data = json.loads(unquote(auth_data['user']))
    
    return TelegramAuthData(
        user=TelegramUser(**user_data),
        auth_date=int(auth_data['auth_date']),
        hash=auth_data['hash'],
        chat_instance=auth_data.get('chat_instance'),
        chat_type=auth_data.get('chat_type')
    )


def validate_telegram_authorization(auth_string: str) -> TelegramAuthData | None:
    """Validate telegram authorization data."""
    try:
        auth_data = parse_telegram_data(auth_string)
        
        # Check if the authorization is not expired (48 hours)
        if time.time() - auth_data.auth_date > 48 * 3600:
            return None
        
        # Convert auth_data to dict for verification
        auth_dict = {
            'auth_date': str(auth_data.auth_date),
            'hash': auth_data.hash,
            **auth_data.user.model_dump(exclude_none=True)
        }
        
        if auth_data.chat_instance:
            auth_dict['chat_instance'] = auth_data.chat_instance
        if auth_data.chat_type:
            auth_dict['chat_type'] = auth_data.chat_type
            
        # Verify hash
        if not verify_telegram_hash(auth_dict, settings.BOT_TOKEN):
            return None
            
        return auth_data
    except Exception:
        return None 