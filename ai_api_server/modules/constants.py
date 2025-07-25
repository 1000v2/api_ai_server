"""
Константы и конфигурация AI API Server.
"""

from enum import Enum
from typing import Dict, List, Any

# Информация о версии и сервисе
SERVICE_INFO = {
    "name": "AI API Server",
    "version": "1.0.0",
    "description": "Модульный API сервер для работы с различными AI провайдерами",
    "author": "AI API Server Team",
    "license": "MIT"
}

# Поддерживаемые типы эндпоинтов
class EndpointType(Enum):
    """Типы поддерживаемых эндпоинтов."""
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    TRANSCRIPTION = "transcription"
    VECTORIZATION = "vectorization"
    IMAGE_EDITING = "image_editing"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    EMBEDDINGS = "embeddings"
    MODERATION = "moderation"
    FINE_TUNING = "fine_tuning"


# Поддерживаемые эндпоинты по провайдерам
SUPPORTED_ENDPOINTS = {
    "openai": [
        EndpointType.TEXT_GENERATION,
        EndpointType.IMAGE_GENERATION,
        EndpointType.TRANSCRIPTION,
        EndpointType.VECTORIZATION,
        EndpointType.IMAGE_EDITING,
        EndpointType.TEXT_TO_SPEECH,
        EndpointType.EMBEDDINGS,
        EndpointType.MODERATION,
        EndpointType.FINE_TUNING
    ],
    "gemini": [
        EndpointType.TEXT_GENERATION,
        EndpointType.VECTORIZATION,
        EndpointType.EMBEDDINGS
    ],
    "cody": [
        EndpointType.TEXT_GENERATION,
        EndpointType.IMAGE_GENERATION,
        EndpointType.AUDIO_GENERATION,
        EndpointType.IMAGE_EDITING
    ],
    "openrouter": [
        EndpointType.TEXT_GENERATION
    ]
}

# Категории моделей (обновленные)
MODEL_CATEGORIES = {
    "text_generation": {
        "name": "Генератор текста",
        "description": "Модели для генерации и обработки текста",
        "keywords": ["gpt", "claude", "gemini", "llama", "chat", "completion"],
        "icon": "💬",
        "default": True  # Категория по умолчанию для неопределенных моделей
    },
    "image_generation": {
        "name": "Генератор картинок",
        "description": "Модели для генерации изображений",
        "keywords": ["dall-e", "imagen", "midjourney", "stable-diffusion", "image"],
        "icon": "🎨"
    },
    "audio_generation": {
        "name": "Генератор аудио",
        "description": "Модели для генерации аудио и музыки",
        "keywords": ["audio", "music", "sound", "tts", "voice"],
        "icon": "🎵"
    },
    "transcription": {
        "name": "Транскрипция",
        "description": "Модели для преобразования речи в текст",
        "keywords": ["whisper", "transcription", "speech-to-text", "stt"],
        "icon": "🎤"
    },
    "vectorization": {
        "name": "Векторизация",
        "description": "Модели для создания эмбеддингов и векторизации",
        "keywords": ["embedding", "embed", "vector", "similarity"],
        "icon": "🔢"
    },
    "image_editing": {
        "name": "Редактирование картинок",
        "description": "Модели для редактирования и обработки изображений",
        "keywords": ["edit", "inpaint", "outpaint", "variation"],
        "icon": "✏️"
    }
}

# Лимиты по умолчанию для провайдеров (запросов в минуту)
DEFAULT_RATE_LIMITS = {
    "openai": {
        "gpt-4": 10,
        "gpt-4-turbo": 10,
        "gpt-3.5-turbo": 60,
        "dall-e-3": 5,
        "dall-e-2": 10,
        "whisper-1": 50,
        "text-embedding-ada-002": 100
    },
    "gemini": {
        "models/gemini-pro": 60,
        "models/gemini-pro-vision": 60,
        "models/gemini-1.5-pro": 10,
        "models/gemini-1.5-flash": 100
    },
    "cody": {
        "gpt-4.1": 10,  # 10rpm согласно документации
        "gpt-4o": 10,
        "gpt-4o-mini": 10,
        "gpt-4o-mini-audio-preview": 5,
        "gpt-image-1": 5,
        "flux.1-kontext-pro": 5
    },
    "openrouter": {
        "openai/gpt-4-turbo": 20,
        "openai/gpt-3.5-turbo": 60,
        "anthropic/claude-3-opus": 10,
        "anthropic/claude-3-sonnet": 20,
        "google/gemini-pro": 60,
        "meta-llama/llama-2-70b-chat": 30,
        "mistralai/mistral-7b-instruct": 100,
        "cohere/command-r-plus": 20
    }
}

# Коды ошибок лимитов
RATE_LIMIT_ERROR_CODES = {
    "openai": [429, "rate_limit_exceeded"],
    "gemini": [429, "RATE_LIMIT_EXCEEDED", "QUOTA_EXCEEDED"],
    "cody": [429, "rate_limit_exceeded", "too_many_requests"],
    "openrouter": [429, "rate_limit_exceeded", "quota_exceeded"]
}

# Время сброса лимитов (в часах)
RATE_LIMIT_RESET_HOURS = {
    "openai": 24,  # Сброс каждые 24 часа
    "gemini": 24,
    "default": 24
}

# Статусы API ключей
class APIKeyStatus(Enum):
    """Статусы API ключей."""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID = "invalid"
    EXPIRED = "expired"
    DISABLED = "disabled"


# Приоритеты провайдеров (для ротации)
PROVIDER_PRIORITIES = {
    "openai": 1,
    "gemini": 2
}

# Конфигурация по умолчанию для новых провайдеров
DEFAULT_PROVIDER_CONFIG = {
    "enabled": True,
    "fetch_models_dynamically": True,
    "rate_limit_enabled": True,
    "key_rotation_enabled": True,
    "retry_attempts": 3,
    "retry_delay_seconds": 1,
    "health_check_interval_minutes": 5
}

# Поддерживаемые форматы файлов
SUPPORTED_FILE_FORMATS = {
    "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "document": [".txt", ".pdf", ".docx", ".md"]
}

# HTTP статус коды
HTTP_STATUS_CODES = {
    "SUCCESS": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# Сообщения об ошибках
ERROR_MESSAGES = {
    "NO_API_KEY": "API ключ не настроен для провайдера {provider}",
    "INVALID_API_KEY": "Недействительный API ключ для провайдера {provider}",
    "RATE_LIMIT_EXCEEDED": "Превышен лимит запросов для провайдера {provider}",
    "QUOTA_EXCEEDED": "Превышена квота для провайдера {provider}",
    "MODEL_NOT_FOUND": "Модель {model} не найдена у провайдера {provider}",
    "PROVIDER_UNAVAILABLE": "Провайдер {provider} недоступен",
    "INVALID_REQUEST": "Некорректный запрос: {details}",
    "INTERNAL_ERROR": "Внутренняя ошибка сервера: {details}"
}

# Конфигурация логирования
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "detailed",
            "level": "DEBUG"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Метрики для мониторинга
METRICS_CONFIG = {
    "enabled": True,
    "collect_interval_seconds": 60,
    "retention_days": 30,
    "metrics": [
        "requests_total",
        "requests_duration_seconds",
        "errors_total",
        "active_connections",
        "provider_availability",
        "model_usage_count",
        "tokens_processed_total"
    ]
}