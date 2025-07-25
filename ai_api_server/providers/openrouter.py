"""
Провайдер для OpenRouter API.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from .base import BaseProvider, ProviderInfo, ModelInfo, ChatRequest, ChatResponse
from ai_api_server.modules.key_manager import APIKeyManager


class OpenRouterProvider(BaseProvider):
    """Провайдер для OpenRouter API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация OpenRouter провайдера.
        
        Args:
            config: Конфигурация провайдера
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.fetch_models_dynamically = config.get("fetch_models_dynamically", True)
        self._cached_models: Optional[List[ModelInfo]] = None
        self.key_manager = APIKeyManager()
    
    def get_provider_info(self) -> ProviderInfo:
        """Получить информацию о провайдере OpenRouter."""
        return ProviderInfo(
            name="openrouter",
            display_name="OpenRouter",
            description="Доступ к бесплатным AI моделям через OpenRouter API (только модели с суффиксом :free)",
            version="1.0.0",
            enabled=self.config.get("enabled", True) and self.is_available(),
            models=[]  # Модели будут загружены динамически
        )
    
    async def fetch_models_from_api(self) -> List[ModelInfo]:
        """
        Получить список моделей из OpenRouter API.
        
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
                # Фильтруем только бесплатные модели с суффиксом :free
                if self._is_free_model(model.id):
                    model_info = self._get_model_details(model.id)
                    
                    models.append(ModelInfo(
                        id=model.id,
                        name=model_info.get("name", model.id),
                        description=model_info.get("description", f"Бесплатная модель OpenRouter: {model.id}"),
                        context_length=model_info.get("context_length"),
                        input_cost_per_token=0.0,  # Бесплатные модели
                        output_cost_per_token=0.0,  # Бесплатные модели
                        supports_streaming=model_info.get("supports_streaming", True),
                        supports_function_calling=model_info.get("supports_function_calling", False)
                    ))
            
            return models
            
        except Exception as e:
            print(f"Ошибка получения моделей OpenRouter: {e}")
            # Возвращаем пустой список, так как получаем модели только онлайн
            return []
    
    def _is_free_model(self, model_id: str) -> bool:
        """
        Проверить, является ли модель бесплатной (с суффиксом :free).
        
        Args:
            model_id: ID модели
            
        Returns:
            bool: True если модель бесплатная
        """
        return model_id.endswith(":free")
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """Получить список моделей по умолчанию (не используется, так как получаем только онлайн)."""
        return []
    
    def _get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Получить детальную информацию о модели.
        
        Args:
            model_id: ID модели
            
        Returns:
            Dict[str, Any]: Детальная информация
        """
        # Базовая информация о популярных моделях OpenRouter
        model_details = {
            "openai/gpt-4-turbo": {
                "name": "GPT-4 Turbo (OpenRouter)",
                "description": "GPT-4 Turbo через OpenRouter",
                "context_length": 128000,
                "input_cost_per_token": 0.00001,
                "output_cost_per_token": 0.00003,
                "supports_streaming": True,
                "supports_function_calling": True
            }
        }
        
        return model_details.get(model_id, {
            "name": model_id,
            "description": f"Бесплатная модель OpenRouter: {model_id}",
            "context_length": None,
            "input_cost_per_token": 0.0,
            "output_cost_per_token": 0.0,
            "supports_streaming": True,
            "supports_function_calling": False
        })
    
    async def _get_models_impl(self) -> List[ModelInfo]:
        """Получить список доступных моделей OpenRouter (только онлайн)."""
        return await self.fetch_models_from_api()
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Выполнить генерацию текста через OpenRouter API.
        
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
        """Проверить доступность OpenRouter провайдера."""
        status = self.key_manager.get_provider_status("openrouter")
        return status["available"]
    
    async def _create_client(self) -> AsyncOpenAI:
        """Создать клиент OpenRouter."""
        # Получаем ключ через key_manager
        try:
            key_result = await self.key_manager.get_api_key("openrouter")
            if not key_result:
                raise ValueError("OpenRouter API ключ не найден")
            
            api_key, key_info = key_result
            return AsyncOpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
        except Exception as e:
            raise ValueError(f"Ошибка создания клиента OpenRouter: {e}")