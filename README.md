# AI API Server

Модульный API сервер для работы с различными AI провайдерами с динамическим получением моделей, кэшированием, фильтрацией и статистикой.

## 🚀 Особенности

- **Модульная архитектура** с поддержкой различных AI провайдеров
- **Динамическое получение моделей** из API провайдеров
- **Система кэширования** для быстрого доступа к моделям
- **Фильтрация по категориям** (текст, изображения, код, аудио, эмбеддинги)
- **Статистика использования** с отслеживанием популярности
- **Группировка моделей** по провайдерам
- **REST API** с полной документацией
- **Легко расширяемый** и переиспользуемый в других проектах

## 🏗️ Поддерживаемые провайдеры

- **OpenAI** (GPT-4, GPT-3.5, DALL-E, Whisper, Embeddings)
- **Google Gemini** (Gemini Pro, Gemini Pro Vision, Gemini 1.5)
- **Cody.su** (Бесплатные GPT-4, изображения, аудио) 🆓
- **OpenRouter** (Доступ к множеству моделей через единый API)
- Легко добавить новые провайдеры

## 📁 Структура проекта

```
ai_api_server/
├── providers/          # Модули провайдеров
│   ├── __init__.py
│   ├── base.py        # Базовый абстрактный класс
│   ├── openai.py      # OpenAI провайдер
│   ├── gemini.py      # Google Gemini провайдер
│   ├── cody.py        # Cody.su провайдер
│   └── openrouter.py  # OpenRouter провайдер
├── modules/           # Модули обобщения (фабрика)
│   ├── __init__.py
│   ├── cache.py       # Система кэширования
│   ├── filters.py     # Фильтрация моделей
│   ├── statistics.py  # Статистика использования
│   └── factory.py     # Фабрика провайдеров
├── core/              # Основная логика
│   ├── __init__.py
│   ├── manager.py     # Менеджер провайдеров
│   └── config.py      # Менеджер конфигурации
├── api/               # API эндпоинты
│   ├── __init__.py
│   └── routes.py      # Маршруты API
├── examples/          # Примеры использования
│   └── client_example.py
├── main.py            # Точка входа
├── config.yaml        # Конфигурационный файл
├── .env.example       # Пример переменных окружения
└── requirements.txt   # Зависимости
```

## 🛠️ Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd ai_api_server
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте API ключи:**
Отредактируйте `api_keys.yaml` файл, добавив ваши API ключи:
```yaml
providers:
  openai:
    keys:
      - sk-proj-your_key_here
      - sk-proj-your_backup_key
  cody:
    keys:
      - cody-your_key_here
```

4. **Настройте конфигурацию (опционально):**
Отредактируйте `config.yaml` для настройки провайдеров, кэширования и фильтров.

## 🚀 Запуск

### Запуск сервера
```bash
python -m ai_api_server.main
```

Или:
```bash
cd ai_api_server
python main.py
```

### Запуск с uvicorn
```bash
uvicorn ai_api_server.main:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступен по адресу: http://localhost:8000

## 📚 API Документация

### Основные эндпоинты

- **GET /** - Информация об API
- **GET /api/v1/providers** - Список всех провайдеров
- **GET /api/v1/models** - Модели, сгруппированные по провайдерам
- **GET /api/v1/models/by-category** - Модели по категориям
- **GET /api/v1/models/search** - Поиск моделей
- **POST /api/v1/chat/completions** - Генерация текста
- **GET /api/v1/statistics** - Статистика использования
- **GET /api/v1/health** - Проверка состояния

### Интерактивная документация

После запуска сервера доступна по адресам:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Примеры использования

### Получение списка провайдеров
```bash
curl http://localhost:8000/api/v1/providers
```

### Получение моделей по провайдерам
```bash
curl http://localhost:8000/api/v1/models
```

Ответ:
```json
{
  "success": true,
  "models": {
    "openai": [
      {
        "id": "gpt-4",
        "name": "GPT-4",
        "description": "Самая мощная модель GPT-4",
        "category": "text_generation",
        "context_length": 8192,
        "supports_streaming": true
      }
    ],
    "gemini": [
      {
        "id": "models/gemini-pro",
        "name": "Gemini Pro",
        "description": "Мощная модель для текстовых задач",
        "category": "text_generation",
        "context_length": 32768
      }
    ]
  }
}
```

### Генерация текста
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Привет! Как дела?"}
    ],
    "max_tokens": 100
  }'
```

### Поиск моделей
```bash
curl "http://localhost:8000/api/v1/models/search?q=gpt&provider=openai"
```

### Статистика
```bash
curl http://localhost:8000/api/v1/statistics
```

### Получение API ключей

**OpenAI**: https://platform.openai.com/api-keys
**Gemini**: https://makersuite.google.com/app/apikey
**Cody.su**: Бесплатный ключ через API:
```bash
curl -X POST https://cody.su/api/v1/get_api_key
```
**OpenRouter**: https://openrouter.ai/keys

### Прямые эндпоинты провайдеров
```bash
# Модели конкретного провайдера
curl http://localhost:8000/api/v1/cody/models
curl http://localhost:8000/api/v1/openrouter/models

# Генерация через конкретного провайдера
curl -X POST http://localhost:8000/api/v1/cody/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Статус провайдера
curl http://localhost:8000/api/v1/cody/status
```

## 🐍 Python клиент

```python
import asyncio
from examples.client_example import AIAPIClient

async def main():
    async with AIAPIClient() as client:
        # Получить провайдеры
        providers = await client.get_providers()
        print(providers)
        
        # Получить модели
        models = await client.get_models_by_provider()
        print(models)
        
        # Генерация текста
        response = await client.chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response)

asyncio.run(main())
```

## ⚙️ Конфигурация

### Основные настройки в config.yaml

```yaml
# Настройки кэширования
models_cache:
  enabled: true
  update_interval_hours: 24  # Обновлять каждые 24 часа
  cache_file: "data/models_cache.json"

# Фильтры категорий
model_filters:
  image_generation:
    keywords: ["image", "dall-e", "imagen"]
    category: "image_generation"
  text_generation:
    keywords: ["gpt", "claude", "gemini", "text"]
    category: "text_generation"

# Статистика
statistics:
  enabled: true
  database_file: "data/statistics.db"
  track_usage: true
```

## 🔌 Добавление нового провайдера

1. **Создайте новый файл провайдера:**
```python
# providers/my_provider.py
from .base import BaseProvider, ProviderInfo, ModelInfo

class MyProvider(BaseProvider):
    def get_provider_info(self) -> ProviderInfo:
        # Реализация
        pass
    
    async def get_models(self) -> List[ModelInfo]:
        # Реализация
        pass
    
    # Другие методы...
```

2. **Зарегистрируйте в фабрике:**
```python
# modules/factory.py
from ..providers.my_provider import MyProvider

class ProviderFactory:
    _providers_registry = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "my_provider": MyProvider,  # Добавить здесь
    }
```

3. **Добавьте в конфигурацию:**
```yaml
# config.yaml
providers:
  my_provider:
    enabled: true
    api_key_env: "MY_PROVIDER_API_KEY"
```

## 📊 Мониторинг и статистика

Сервер автоматически отслеживает:
- Количество запросов по провайдерам и моделям
- Время ответа
- Успешность запросов
- Использование токенов
- Популярность моделей

## 🔒 Безопасность

- CORS настройки
- Rate limiting (настраивается)
- API ключи через переменные окружения
- Логирование всех операций

## 🐛 Отладка

Логи сохраняются в `logs/app.log`. Для отладки установите:
```yaml
server:
  debug: true
logging:
  level: "DEBUG"
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.