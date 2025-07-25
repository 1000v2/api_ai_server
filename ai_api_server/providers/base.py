"""
Базовый абстрактный класс для AI провайдеров.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Информация о модели."""
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_token: Optional[float] = None
    output_cost_per_token: Optional[float] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False


class ProviderInfo(BaseModel):
    """Информация о провайдере."""
    name: str
    display_name: str
    description: str
    version: str
    enabled: bool
    models: List[ModelInfo]


class ChatMessage(BaseModel):
    """Сообщение в чате."""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """Запрос для генерации текста."""
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Ответ от модели."""
    id: str
    model: str
    content: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class BaseProvider(ABC):
    """Базовый абстрактный класс для AI провайдеров."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация провайдера.
        
        Args:
            config: Конфигурация провайдера
        """
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()
        self._client = None
    
    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        """
        Получить информацию о провайдере.
        
        Returns:
            ProviderInfo: Информация о провайдере
        """
        pass
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Получить список доступных моделей.
        
        Returns:
            List[ModelInfo]: Список моделей или пустой список если недоступно
        """
        try:
            return await self._get_models_impl()
        except Exception as e:
            print(f"Провайдер {self.__class__.__name__} недоступен: {e}")
            return []
    
    @abstractmethod
    async def _get_models_impl(self) -> List[ModelInfo]:
        """
        Реализация получения моделей (должна быть переопределена в подклассах).
        
        Returns:
            List[ModelInfo]: Список моделей
        """
        pass
    
    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Выполнить генерацию текста.
        
        Args:
            request: Запрос для генерации
            
        Returns:
            ChatResponse: Ответ от модели
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверить доступность провайдера.
        
        Returns:
            bool: True если провайдер доступен
        """
        pass
    
    async def get_client(self):
        """
        Получить клиент для работы с API.
        
        Returns:
            Клиент API провайдера
        """
        if self._client is None:
            self._client = await self._create_client()
        return self._client
    
    @abstractmethod
    async def _create_client(self):
        """
        Создать клиент для работы с API.
        
        Returns:
            Клиент API провайдера
        """
        pass
    
    async def validate_model(self, model_id: str) -> bool:
        """
        Проверить поддержку модели.
        
        Args:
            model_id: ID модели
            
        Returns:
            bool: True если модель поддерживается
        """
        models = await self.get_models()
        return any(model.id == model_id for model in models)