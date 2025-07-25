"""
Провайдер для Cody.su API.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from .base import BaseProvider, ProviderInfo, ModelInfo, ChatRequest, ChatResponse
from ai_api_server.modules.key_manager import APIKeyManager


class CodyProvider(BaseProvider):
    """Провайдер для Cody.su API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация Cody провайдера.
        
        Args:
            config: Конфигурация провайдера
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://cody.su/api/v1")
        self.fetch_models_dynamically = config.get("fetch_models_dynamically", True)
        self._cached_models: Optional[List[ModelInfo]] = None
        self.key_manager = APIKeyManager()
    
    def get_provider_info(self) -> ProviderInfo:
        """Получить информацию о провайдере Cody.su."""
        return ProviderInfo(
            name="cody",
            display_name="Cody.su",
            description="Бесплатное безлимитное API для AI моделей с поддержкой текста, изображений и аудио",
            version="1.0.0",
            enabled=self.config.get("enabled", True) and self.is_available(),
            models=[]  # Модели будут загружены динамически
        )
    
    async def fetch_models_from_api(self) -> List[ModelInfo]:
        """
        Получить список моделей из Cody.su API.
        
        Returns:
            List[ModelInfo]: Список моделей
        """
        if not self.is_available():
            return []
        
        try:
            client = await self.get_client()
            models_response = await client.models.list()
            
            models = []
            for model in models_response.data:
                # Определяем дополнительную информацию о модели
                model_info = self._get_model_details(model.id)
                
                models.append(ModelInfo(
                    id=model.id,
                    name=model_info.get("name", model.id),
                    description=model_info.get("description", f"Модель Cody.su: {model.id}"),
                    context_length=model_info.get("context_length"),
                    input_cost_per_token=model_info.get("input_cost_per_token", 0.0),  # Бесплатно
                    output_cost_per_token=model_info.get("output_cost_per_token", 0.0),  # Бесплатно
                    supports_streaming=model_info.get("supports_streaming", True),
                    supports_function_calling=model_info.get("supports_function_calling", False)
                ))
            
            return models
            
        except Exception as e:
            print(f"Ошибка получения моделей Cody.su: {e}")
            # Возвращаем пустой список вместо fallback моделей, чтобы избежать проблем с event loop
            return []
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """Получить список моделей по умолчанию если API недоступен."""
        fallback_models = [
            # Текстовые модели
            ModelInfo(
                id="gpt-4.1",
                name="GPT-4.1",
                description="Улучшенная версия GPT-4 через Cody.su",
                context_length=128000,
                input_cost_per_token=0.0,
                output_cost_per_token=0.0,
                supports_streaming=True,
                supports_function_calling=True
            )
        ]
        
        return fallback_models
    
    def _get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Получить детальную информацию о модели.
        
        Args:
            model_id: ID модели
            
        Returns:
            Dict[str, Any]: Детальная информация
        """
        # Базовая информация о моделях Cody.su
        model_details = {
            "gpt-4.1": {
                "name": "GPT-4.1",
                "description": "Улучшенная версия GPT-4 через Cody.su",
                "context_length": 128000,
                "input_cost_per_token": 0.0,
                "output_cost_per_token": 0.0,
                "supports_streaming": True,
                "supports_function_calling": True
            }
        }
        
        return model_details.get(model_id, {
            "name": model_id,
            "description": f"Модель Cody.su: {model_id}",
            "context_length": None,
            "input_cost_per_token": 0.0,
            "output_cost_per_token": 0.0,
            "supports_streaming": True,
            "supports_function_calling": False
        })
    
    async def _get_models_impl(self) -> List[ModelInfo]:
        """Получить список доступных моделей Cody.su."""
        if self.fetch_models_dynamically:
            models = await self.fetch_models_from_api()
            # Если не удалось получить модели из API, используем fallback
            if not models:
                return self._get_fallback_models()
            return models
        else:
            return self._get_fallback_models()
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Выполнить генерацию текста через Cody.su API.
        
        Args:
            request: Запрос для генерации
            
        Returns:
            ChatResponse: Ответ от модели
        """
        if not await self.validate_model(request.model):
            raise ValueError(f"Модель {request.model} не поддерживается")
        
        client = await self.get_client()
        
        # Подготовка сообщений
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Параметры запроса
        params = {
            "model": request.model,
            "messages": messages,
            "stream": request.stream
        }
        
        if request.max_tokens:
            params["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            params["temperature"] = request.temperature
        
        # Выполнение запроса
        response = await client.chat.completions.create(**params)
        
        # Обработка ответа
        choice = response.choices[0]
        
        return ChatResponse(
            id=response.id,
            model=response.model,
            content=choice.message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            } if response.usage else None,
            finish_reason=choice.finish_reason
        )
    
    def is_available(self) -> bool:
        """Проверить доступность Cody.su провайдера."""
        try:
            # Простая проверка - есть ли ключи для провайдера
            return "cody" in self.key_manager.keys and len(self.key_manager.keys["cody"]) > 0
        except Exception:
            return False
    
    async def _create_client(self) -> AsyncOpenAI:
        """Создать клиент Cody.su."""
        # Получаем ключ через key_manager
        try:
            key_result = await self.key_manager.get_api_key("cody")
            if not key_result:
                raise ValueError("Cody.su API ключ не найден")
            
            api_key, key_info = key_result
            return AsyncOpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
        except Exception as e:
            raise ValueError(f"Ошибка создания клиента Cody.su: {e}")
    
    async def generate_api_key(self) -> Optional[str]:
        """
        Сгенерировать новый API ключ для Cody.su.
        
        Returns:
            Optional[str]: Новый API ключ или None при ошибке
        """
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post("https://cody.su/api/v1/get_api_key")
                response.raise_for_status()
                
                # API возвращает ключ в виде текста
                api_key = response.text.strip()
                return api_key
                
        except Exception as e:
            print(f"Ошибка генерации API ключа Cody.su: {e}")
            return None