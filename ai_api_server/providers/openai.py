"""
Провайдер для OpenAI API.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from .base import BaseProvider, ProviderInfo, ModelInfo, ChatRequest, ChatResponse
from ai_api_server.modules.key_manager import APIKeyManager


class OpenAIProvider(BaseProvider):
    """Провайдер для OpenAI API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация OpenAI провайдера.
        
        Args:
            config: Конфигурация провайдера
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.fetch_models_dynamically = config.get("fetch_models_dynamically", True)
        self._cached_models: Optional[List[ModelInfo]] = None
        self.key_manager = APIKeyManager()
    
    def get_provider_info(self) -> ProviderInfo:
        """Получить информацию о провайдере OpenAI."""
        return ProviderInfo(
            name="openai",
            display_name="OpenAI",
            description="Провайдер для работы с моделями OpenAI (GPT-4, GPT-3.5-turbo и др.)",
            version="1.0.0",
            enabled=self.config.get("enabled", True) and self.is_available(),
            models=[]  # Модели будут загружены динамически
        )
    
    async def fetch_models_from_api(self) -> List[ModelInfo]:
        """
        Получить список моделей из OpenAI API.
        
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
                    description=model_info.get("description", f"Модель OpenAI: {model.id}"),
                    context_length=model_info.get("context_length"),
                    input_cost_per_token=model_info.get("input_cost_per_token"),
                    output_cost_per_token=model_info.get("output_cost_per_token"),
                    supports_streaming=model_info.get("supports_streaming", True),
                    supports_function_calling=model_info.get("supports_function_calling", False)
                ))
            
            return models
            
        except Exception as e:
            print(f"Ошибка получения моделей OpenAI: {e}")
            return []
    
    def _get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Получить детальную информацию о модели.
        
        Args:
            model_id: ID модели
            
        Returns:
            Dict[str, Any]: Детальная информация
        """
        # Базовая информация о популярных моделях OpenAI
        model_details = {
            "gpt-4": {
                "name": "GPT-4",
                "description": "Самая мощная модель GPT-4",
                "context_length": 8192,
                "input_cost_per_token": 0.00003,
                "output_cost_per_token": 0.00006,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "description": "Улучшенная версия GPT-4 с большим контекстом",
                "context_length": 128000,
                "input_cost_per_token": 0.00001,
                "output_cost_per_token": 0.00003,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "gpt-4-turbo-preview": {
                "name": "GPT-4 Turbo Preview",
                "description": "Предварительная версия GPT-4 Turbo",
                "context_length": 128000,
                "input_cost_per_token": 0.00001,
                "output_cost_per_token": 0.00003,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "description": "Быстрая и эффективная модель для большинства задач",
                "context_length": 4096,
                "input_cost_per_token": 0.0000015,
                "output_cost_per_token": 0.000002,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "gpt-3.5-turbo-16k": {
                "name": "GPT-3.5 Turbo 16K",
                "description": "GPT-3.5 Turbo с увеличенным контекстом",
                "context_length": 16384,
                "input_cost_per_token": 0.000003,
                "output_cost_per_token": 0.000004,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "dall-e-3": {
                "name": "DALL-E 3",
                "description": "Генератор изображений DALL-E 3",
                "context_length": None,
                "input_cost_per_token": None,
                "output_cost_per_token": None,
                "supports_streaming": False,
                "supports_function_calling": False
            },
            "dall-e-2": {
                "name": "DALL-E 2",
                "description": "Генератор изображений DALL-E 2",
                "context_length": None,
                "input_cost_per_token": None,
                "output_cost_per_token": None,
                "supports_streaming": False,
                "supports_function_calling": False
            },
            "whisper-1": {
                "name": "Whisper",
                "description": "Модель распознавания речи",
                "context_length": None,
                "input_cost_per_token": None,
                "output_cost_per_token": None,
                "supports_streaming": False,
                "supports_function_calling": False
            },
            "text-embedding-ada-002": {
                "name": "Text Embedding Ada 002",
                "description": "Модель для создания эмбеддингов текста",
                "context_length": 8191,
                "input_cost_per_token": 0.0000001,
                "output_cost_per_token": None,
                "supports_streaming": False,
                "supports_function_calling": False
            }
        }
        
        return model_details.get(model_id, {
            "name": model_id,
            "description": f"Модель OpenAI: {model_id}",
            "context_length": None,
            "input_cost_per_token": None,
            "output_cost_per_token": None,
            "supports_streaming": True,
            "supports_function_calling": False
        })
    
    async def _get_models_impl(self) -> List[ModelInfo]:
        """Получить список доступных моделей OpenAI."""
        if self.fetch_models_dynamically:
            return await self.fetch_models_from_api()
        else:
            # Возвращаем статический список, если динамическое получение отключено
            return await self.fetch_models_from_api()
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Выполнить генерацию текста через OpenAI API.
        
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
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None,
            finish_reason=choice.finish_reason
        )
    
    def is_available(self) -> bool:
        """Проверить доступность OpenAI провайдера."""
        try:
            # Простая проверка - есть ли ключи для провайдера
            return "openai" in self.key_manager.keys and len(self.key_manager.keys["openai"]) > 0
        except Exception:
            return False
    
    async def _create_client(self) -> AsyncOpenAI:
        """Создать клиент OpenAI."""
        # Получаем ключ через key_manager
        try:
            key_result = await self.key_manager.get_api_key("openai")
            if not key_result:
                raise ValueError("OpenAI API ключ не найден")
            
            api_key, key_info = key_result
            return AsyncOpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
        except Exception as e:
            raise ValueError(f"Ошибка создания клиента OpenAI: {e}")