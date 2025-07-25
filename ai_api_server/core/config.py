"""
Менеджер конфигурации AI API Server.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Менеджер конфигурации."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Инициализация менеджера конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        self.load_config()
    
    def load_config(self) -> None:
        """Загрузить конфигурацию из файла."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                print(f"Файл конфигурации {self.config_path} не найден, используется конфигурация по умолчанию")
                self._config = self._get_default_config()
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Получить конфигурацию по умолчанию."""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            },
            "providers": {
                "openai": {
                    "enabled": True,
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "fetch_models_dynamically": True
                },
                "gemini": {
                    "enabled": True,
                    "api_key_env": "GEMINI_API_KEY",
                    "fetch_models_dynamically": True
                }
            },
            "models_cache": {
                "enabled": True,
                "update_interval_hours": 24,
                "cache_file": "data/models_cache.json",
                "force_update_on_startup": False
            },
            "model_filters": {
                "image_generation": {
                    "keywords": ["image", "dall-e", "imagen", "midjourney", "stable-diffusion"],
                    "category": "image_generation"
                },
                "text_generation": {
                    "keywords": ["gpt", "claude", "gemini", "llama", "text"],
                    "category": "text_generation"
                },
                "code_generation": {
                    "keywords": ["code", "codex", "copilot", "programming"],
                    "category": "code_generation"
                },
                "embedding": {
                    "keywords": ["embedding", "embed", "vector"],
                    "category": "embedding"
                },
                "audio": {
                    "keywords": ["whisper", "audio", "speech", "tts"],
                    "category": "audio"
                }
            },
            "statistics": {
                "enabled": True,
                "database_file": "data/statistics.db",
                "track_usage": True,
                "track_response_time": True,
                "track_errors": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log"
            },
            "security": {
                "cors_origins": [
                    "http://localhost:3000",
                    "http://localhost:8080"
                ],
                "rate_limit": {
                    "requests_per_minute": 60
                }
            },
            "data": {
                "directory": "data",
                "auto_create": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение конфигурации по ключу.
        
        Args:
            key: Ключ конфигурации (поддерживает точечную нотацию, например 'server.port')
            default: Значение по умолчанию
            
        Returns:
            Any: Значение конфигурации
        """
        if not self._config:
            return default
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_server_config(self) -> Dict[str, Any]:
        """Получить конфигурацию сервера."""
        return self.get("server", {})
    
    def get_providers_config(self) -> Dict[str, Any]:
        """Получить конфигурацию провайдеров."""
        return self.get("providers", {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Получить конфигурацию кэша."""
        return self.get("models_cache", {})
    
    def get_filters_config(self) -> Dict[str, Any]:
        """Получить конфигурацию фильтров."""
        return self.get("model_filters", {})
    
    def get_statistics_config(self) -> Dict[str, Any]:
        """Получить конфигурацию статистики."""
        return self.get("statistics", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Получить конфигурацию логирования."""
        return self.get("logging", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Получить конфигурацию безопасности."""
        return self.get("security", {})
    
    def get_data_config(self) -> Dict[str, Any]:
        """Получить конфигурацию данных."""
        return self.get("data", {})
    
    def ensure_directories(self) -> None:
        """Создать необходимые директории."""
        data_config = self.get_data_config()
        
        if data_config.get("auto_create", True):
            # Создаем основную директорию данных
            data_dir = data_config.get("directory", "data")
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            
            # Создаем директорию для логов
            logs_dir = Path(self.get("logging.file", "logs/app.log")).parent
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем директорию для кэша
            cache_file = self.get("models_cache.cache_file", "data/models_cache.json")
            cache_dir = Path(cache_file).parent
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def reload_config(self) -> None:
        """Перезагрузить конфигурацию."""
        self.load_config()
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        Сохранить текущую конфигурацию в файл.
        
        Args:
            config_path: Путь для сохранения (если None, используется текущий путь)
        """
        if not self._config:
            return
        
        save_path = config_path or self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def update_config(self, key: str, value: Any) -> None:
        """
        Обновить значение конфигурации.
        
        Args:
            key: Ключ конфигурации (поддерживает точечную нотацию)
            value: Новое значение
        """
        if not self._config:
            self._config = {}
        
        keys = key.split('.')
        config = self._config
        
        # Создаем вложенную структуру если необходимо
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Устанавливаем значение
        config[keys[-1]] = value
    
    @property
    def config(self) -> Dict[str, Any]:
        """Получить полную конфигурацию."""
        return self._config or {}