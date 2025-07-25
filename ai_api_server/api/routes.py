"""
API маршруты для AI API Server.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from ai_api_server.providers.base import ChatRequest, ChatResponse
from ai_api_server.core.manager import ProvidersManager

router = APIRouter()

# Глобальная переменная для менеджера (будет инициализирована в main.py)
_manager: Optional[ProvidersManager] = None


def get_manager() -> ProvidersManager:
    """Получить экземпляр менеджера провайдеров."""
    if _manager is None:
        raise HTTPException(status_code=500, detail="Менеджер провайдеров не инициализирован")
    return _manager


def set_manager(manager: ProvidersManager) -> None:
    """Установить экземпляр менеджера провайдеров."""
    global _manager
    _manager = manager


@router.get("/", summary="Информация об API")
async def root():
    """Корневой эндпоинт с информацией об API."""
    return {
        "name": "AI API Server",
        "version": "1.0.0",
        "description": "Модульный API сервер для работы с различными AI провайдерами",
        "endpoints": {
            "providers": "/providers - Список всех провайдеров",
            "models": "/models - Модели, сгруппированные по провайдерам",
            "models_by_category": "/models/by-category - Модели по категориям",
            "search": "/models/search - Поиск моделей",
            "chat": "/chat/completions - Генерация текста",
            "statistics": "/statistics - Статистика использования",
            "cache": "/cache - Управление кэшем"
        }
    }


@router.get("/providers", summary="Получить список всех провайдеров")
async def get_providers(manager: ProvidersManager = Depends(get_manager)) -> Dict[str, Any]:
    """
    Получить информацию о всех доступных провайдерах.
    
    Returns:
        Dict[str, Any]: Информация о провайдерах
    """
    try:
        providers = await manager.get_all_providers()
        return {
            "success": True,
            "providers": providers,
            "total_count": len(providers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения провайдеров: {str(e)}")


@router.get("/models", summary="Получить модели, сгруппированные по провайдерам")
async def get_models_by_provider(
    use_cache: bool = Query(True, description="Использовать кэш"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Получить все модели, сгруппированные по провайдерам.
    
    Args:
        use_cache: Использовать кэшированные данные
        
    Returns:
        Dict[str, Any]: Модели по провайдерам
    """
    try:
        models = await manager.get_models_by_provider(use_cache=use_cache)
        
        # Подсчитываем общее количество моделей
        total_models = sum(len(provider_models) for provider_models in models.values())
        
        return {
            "success": True,
            "models": models,
            "providers_count": len(models),
            "total_models": total_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей: {str(e)}")


@router.get("/models/by-category", summary="Получить модели по категориям")
async def get_models_by_category(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Получить модели, сгруппированные по категориям.
    
    Args:
        category: Конкретная категория для фильтрации
        
    Returns:
        Dict[str, Any]: Модели по категориям
    """
    try:
        models = await manager.get_models_by_category(category=category)
        
        # Подсчитываем общее количество моделей
        total_models = sum(len(category_models) for category_models in models.values())
        
        return {
            "success": True,
            "models": models,
            "categories_count": len(models),
            "total_models": total_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей по категориям: {str(e)}")


@router.get("/models/categories", summary="Получить список доступных категорий")
async def get_categories(manager: ProvidersManager = Depends(get_manager)) -> Dict[str, Any]:
    """
    Получить список всех доступных категорий моделей.
    
    Returns:
        Dict[str, Any]: Список категорий
    """
    try:
        categories = manager.get_available_categories()
        return {
            "success": True,
            "categories": categories,
            "total_count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения категорий: {str(e)}")


@router.get("/models/search", summary="Поиск моделей")
async def search_models(
    q: str = Query(..., description="Поисковый запрос"),
    provider: Optional[str] = Query(None, description="Фильтр по провайдеру"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Поиск моделей по запросу.
    
    Args:
        q: Поисковый запрос
        provider: Фильтр по провайдеру
        
    Returns:
        Dict[str, Any]: Найденные модели
    """
    try:
        models = await manager.search_models(query=q, provider=provider)
        return {
            "success": True,
            "query": q,
            "provider_filter": provider,
            "models": models,
            "total_found": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска моделей: {str(e)}")


@router.post("/chat/completions", summary="Генерация текста")
async def chat_completions(
    request: ChatRequest,
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Выполнить генерацию текста с помощью указанной модели.
    
    Args:
        request: Запрос для генерации текста
        
    Returns:
        Dict[str, Any]: Ответ от модели
    """
    try:
        response, response_time = await manager.chat_completion(request)
        
        return {
            "success": True,
            "response": response.dict(),
            "response_time_ms": response_time
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.get("/statistics", summary="Статистика использования")
async def get_statistics(manager: ProvidersManager = Depends(get_manager)) -> Dict[str, Any]:
    """
    Получить статистику использования моделей и провайдеров.
    
    Returns:
        Dict[str, Any]: Статистика использования
    """
    try:
        stats = await manager.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@router.get("/cache/info", summary="Информация о кэше")
async def get_cache_info(manager: ProvidersManager = Depends(get_manager)) -> Dict[str, Any]:
    """
    Получить информацию о состоянии кэша.
    
    Returns:
        Dict[str, Any]: Информация о кэше
    """
    try:
        cache_info = await manager.get_cache_info()
        return {
            "success": True,
            "cache": cache_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о кэше: {str(e)}")


@router.delete("/cache", summary="Очистить кэш")
async def clear_cache(
    provider: Optional[str] = Query(None, description="Провайдер для очистки"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Очистить кэш моделей.
    
    Args:
        provider: Конкретный провайдер для очистки (если не указан - очистить весь кэш)
        
    Returns:
        Dict[str, Any]: Результат операции
    """
    try:
        await manager.clear_cache(provider=provider)
        return {
            "success": True,
            "message": f"Кэш {'для ' + provider if provider else 'полностью'} очищен"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")


@router.post("/models/refresh", summary="Обновить модели")
async def refresh_models(
    provider: Optional[str] = Query(None, description="Провайдер для обновления"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Принудительно обновить список моделей.
    
    Args:
        provider: Конкретный провайдер для обновления (если не указан - обновить все)
        
    Returns:
        Dict[str, Any]: Результат обновления
    """
    try:
        result = await manager.refresh_models(provider=provider)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления моделей: {str(e)}")


@router.get("/health", summary="Проверка состояния сервиса")
async def health_check(manager: ProvidersManager = Depends(get_manager)) -> Dict[str, Any]:
    """
    Проверить состояние сервиса и всех провайдеров.
    
    Returns:
        Dict[str, Any]: Состояние сервиса
    """
    try:
        providers = await manager.get_all_providers()
        
        # Подсчитываем доступные провайдеры
        available_providers = sum(1 for p in providers.values() if p.get("available", False))
        
        return {
            "success": True,
            "status": "healthy",
            "providers": {
                "total": len(providers),
                "available": available_providers,
                "unavailable": len(providers) - available_providers
            },
            "cache": await manager.get_cache_info()
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }


# Прямые эндпоинты для провайдеров
@router.get("/{provider_name}/models", summary="Получить модели конкретного провайдера")
async def get_provider_models(
    provider_name: str,
    use_cache: bool = Query(True, description="Использовать кэш"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Получить модели конкретного провайдера.
    
    Args:
        provider_name: Имя провайдера
        use_cache: Использовать кэшированные данные
        
    Returns:
        Dict[str, Any]: Модели провайдера
    """
    try:
        all_models = await manager.get_models_by_provider(use_cache=use_cache)
        
        if provider_name not in all_models:
            raise HTTPException(status_code=404, detail=f"Провайдер {provider_name} не найден")
        
        return {
            "success": True,
            "provider": provider_name,
            "models": all_models[provider_name],
            "total_models": len(all_models[provider_name])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей провайдера {provider_name}: {str(e)}")


@router.post("/{provider_name}/chat/completions", summary="Генерация текста через конкретного провайдера")
async def provider_chat_completions(
    provider_name: str,
    request: ChatRequest,
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Выполнить генерацию текста через конкретного провайдера.
    
    Args:
        provider_name: Имя провайдера
        request: Запрос для генерации текста
        
    Returns:
        Dict[str, Any]: Ответ от модели
    """
    try:
        # Проверяем, что провайдер существует
        providers = await manager.get_all_providers()
        if provider_name not in providers:
            raise HTTPException(status_code=404, detail=f"Провайдер {provider_name} не найден")
        
        if not providers[provider_name].get("available", False):
            raise HTTPException(status_code=503, detail=f"Провайдер {provider_name} недоступен")
        
        # Проверяем, что модель принадлежит этому провайдеру
        provider_models = await manager.get_models_by_provider()
        if provider_name not in provider_models:
            raise HTTPException(status_code=404, detail=f"Модели провайдера {provider_name} не найдены")
        
        model_ids = [model["id"] for model in provider_models[provider_name]]
        if request.model not in model_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Модель {request.model} не принадлежит провайдеру {provider_name}"
            )
        
        # Выполняем запрос
        response, response_time = await manager.chat_completion(request)
        
        return {
            "success": True,
            "provider": provider_name,
            "response": response.dict(),
            "response_time_ms": response_time
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации через {provider_name}: {str(e)}")


@router.get("/{provider_name}/status", summary="Статус конкретного провайдера")
async def get_provider_status(
    provider_name: str,
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Получить детальный статус конкретного провайдера.
    
    Args:
        provider_name: Имя провайдера
        
    Returns:
        Dict[str, Any]: Статус провайдера
    """
    try:
        providers = await manager.get_all_providers()
        
        if provider_name not in providers:
            raise HTTPException(status_code=404, detail=f"Провайдер {provider_name} не найден")
        
        provider_info = providers[provider_name]
        
        # Получаем дополнительную информацию
        models = await manager.get_models_by_provider()
        provider_models = models.get(provider_name, [])
        
        # Получаем статистику
        stats = await manager.get_statistics()
        provider_stats = None
        for provider_stat in stats["statistics"].get("popular_providers", []):
            if provider_stat["provider_name"] == provider_name:
                provider_stats = provider_stat
                break
        
        return {
            "success": True,
            "provider": provider_name,
            "info": provider_info,
            "models_count": len(provider_models),
            "statistics": provider_stats,
            "endpoints": {
                "models": f"/{provider_name}/models",
                "chat": f"/{provider_name}/chat/completions",
                "status": f"/{provider_name}/status"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса провайдера {provider_name}: {str(e)}")


@router.get("/{provider_name}/models/search", summary="Поиск моделей у конкретного провайдера")
async def search_provider_models(
    provider_name: str,
    q: str = Query(..., description="Поисковый запрос"),
    manager: ProvidersManager = Depends(get_manager)
) -> Dict[str, Any]:
    """
    Поиск моделей у конкретного провайдера.
    
    Args:
        provider_name: Имя провайдера
        q: Поисковый запрос
        
    Returns:
        Dict[str, Any]: Найденные модели
    """
    try:
        models = await manager.search_models(query=q, provider=provider_name)
        
        return {
            "success": True,
            "provider": provider_name,
            "query": q,
            "models": models,
            "total_found": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска моделей у провайдера {provider_name}: {str(e)}")