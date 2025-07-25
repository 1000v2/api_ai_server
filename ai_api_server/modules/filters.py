"""
Система фильтрации моделей по категориям.
"""

from typing import Dict, List, Any, Optional
from ai_api_server.providers.base import ModelInfo
from ai_api_server.modules.constants import MODEL_CATEGORIES


class ModelFilter:
    """Фильтр для категоризации моделей."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация фильтра моделей.
        
        Args:
            config: Конфигурация фильтров из config.yaml
        """
        # Инициализируем базовые категории
        self.categories = {
            "text_generation": {
                "name": "Генератор текста",
                "description": "Модели для генерации и обработки текста",
                "keywords": ["gpt", "claude", "gemini", "llama", "chat", "completion"],
                "icon": "💬",
                "default": True
            }
        }
        
        if config:
            # Создаем категории из конфигурации config.yaml
            for filter_name, filter_config in config.items():
                category = filter_config.get("category", filter_name)
                keywords = filter_config.get("keywords", [])
                
                self.categories[category] = {
                    "name": filter_config.get("display_name", category.replace("_", " ").title()),
                    "description": filter_config.get("description", f"Категория {category}"),
                    "keywords": [keyword.lower() for keyword in keywords],
                    "icon": filter_config.get("icon", "🔧")
                }
        
        # Нормализуем ключевые слова
        for category_info in self.categories.values():
            category_info["keywords"] = [kw.lower() for kw in category_info["keywords"]]
    
    def _build_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Построить словарь категорий из конфигурации.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь категорий
        """
        # Этот метод теперь не используется, но оставлен для совместимости
        return self.categories
    
    def categorize_model(self, model: ModelInfo) -> str:
        """
        Определить категорию модели.
        
        Args:
            model: Информация о модели
            
        Returns:
            str: Категория модели
        """
        model_name_lower = model.name.lower()
        model_id_lower = model.id.lower()
        model_desc_lower = (model.description or "").lower()
        
        # Проверяем каждую категорию (кроме text_generation)
        for category_name, category_info in self.categories.items():
            if category_name == "text_generation":
                continue  # Пропускаем text_generation, это категория по умолчанию
            
            keywords = category_info["keywords"]
            
            # Проверяем наличие ключевых слов в названии, ID или описании
            for keyword in keywords:
                if (keyword in model_name_lower or
                    keyword in model_id_lower or
                    keyword in model_desc_lower):
                    return category_name
        
        # Если категория не найдена, возвращаем "text_generation" как категорию по умолчанию
        return "text_generation"
    
    def filter_models_by_category(self, models: List[ModelInfo], category: str) -> List[ModelInfo]:
        """
        Фильтровать модели по категории.
        
        Args:
            models: Список моделей
            category: Категория для фильтрации
            
        Returns:
            List[ModelInfo]: Отфильтрованные модели
        """
        if category == "all":
            return models
        
        filtered_models = []
        for model in models:
            model_category = self.categorize_model(model)
            if model_category == category:
                filtered_models.append(model)
        
        return filtered_models
    
    def group_models_by_category(self, models: List[ModelInfo]) -> Dict[str, List[ModelInfo]]:
        """
        Группировать модели по категориям.
        
        Args:
            models: Список моделей
            
        Returns:
            Dict[str, List[ModelInfo]]: Модели, сгруппированные по категориям
        """
        grouped = {}
        
        # Инициализируем все категории
        for category_name in self.categories.keys():
            grouped[category_name] = []
        
        # Добавляем категорию "other"
        grouped["other"] = []
        
        # Группируем модели
        for model in models:
            category = self.categorize_model(model)
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(model)
        
        # Удаляем пустые категории
        return {k: v for k, v in grouped.items() if v}
    
    def get_available_categories(self) -> List[Dict[str, str]]:
        """
        Получить список доступных категорий.
        
        Returns:
            List[Dict[str, str]]: Список категорий с их описаниями
        """
        categories = []
        
        # Добавляем все настроенные категории
        for category_name, category_info in self.categories.items():
            categories.append({
                "id": category_name,
                "name": category_info["name"],
                "keywords": category_info["keywords"]
            })
        
        # Добавляем специальные категории
        categories.extend([
            {
                "id": "all",
                "name": "Все модели",
                "keywords": []
            },
            {
                "id": "other",
                "name": "Прочие",
                "keywords": []
            }
        ])
        
        return categories
    
    def get_model_statistics_by_category(self, models: List[ModelInfo]) -> Dict[str, int]:
        """
        Получить статистику моделей по категориям.
        
        Args:
            models: Список моделей
            
        Returns:
            Dict[str, int]: Количество моделей в каждой категории
        """
        stats = {}
        grouped = self.group_models_by_category(models)
        
        for category, category_models in grouped.items():
            stats[category] = len(category_models)
        
        return stats
    
    def search_models(self, models: List[ModelInfo], query: str) -> List[ModelInfo]:
        """
        Поиск моделей по запросу.
        
        Args:
            models: Список моделей
            query: Поисковый запрос
            
        Returns:
            List[ModelInfo]: Найденные модели
        """
        if not query:
            return models
        
        query_lower = query.lower()
        found_models = []
        
        for model in models:
            # Поиск в названии, ID и описании
            if (query_lower in model.name.lower() or
                query_lower in model.id.lower() or
                (model.description and query_lower in model.description.lower())):
                found_models.append(model)
        
        return found_models