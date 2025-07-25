"""
Фабрика для создания и управления провайдерами AI моделей.
"""

from typing import Dict, List, Type, Any, Optional
from ai_api_server.providers.base import BaseProvider
from ai_api_server.providers.openai import OpenAIProvider
from ai_api_server.providers.gemini import GeminiProvider
from ai_api_server.providers.cody import CodyProvider
from ai_api_server.providers.openrouter import OpenRouterProvider


class ProviderFactory:
    """Фабрика для создания провайдеров."""
    
    # Реестр доступных провайдеров
    _providers_registry: Dict[str, Type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "cody": CodyProvider,
        "openrouter": OpenRouterProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """
        Зарегистрировать новый провайдер.
        
        Args:
            name: Имя провайдера
            provider_class: Класс провайдера
        """
        cls._providers_registry[name] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Получить список доступных провайдеров.
        
        Returns:
            List[str]: Список имен провайдеров
        """
        return list(cls._providers_registry.keys())
    
    @classmethod
    def create_provider(cls, name: str, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """
        Создать экземпляр провайдера.
        
        Args:
            name: Имя провайдера
            config: Конфигурация провайдера
            
        Returns:
            Optional[BaseProvider]: Экземпляр провайдера или None
        """
        if name not in cls._providers_registry:
            raise ValueError(f"Провайдер '{name}' не найден в реестре")
        
        provider_class = cls._providers_registry[name]
        
        try:
            return provider_class(config)
        except Exception as e:
            print(f"Ошибка создания провайдера {name}: {e}")
            return None
    
    @classmethod
    def create_all_providers(cls, providers_config: Dict[str, Dict[str, Any]]) -> Dict[str, BaseProvider]:
        """
        Создать все настроенные провайдеры.
        
        Args:
            providers_config: Конфигурация всех провайдеров
            
        Returns:
            Dict[str, BaseProvider]: Словарь созданных провайдеров
        """
        providers = {}
        
        for provider_name, provider_config in providers_config.items():
            # Проверяем, включен ли провайдер
            if not provider_config.get("enabled", True):
                print(f"Провайдер {provider_name} отключен в конфигурации")
                continue
            
            try:
                # Создаем провайдер
                provider = cls.create_provider(provider_name, provider_config)
                if provider:
                    providers[provider_name] = provider
                    print(f"Провайдер {provider_name} создан")
                else:
                    print(f"Не удалось создать провайдер {provider_name}")
            except Exception as e:
                print(f"Ошибка создания провайдера {provider_name}: {e}")
        
        return providers
    
    @classmethod
    def validate_provider_config(cls, name: str, config: Dict[str, Any]) -> List[str]:
        """
        Валидировать конфигурацию провайдера.
        
        Args:
            name: Имя провайдера
            config: Конфигурация провайдера
            
        Returns:
            List[str]: Список ошибок валидации
        """
        errors = []
        
        if name not in cls._providers_registry:
            errors.append(f"Провайдер '{name}' не найден в реестре")
            return errors
        
        # Базовая валидация
        if not isinstance(config, dict):
            errors.append("Конфигурация должна быть словарем")
            return errors
        
        # Проверяем обязательные поля
        required_fields = ["enabled"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Отсутствует обязательное поле: {field}")
        
        # Специфичная валидация для каждого провайдера
        if name == "openai":
            if "api_key_env" not in config:
                errors.append("Для OpenAI провайдера требуется поле 'api_key_env'")
        
        elif name == "gemini":
            if "api_key_env" not in config:
                errors.append("Для Gemini провайдера требуется поле 'api_key_env'")
        
        elif name == "cody":
            if "api_key_env" not in config:
                errors.append("Для Cody.su провайдера требуется поле 'api_key_env'")
        
        elif name == "openrouter":
            if "api_key_env" not in config:
                errors.append("Для OpenRouter провайдера требуется поле 'api_key_env'")
        
        return errors
    
    @classmethod
    def get_provider_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о провайдере.
        
        Args:
            name: Имя провайдера
            
        Returns:
            Optional[Dict[str, Any]]: Информация о провайдере
        """
        if name not in cls._providers_registry:
            return None
        
        provider_class = cls._providers_registry[name]
        
        return {
            "name": name,
            "class_name": provider_class.__name__,
            "module": provider_class.__module__,
            "description": provider_class.__doc__ or "Описание отсутствует"
        }
    
    @classmethod
    def get_all_providers_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Получить информацию о всех зарегистрированных провайдерах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Информация о всех провайдерах
        """
        providers_info = {}
        
        for name in cls._providers_registry:
            info = cls.get_provider_info(name)
            if info:
                providers_info[name] = info
        
        return providers_info