"""
Провайдер для Google Gemini API.
"""

import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .base import BaseProvider, ProviderInfo, ModelInfo, ChatRequest, ChatResponse
from ai_api_server.modules.key_manager import APIKeyManager


class GeminiProvider(BaseProvider):
    """Провайдер для Google Gemini API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация Gemini провайдера.
        
        Args:
            config: Конфигурация провайдера
        """
        super().__init__(config)
        self.fetch_models_dynamically = config.get("fetch_models_dynamically", True)
        self._cached_models: Optional[List[ModelInfo]] = None
        self.key_manager = APIKeyManager()
        
        # API ключ будет настроен при первом использовании
    

    
    def get_provider_info(self) -> ProviderInfo:
        """Получить информацию о провайдере Gemini."""
        return ProviderInfo(
            name="gemini",
            display_name="Google Gemini",
            description="Провайдер для работы с моделями Google Gemini",
            version="1.0.0",
            enabled=self.config.get("enabled", True) and self.is_available(),
            models=[]  # Модели будут загружены динамически
        )
    
    async def fetch_models_from_api(self) -> List[ModelInfo]:
        """
        Получить список моделей из Gemini API.
        
        Returns:
            List[ModelInfo]: Список моделей
        """
        if not self.is_available():
            return []
        
        try:
            # Получаем список моделей
            models_list = genai.list_models()
            
            models = []
            for model in models_list:
                # Определяем дополнительную информацию о модели
                model_info = self._get_model_details(model.name)
                
                models.append(ModelInfo(
                    id=model.name,
                    name=model_info.get("display_name", model.display_name or model.name),
                    description=model_info.get("description", model.description or f"Модель Google Gemini: {model.name}"),
                    context_length=model_info.get("context_length"),
                    input_cost_per_token=model_info.get("input_cost_per_token"),
                    output_cost_per_token=model_info.get("output_cost_per_token"),
                    supports_streaming=model_info.get("supports_streaming", True),
                    supports_function_calling=model_info.get("supports_function_calling", False)
                ))
            
            return models
            
        except Exception as e:
            print(f"Ошибка получения моделей Gemini: {e}")
            return []
    
    def _get_model_details(self, model_name: str) -> Dict[str, Any]:
        """
        Получить детальную информацию о модели.
        
        Args:
            model_name: Имя модели
            
        Returns:
            Dict[str, Any]: Детальная информация
        """
        # Базовая информация о моделях Gemini
        model_details = {
            "models/gemini-pro": {
                "display_name": "Gemini Pro",
                "description": "Мощная модель для текстовых задач",
                "context_length": 32768,
                "input_cost_per_token": 0.00000025,
                "output_cost_per_token": 0.0000005,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "models/gemini-pro-vision": {
                "display_name": "Gemini Pro Vision",
                "description": "Модель для работы с текстом и изображениями",
                "context_length": 16384,
                "input_cost_per_token": 0.00000025,
                "output_cost_per_token": 0.0000005,
                "supports_streaming": True,
                "supports_function_calling": False
            },
            "models/gemini-1.5-pro": {
                "display_name": "Gemini 1.5 Pro",
                "description": "Улучшенная версия Gemini Pro с большим контекстом",
                "context_length": 1048576,  # 1M токенов
                "input_cost_per_token": 0.00000125,
                "output_cost_per_token": 0.00000375,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "models/gemini-1.5-flash": {
                "display_name": "Gemini 1.5 Flash",
                "description": "Быстрая версия Gemini 1.5 для простых задач",
                "context_length": 1048576,  # 1M токенов
                "input_cost_per_token": 0.000000075,
                "output_cost_per_token": 0.0000003,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "models/embedding-001": {
                "display_name": "Text Embedding 001",
                "description": "Модель для создания эмбеддингов текста",
                "context_length": 2048,
                "input_cost_per_token": 0.0000001,
                "output_cost_per_token": None,
                "supports_streaming": False,
                "supports_function_calling": False
            }
        }
        
        return model_details.get(model_name, {
            "display_name": model_name.split("/")[-1] if "/" in model_name else model_name,
            "description": f"Модель Google Gemini: {model_name}",
            "context_length": None,
            "input_cost_per_token": None,
            "output_cost_per_token": None,
            "supports_streaming": True,
            "supports_function_calling": False
        })
    
    async def _get_models_impl(self) -> List[ModelInfo]:
        """Получить список доступных моделей Gemini."""
        if self.fetch_models_dynamically:
            return await self.fetch_models_from_api()
        else:
            # Возвращаем статический список, если динамическое получение отключено
            return await self.fetch_models_from_api()
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Выполнить генерацию текста через Gemini API.
        
        Args:
            request: Запрос для генерации
            
        Returns:
            ChatResponse: Ответ от модели
        """
        if not await self.validate_model(request.model):
            raise ValueError(f"Модель {request.model} не поддерживается")
        
        try:
            # Создаем модель
            model = genai.GenerativeModel(request.model)
            
            # Подготавливаем сообщения
            # Gemini использует другой формат, конвертируем
            conversation_history = []
            for msg in request.messages:
                if msg.role == "user":
                    conversation_history.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "assistant":
                    conversation_history.append({"role": "model", "parts": [msg.content]})
                # system сообщения обрабатываются отдельно
            
            # Настройки генерации
            generation_config = {}
            if request.max_tokens:
                generation_config["max_output_tokens"] = request.max_tokens
            if request.temperature is not None:
                generation_config["temperature"] = request.temperature
            
            # Выполняем запрос
            if len(conversation_history) == 1 and conversation_history[0]["role"] == "user":
                # Простой запрос
                response = model.generate_content(
                    conversation_history[0]["parts"][0],
                    generation_config=generation_config if generation_config else None
                )
            else:
                # Диалог
                chat = model.start_chat(history=conversation_history[:-1])
                response = chat.send_message(
                    conversation_history[-1]["parts"][0],
                    generation_config=generation_config if generation_config else None
                )
            
            # Обработка ответа
            content = response.text if hasattr(response, 'text') else str(response)
            
            # Подсчет токенов (приблизительно)
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return ChatResponse(
                id=f"gemini-{hash(content)}",  # Gemini не возвращает ID
                model=request.model,
                content=content,
                usage=usage,
                finish_reason="stop"
            )
            
        except Exception as e:
            raise Exception(f"Ошибка Gemini API: {str(e)}")
    
    def is_available(self) -> bool:
        """Проверить доступность Gemini провайдера."""
        try:
            # Простая проверка - есть ли ключи для провайдера
            return "gemini" in self.key_manager.keys and len(self.key_manager.keys["gemini"]) > 0
        except Exception:
            return False
    
    async def _create_client(self):
        """Создать клиент Gemini (не используется, так как используется глобальная конфигурация)."""
        # Получаем ключ через key_manager
        try:
            key_result = await self.key_manager.get_api_key("gemini")
            if not key_result:
                raise ValueError("Gemini API ключ не найден")
            
            api_key, key_info = key_result
            genai.configure(api_key=api_key)
            return genai  # Возвращаем модуль как "клиент"
        except Exception as e:
            raise ValueError(f"Ошибка создания клиента Gemini: {e}")