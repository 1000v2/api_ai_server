"""
Пример использования AI API Server.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class AIAPIClient:
    """Клиент для работы с AI API Server."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        Инициализация клиента.
        
        Args:
            base_url: Базовый URL API сервера
        """
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход."""
        if self.session:
            await self.session.close()
    
    async def get_providers(self) -> Dict[str, Any]:
        """Получить список провайдеров."""
        async with self.session.get(f"{self.base_url}/providers") as response:
            return await response.json()
    
    async def get_models_by_provider(self) -> Dict[str, Any]:
        """Получить модели, сгруппированные по провайдерам."""
        async with self.session.get(f"{self.base_url}/models") as response:
            return await response.json()
    
    async def get_models_by_category(self, category: str = None) -> Dict[str, Any]:
        """Получить модели по категориям."""
        url = f"{self.base_url}/models/by-category"
        if category:
            url += f"?category={category}"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def search_models(self, query: str, provider: str = None) -> Dict[str, Any]:
        """Поиск моделей."""
        url = f"{self.base_url}/models/search?q={query}"
        if provider:
            url += f"&provider={provider}"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def chat_completion(self, model: str, messages: list, **kwargs) -> Dict[str, Any]:
        """Генерация текста."""
        data = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/chat/completions",
            json=data
        ) as response:
            return await response.json()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику."""
        async with self.session.get(f"{self.base_url}/statistics") as response:
            return await response.json()


async def main():
    """Основная функция с примерами использования."""
    
    async with AIAPIClient() as client:
        print("🤖 Примеры использования AI API Server\n")
        
        # 1. Получаем список провайдеров
        print("1️⃣ Получение списка провайдеров:")
        providers = await client.get_providers()
        if providers.get("success"):
            for name, info in providers["providers"].items():
                status = "✅" if info["available"] else "❌"
                print(f"   {status} {info['display_name']} - {info['description']}")
        print()
        
        # 2. Получаем модели по провайдерам
        print("2️⃣ Модели по провайдерам:")
        models_by_provider = await client.get_models_by_provider()
        if models_by_provider.get("success"):
            for provider, models in models_by_provider["models"].items():
                print(f"   📦 {provider.upper()}: {len(models)} моделей")
                for model in models[:3]:  # Показываем первые 3 модели
                    print(f"      - {model['name']} ({model['id']})")
                if len(models) > 3:
                    print(f"      ... и ещё {len(models) - 3} моделей")
        print()
        
        # 3. Получаем модели по категориям
        print("3️⃣ Модели по категориям:")
        models_by_category = await client.get_models_by_category()
        if models_by_category.get("success"):
            for category, models in models_by_category["models"].items():
                print(f"   🏷️ {category}: {len(models)} моделей")
        print()
        
        # 4. Поиск моделей
        print("4️⃣ Поиск моделей (запрос: 'gpt'):")
        search_results = await client.search_models("gpt")
        if search_results.get("success"):
            print(f"   Найдено: {search_results['total_found']} моделей")
            for model in search_results["models"][:3]:
                print(f"   - {model['name']} ({model['id']})")
        print()
        
        # 5. Пример генерации текста (если есть доступные модели)
        print("5️⃣ Пример генерации текста:")
        try:
            # Пробуем найти доступную модель
            available_model = None
            if models_by_provider.get("success"):
                for provider, models in models_by_provider["models"].items():
                    if models:
                        # Ищем текстовую модель
                        for model in models:
                            if any(keyword in model["id"].lower() for keyword in ["gpt", "gemini", "claude"]):
                                available_model = model["id"]
                                break
                        if available_model:
                            break
            
            if available_model:
                print(f"   Используем модель: {available_model}")
                
                response = await client.chat_completion(
                    model=available_model,
                    messages=[
                        {"role": "user", "content": "Привет! Как дела?"}
                    ],
                    max_tokens=100
                )
                
                if response.get("success"):
                    chat_response = response["response"]
                    print(f"   Ответ: {chat_response['content']}")
                    print(f"   Время ответа: {response['response_time_ms']}мс")
                else:
                    print(f"   Ошибка: {response}")
            else:
                print("   ⚠️ Нет доступных моделей для генерации")
        
        except Exception as e:
            print(f"   ❌ Ошибка генерации: {e}")
        print()
        
        # 6. Статистика
        print("6️⃣ Статистика использования:")
        stats = await client.get_statistics()
        if stats.get("success"):
            summary = stats["statistics"]["summary"]
            print(f"   📊 Всего запросов: {summary.get('total_requests', 0)}")
            print(f"   ✅ Успешных: {summary.get('successful_requests', 0)}")
            print(f"   📈 Процент успеха: {summary.get('success_rate', 0):.1f}%")
            print(f"   🔤 Всего токенов: {summary.get('total_tokens', 0)}")
            
            popular_models = stats["statistics"].get("popular_models", [])
            if popular_models:
                print("   🏆 Популярные модели:")
                for model in popular_models[:3]:
                    print(f"      - {model['model_id']} ({model['provider_name']}): {model['usage_count']} использований")
        print()
        
        print("✨ Примеры завершены!")


if __name__ == "__main__":
    asyncio.run(main())