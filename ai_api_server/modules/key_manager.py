"""
Менеджер API ключей с ротацией и управлением лимитами.
"""

import yaml
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from ai_api_server.modules.constants import APIKeyStatus, RATE_LIMIT_RESET_HOURS, RATE_LIMIT_ERROR_CODES


class APIKeyInfo:
    """Информация об API ключе."""
    
    def __init__(self, key: str, provider: str, name: str = None, priority: int = 1):
        """
        Инициализация информации о ключе.
        
        Args:
            key: API ключ
            provider: Имя провайдера
            name: Имя ключа (для идентификации)
            priority: Приоритет ключа (1 - высший)
        """
        self.key = key
        self.provider = provider
        self.name = name or f"{provider}_key_{hash(key) % 1000}"
        self.priority = priority
        self.status = APIKeyStatus.ACTIVE
        self.last_used = None
        self.rate_limit_reset_time = None
        self.error_count = 0
        self.success_count = 0
        self.last_error = None
        self.created_at = datetime.now()
    
    def is_available(self) -> bool:
        """Проверить доступность ключа."""
        if self.status == APIKeyStatus.ACTIVE:
            return True
        
        # Проверяем, не истек ли срок блокировки по лимиту
        if (self.status == APIKeyStatus.RATE_LIMITED and 
            self.rate_limit_reset_time and 
            datetime.now() > self.rate_limit_reset_time):
            self.status = APIKeyStatus.ACTIVE
            self.rate_limit_reset_time = None
            return True
        
        return False
    
    def mark_rate_limited(self, reset_hours: int = None) -> None:
        """Отметить ключ как заблокированный по лимиту."""
        self.status = APIKeyStatus.RATE_LIMITED
        reset_hours = reset_hours or RATE_LIMIT_RESET_HOURS.get(self.provider, 24)
        self.rate_limit_reset_time = datetime.now() + timedelta(hours=reset_hours)
    
    def mark_error(self, error_message: str) -> None:
        """Отметить ошибку для ключа."""
        self.error_count += 1
        self.last_error = error_message
        self.last_used = datetime.now()
        
        # Если слишком много ошибок, помечаем как недействительный
        if self.error_count >= 5:
            self.status = APIKeyStatus.INVALID
    
    def mark_success(self) -> None:
        """Отметить успешное использование ключа."""
        self.success_count += 1
        self.last_used = datetime.now()
        self.error_count = max(0, self.error_count - 1)  # Уменьшаем счетчик ошибок
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            "name": self.name,
            "provider": self.provider,
            "priority": self.priority,
            "status": self.status.value,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rate_limit_reset_time": self.rate_limit_reset_time.isoformat() if self.rate_limit_reset_time else None,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat()
        }


class APIKeyManager:
    """Менеджер API ключей с ротацией."""
    
    def __init__(self, keys_config_path: str = "api_keys.yaml"):
        """
        Инициализация менеджера ключей.
        
        Args:
            keys_config_path: Путь к файлу конфигурации ключей
        """
        self.keys_config_path = keys_config_path
        self.keys: Dict[str, List[APIKeyInfo]] = {}  # provider -> [keys]
        self.current_key_index: Dict[str, int] = {}  # provider -> current_index
        self._lock = asyncio.Lock()
        
        self.load_keys()
    
    def load_keys(self) -> None:
        """Загрузить ключи из конфигурационного файла."""
        if not Path(self.keys_config_path).exists():
            self.create_default_config()
            return
        
        try:
            with open(self.keys_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.keys.clear()
            self.current_key_index.clear()
            
            for provider_name, provider_config in config.get('providers', {}).items():
                keys_list = []
                
                # Новый формат - ключи в виде простого списка строк
                for i, key in enumerate(provider_config.get('keys', [])):
                    if isinstance(key, str):
                        # Простой формат - только ключ
                        key_info = APIKeyInfo(
                            key=key,
                            provider=provider_name,
                            name=f"{provider_name}_key_{i+1}",
                            priority=i+1
                        )
                    else:
                        # Старый формат - объект с параметрами
                        key_info = APIKeyInfo(
                            key=key['key'],
                            provider=provider_name,
                            name=key.get('name', f"{provider_name}_key_{i+1}"),
                            priority=key.get('priority', i+1)
                        )
                        
                        # Восстанавливаем статус если есть
                        if 'status' in key:
                            try:
                                key_info.status = APIKeyStatus(key['status'])
                            except ValueError:
                                pass
                    
                    keys_list.append(key_info)
                
                # Сортируем по приоритету
                keys_list.sort(key=lambda x: x.priority)
                
                self.keys[provider_name] = keys_list
                self.current_key_index[provider_name] = 0
                
        except Exception as e:
            print(f"Ошибка загрузки ключей: {e}")
            self.create_default_config()
    
    def create_default_config(self) -> None:
        """Создать конфигурационный файл по умолчанию."""
        default_config = {
            'providers': {
                'openai': {
                    'keys': [
                        {
                            'name': 'openai_primary',
                            'key': 'your_openai_api_key_here',
                            'priority': 1,
                            'enabled': True
                        }
                    ]
                },
                'gemini': {
                    'keys': [
                        {
                            'name': 'gemini_primary',
                            'key': 'your_gemini_api_key_here',
                            'priority': 1,
                            'enabled': True
                        }
                    ]
                }
            }
        }
        
        try:
            with open(self.keys_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            print(f"Создан файл конфигурации ключей: {self.keys_config_path}")
        except Exception as e:
            print(f"Ошибка создания конфигурации ключей: {e}")
    
    def save_keys(self) -> None:
        """Сохранить текущее состояние ключей."""
        config = {'providers': {}}
        
        for provider_name, keys_list in self.keys.items():
            config['providers'][provider_name] = {
                'keys': [
                    {
                        'name': key.name,
                        'key': key.key,
                        'priority': key.priority,
                        'status': key.status.value,
                        'enabled': key.status != APIKeyStatus.DISABLED
                    }
                    for key in keys_list
                ]
            }
        
        try:
            with open(self.keys_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"Ошибка сохранения ключей: {e}")
    
    async def get_api_key(self, provider: str) -> Optional[Tuple[str, APIKeyInfo]]:
        """
        Получить доступный API ключ для провайдера.
        
        Args:
            provider: Имя провайдера
            
        Returns:
            Optional[Tuple[str, APIKeyInfo]]: Ключ и информация о нем или None
        """
        async with self._lock:
            if provider not in self.keys or not self.keys[provider]:
                return None
            
            keys_list = self.keys[provider]
            start_index = self.current_key_index.get(provider, 0)
            
            # Пробуем найти доступный ключ, начиная с текущего
            for i in range(len(keys_list)):
                index = (start_index + i) % len(keys_list)
                key_info = keys_list[index]
                
                if key_info.is_available():
                    self.current_key_index[provider] = index
                    return key_info.key, key_info
            
            # Если нет доступных ключей
            return None
    
    async def mark_key_error(self, provider: str, key: str, error_message: str, 
                           is_rate_limit: bool = False) -> None:
        """
        Отметить ошибку для ключа.
        
        Args:
            provider: Имя провайдера
            key: API ключ
            error_message: Сообщение об ошибке
            is_rate_limit: Является ли ошибка превышением лимита
        """
        async with self._lock:
            if provider not in self.keys:
                return
            
            for key_info in self.keys[provider]:
                if key_info.key == key:
                    if is_rate_limit:
                        key_info.mark_rate_limited()
                    else:
                        key_info.mark_error(error_message)
                    
                    # Переключаемся на следующий ключ
                    self._rotate_to_next_key(provider)
                    break
    
    async def mark_key_success(self, provider: str, key: str) -> None:
        """
        Отметить успешное использование ключа.
        
        Args:
            provider: Имя провайдера
            key: API ключ
        """
        async with self._lock:
            if provider not in self.keys:
                return
            
            for key_info in self.keys[provider]:
                if key_info.key == key:
                    key_info.mark_success()
                    break
    
    def _rotate_to_next_key(self, provider: str) -> None:
        """Переключиться на следующий ключ."""
        if provider in self.keys and self.keys[provider]:
            current_index = self.current_key_index.get(provider, 0)
            self.current_key_index[provider] = (current_index + 1) % len(self.keys[provider])
    
    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """
        Получить статус провайдера.
        
        Args:
            provider: Имя провайдера
            
        Returns:
            Dict[str, Any]: Статус провайдера
        """
        if provider not in self.keys:
            return {
                "provider": provider,
                "available": False,
                "reason": "Ключи не настроены",
                "keys_count": 0,
                "active_keys": 0
            }
        
        keys_list = self.keys[provider]
        active_keys = sum(1 for key in keys_list if key.is_available())
        
        return {
            "provider": provider,
            "available": active_keys > 0,
            "reason": "Нет доступных ключей" if active_keys == 0 else "OK",
            "keys_count": len(keys_list),
            "active_keys": active_keys,
            "keys": [key.to_dict() for key in keys_list]
        }
    
    def get_all_providers_status(self) -> Dict[str, Dict[str, Any]]:
        """Получить статус всех провайдеров."""
        status = {}
        
        # Добавляем настроенные провайдеры
        for provider in self.keys.keys():
            status[provider] = self.get_provider_status(provider)
        
        return status
    
    def is_rate_limit_error(self, provider: str, error_code: Any, error_message: str = "") -> bool:
        """
        Проверить, является ли ошибка превышением лимита.
        
        Args:
            provider: Имя провайдера
            error_code: Код ошибки
            error_message: Сообщение об ошибке
            
        Returns:
            bool: True если это ошибка лимита
        """
        if provider not in RATE_LIMIT_ERROR_CODES:
            return False
        
        limit_codes = RATE_LIMIT_ERROR_CODES[provider]
        
        # Проверяем код ошибки
        if error_code in limit_codes:
            return True
        
        # Проверяем сообщение об ошибке
        error_message_lower = error_message.lower()
        for code in limit_codes:
            if isinstance(code, str) and code.lower() in error_message_lower:
                return True
        
        return False
    
    async def cleanup_expired_limits(self) -> None:
        """Очистить истекшие ограничения по лимитам."""
        async with self._lock:
            for provider_keys in self.keys.values():
                for key_info in provider_keys:
                    if (key_info.status == APIKeyStatus.RATE_LIMITED and
                        key_info.rate_limit_reset_time and
                        datetime.now() > key_info.rate_limit_reset_time):
                        key_info.status = APIKeyStatus.ACTIVE
                        key_info.rate_limit_reset_time = None
    
    def add_key(self, provider: str, key: str, name: str = None, priority: int = 1) -> bool:
        """
        Добавить новый ключ.
        
        Args:
            provider: Имя провайдера
            key: API ключ
            name: Имя ключа
            priority: Приоритет
            
        Returns:
            bool: True если ключ добавлен успешно
        """
        try:
            if provider not in self.keys:
                self.keys[provider] = []
                self.current_key_index[provider] = 0
            
            # Проверяем, что ключ не дублируется
            for existing_key in self.keys[provider]:
                if existing_key.key == key:
                    return False
            
            key_info = APIKeyInfo(key, provider, name, priority)
            self.keys[provider].append(key_info)
            
            # Пересортировываем по приоритету
            self.keys[provider].sort(key=lambda x: x.priority)
            
            self.save_keys()
            return True
            
        except Exception as e:
            print(f"Ошибка добавления ключа: {e}")
            return False
    
    def remove_key(self, provider: str, key: str) -> bool:
        """
        Удалить ключ.
        
        Args:
            provider: Имя провайдера
            key: API ключ
            
        Returns:
            bool: True если ключ удален успешно
        """
        try:
            if provider not in self.keys:
                return False
            
            self.keys[provider] = [k for k in self.keys[provider] if k.key != key]
            
            # Сбрасываем индекс если нужно
            if not self.keys[provider]:
                self.current_key_index[provider] = 0
            else:
                self.current_key_index[provider] = min(
                    self.current_key_index[provider], 
                    len(self.keys[provider]) - 1
                )
            
            self.save_keys()
            return True
            
        except Exception as e:
            print(f"Ошибка удаления ключа: {e}")
            return False