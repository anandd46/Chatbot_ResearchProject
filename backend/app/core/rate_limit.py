from app.core.config import settings
from app.core.logging import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_GENERAL])
