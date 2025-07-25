"""
Менеджер провайдеров AI моделей.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from ai_api_server.providers.base import BaseProvider, ModelInfo, ChatRequest, ChatResponse
from ai_api_server.modules.factory import ProviderFactory
from ai_api_server.modules.cache import ModelCache
from ai_api_server.modules.filters import ModelFilter
from ai_api_server.modules.statistics import StatisticsManager


class ProvidersManager:
    """Менеджер для управления всеми провайдерами AI моделей."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация менеджера провайдеров.
        
        Args:
            config: Полная конфигурация приложения
        """
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        
        # Инициализация модулей
        self.cache = ModelCache(config.get("models_cache", {}))
        self.filter = ModelFilter(config.get("model_filters", {}))
        self.statistics = StatisticsManager(config.get("statistics", {}))
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Инициализировать менеджер провайдеров."""
        if self._initialized:
            return
        
        # Инициализируем базу данных статистики
        await self.statistics.initialize_database()
        
        # Загружаем кэш
        await self.cache.load_cache()
        
        # Создаем провайдеры
        providers_config = self.config.get("providers", {})
        self.providers = ProviderFactory.create_all_providers(providers_config)
        
        print(f"Инициализированы провайдеры: {list(self.providers.keys())}")
        
        self._initialized = True
    
    async def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить информацию о всех провайдерах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Информация о провайдерах
        """
        providers_info = {}
        
        for name, provider in self.providers.items():
            try:
                provider_info = provider.get_provider_info()
                providers_info[name] = {
                    "name": provider_info.name,
                    "display_name": provider_info.display_name,
                    "description": provider_info.description,
                    "version": provider_info.version,
                    "enabled": provider_info.enabled,
                    "available": provider.is_available()
                }
            except Exception as e:
                providers_info[name] = {
                    "name": name,
                    "display_name": name.title(),
                    "description": f"Ошибка получения информации: {e}",
                    "version": "unknown",
                    "enabled": False,
                    "available": False
                }
        
        return providers_info
    
    async def get_models_by_provider(self, use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получить модели, сгруппированные по провайдерам.
        
        Args:
            use_cache: Использовать кэш если доступен
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Модели по провайдерам
        """
        models_by_provider = {}
        
        for provider_name, provider in self.providers.items():
            try:
                # Проверяем доступность провайдера
                if not provider.is_available():
                    print(f"Провайдер {provider_name} недоступен")
                    models_by_provider[provider_name] = []
                    continue
                
                # Проверяем кэш
                cached_models = None
                if use_cache:
                    cached_models = await self.cache.get_cached_models(provider_name)
                
                if cached_models:
                    # Используем кэшированные модели
                    models = [ModelInfo(**model_data) for model_data in cached_models]
                else:
                    # Получаем модели из API
                    models = await provider.get_models()
                    
                    # Кэшируем полученные модели
                    if models:
                        await self.cache.cache_models(provider_name, models)
                
                # Если модели не получены, просто говорим "недоступно"
                if not models:
                    print(f"Список моделей для {provider_name} недоступен")
                    models_by_provider[provider_name] = []
                    continue
                
                # Конвертируем в словари для JSON
                models_data = []
                for model in models:
                    model_dict = model.dict()
                    # Добавляем категорию
                    model_dict["category"] = self.filter.categorize_model(model)
                    models_data.append(model_dict)
                
                models_by_provider[provider_name] = models_data
                
            except Exception as e:
                print(f"Провайдер {provider_name} недоступен: {e}")
                models_by_provider[provider_name] = []
        
        return models_by_provider
    
    async def get_models_by_category(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получить модели, сгруппированные по категориям.
        
        Args:
            category: Фильтр по категории (если None - все категории)
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Модели по категориям
        """
        all_models = []
        
        # Собираем все модели от всех провайдеров
        models_by_provider = await self.get_models_by_provider()
        for provider_name, models in models_by_provider.items():
            for model_data in models:
                model_data["provider"] = provider_name
                all_models.append(ModelInfo(**{k: v for k, v in model_data.items() if k != "provider"}))
        
        # Группируем по категориям
        if category:
            # Фильтруем по конкретной категории
            filtered_models = self.filter.filter_models_by_category(all_models, category)
            return {category: [model.dict() for model in filtered_models]}
        else:
            # Группируем по всем категориям
            grouped = self.filter.group_models_by_category(all_models)
            result = {}
            for cat, models in grouped.items():
                result[cat] = [model.dict() for model in models]
            return result
    
    async def search_models(self, query: str, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Поиск моделей по запросу.
        
        Args:
            query: Поисковый запрос
            provider: Фильтр по провайдеру
            
        Returns:
            List[Dict[str, Any]]: Найденные модели
        """
        all_models = []
        
        # Получаем модели
        models_by_provider = await self.get_models_by_provider()
        
        for provider_name, models in models_by_provider.items():
            if provider and provider_name != provider:
                continue
            
            for model_data in models:
                model_data["provider"] = provider_name
                all_models.append(ModelInfo(**{k: v for k, v in model_data.items() if k != "provider"}))
        
        # Выполняем поиск
        found_models = self.filter.search_models(all_models, query)
        
        # Конвертируем в словари
        result = []
        for model in found_models:
            model_dict = model.dict()
            model_dict["category"] = self.filter.categorize_model(model)
            result.append(model_dict)
        
        return result
    
    async def chat_completion(self, request: ChatRequest) -> Tuple[ChatResponse, int]:
        """
        Выполнить генерацию текста.
        
        Args:
            request: Запрос для генерации
            
        Returns:
            Tuple[ChatResponse, int]: Ответ и время выполнения в мс
        """
        # Определяем провайдера по модели
        provider = await self._find_provider_for_model(request.model)
        if not provider:
            raise ValueError(f"Провайдер для модели {request.model} не найден")
        
        # Засекаем время
        start_time = datetime.now()
        
        try:
            # Выполняем запрос
            response = await provider.chat_completion(request)
            
            # Вычисляем время выполнения
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Записываем статистику
            await self.statistics.record_usage(
                provider_name=provider.name,
                model_id=request.model,
                request_tokens=response.usage.get("prompt_tokens") if response.usage else None,
                response_tokens=response.usage.get("completion_tokens") if response.usage else None,
                response_time_ms=response_time_ms,
                success=True
            )
            
            return response, response_time_ms
            
        except Exception as e:
            # Записываем ошибку в статистику
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            await self.statistics.record_usage(
                provider_name=provider.name,
                model_id=request.model,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            raise e
    
    async def _find_provider_for_model(self, model_id: str) -> Optional[BaseProvider]:
        """
        Найти провайдера для модели.
        
        Args:
            model_id: ID модели
            
        Returns:
            Optional[BaseProvider]: Провайдер или None
        """
        for provider in self.providers.values():
            if provider.validate_model(model_id):
                return provider
        return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику использования.
        
        Returns:
            Dict[str, Any]: Статистика
        """
        summary = await self.statistics.get_statistics_summary()
        popular_providers = await self.statistics.get_popular_providers()
        popular_models = await self.statistics.get_popular_models()
        
        return {
            "summary": summary,
            "popular_providers": popular_providers,
            "popular_models": popular_models
        }
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Получить информацию о кэше.
        
        Returns:
            Dict[str, Any]: Информация о кэше
        """
        return self.cache.get_cache_info()
    
    async def clear_cache(self, provider: Optional[str] = None) -> None:
        """
        Очистить кэш.
        
        Args:
            provider: Провайдер для очистки (если None - очистить весь кэш)
        """
        await self.cache.clear_cache(provider)
    
    async def refresh_models(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Обновить модели (принудительно).
        
        Args:
            provider: Провайдер для обновления (если None - все провайдеры)
            
        Returns:
            Dict[str, Any]: Результат обновления
        """
        result = {"updated_providers": [], "errors": []}
        
        providers_to_update = [provider] if provider else list(self.providers.keys())
        
        for provider_name in providers_to_update:
            if provider_name not in self.providers:
                result["errors"].append(f"Провайдер {provider_name} не найден")
                continue
            
            try:
                # Очищаем кэш для провайдера
                await self.cache.clear_cache(provider_name)
                
                # Получаем свежие модели
                provider_obj = self.providers[provider_name]
                models = await provider_obj.get_models()
                
                # Кэшируем новые модели
                if models:
                    await self.cache.cache_models(provider_name, models)
                
                result["updated_providers"].append({
                    "provider": provider_name,
                    "models_count": len(models)
                })
                
            except Exception as e:
                result["errors"].append(f"Ошибка обновления {provider_name}: {str(e)}")
        
        return result
    
    def get_available_categories(self) -> List[Dict[str, Any]]:
        """
        Получить список доступных категорий.
        
        Returns:
            List[Dict[str, Any]]: Список категорий
        """
        return self.filter.get_available_categories()