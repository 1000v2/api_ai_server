"""
Система кэширования моделей.
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiofiles
from ai_api_server.providers.base import ModelInfo


class ModelCache:
    """Менеджер кэширования моделей."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация кэша моделей.
        
        Args:
            config: Конфигурация кэша
        """
        self.config = config
        self.cache_file = config.get("cache_file", "data/models_cache.json")
        self.update_interval_hours = config.get("update_interval_hours", 24)
        self.enabled = config.get("enabled", True)
        self.force_update_on_startup = config.get("force_update_on_startup", False)
        
        # Создаем директорию если не существует
        cache_dir = Path(self.cache_file).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache_data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def load_cache(self) -> Dict[str, Any]:
        """
        Загрузить кэш из файла.
        
        Returns:
            Dict[str, Any]: Данные кэша
        """
        if not self.enabled:
            return {}
        
        async with self._lock:
            try:
                if os.path.exists(self.cache_file):
                    async with aiofiles.open(self.cache_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        self._cache_data = json.loads(content)
                else:
                    self._cache_data = {
                        "last_updated": None,
                        "providers": {}
                    }
            except Exception as e:
                print(f"Ошибка загрузки кэша: {e}")
                self._cache_data = {
                    "last_updated": None,
                    "providers": {}
                }
        
        return self._cache_data
    
    async def save_cache(self) -> None:
        """Сохранить кэш в файл."""
        if not self.enabled:
            return
        
        async with self._lock:
            try:
                async with aiofiles.open(self.cache_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self._cache_data, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Ошибка сохранения кэша: {e}")
    
    def is_cache_expired(self) -> bool:
        """
        Проверить, истек ли срок действия кэша.
        
        Returns:
            bool: True если кэш истек
        """
        if not self.enabled:
            return True
        
        if self.force_update_on_startup:
            return True
        
        last_updated = self._cache_data.get("last_updated")
        if not last_updated:
            return True
        
        try:
            last_update_time = datetime.fromisoformat(last_updated)
            expiry_time = last_update_time + timedelta(hours=self.update_interval_hours)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    async def get_cached_models(self, provider_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получить кэшированные модели для провайдера.
        
        Args:
            provider_name: Имя провайдера
            
        Returns:
            Optional[List[Dict[str, Any]]]: Список моделей или None
        """
        if not self.enabled or self.is_cache_expired():
            return None
        
        return self._cache_data.get("providers", {}).get(provider_name, {}).get("models")
    
    async def cache_models(self, provider_name: str, models: List[ModelInfo]) -> None:
        """
        Кэшировать модели провайдера.
        
        Args:
            provider_name: Имя провайдера
            models: Список моделей
        """
        if not self.enabled:
            return
        
        # Конвертируем ModelInfo в словари
        models_data = []
        for model in models:
            model_dict = model.dict()
            models_data.append(model_dict)
        
        # Обновляем кэш
        if "providers" not in self._cache_data:
            self._cache_data["providers"] = {}
        
        self._cache_data["providers"][provider_name] = {
            "models": models_data,
            "cached_at": datetime.now().isoformat()
        }
        
        self._cache_data["last_updated"] = datetime.now().isoformat()
        
        # Сохраняем в файл
        await self.save_cache()
    
    async def clear_cache(self, provider_name: Optional[str] = None) -> None:
        """
        Очистить кэш.
        
        Args:
            provider_name: Имя провайдера для очистки (если None - очистить весь кэш)
        """
        async with self._lock:
            if provider_name:
                if "providers" in self._cache_data and provider_name in self._cache_data["providers"]:
                    del self._cache_data["providers"][provider_name]
            else:
                self._cache_data = {
                    "last_updated": None,
                    "providers": {}
                }
        
        await self.save_cache()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Получить информацию о кэше.
        
        Returns:
            Dict[str, Any]: Информация о кэше
        """
        return {
            "enabled": self.enabled,
            "cache_file": self.cache_file,
            "update_interval_hours": self.update_interval_hours,
            "last_updated": self._cache_data.get("last_updated"),
            "is_expired": self.is_cache_expired(),
            "providers_count": len(self._cache_data.get("providers", {})),
            "total_models": sum(
                len(provider_data.get("models", []))
                for provider_data in self._cache_data.get("providers", {}).values()
            )
        }