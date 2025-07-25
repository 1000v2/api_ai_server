"""
Главный файл AI API Server.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_api_server.core.config import ConfigManager
from ai_api_server.core.manager import ProvidersManager
from ai_api_server.api.routes import router, set_manager

# Глобальные переменные
config_manager: ConfigManager = None
providers_manager: ProvidersManager = None


def setup_logging(config: ConfigManager) -> None:
    """Настроить логирование."""
    logging_config = config.get_logging_config()
    
    # Создаем директорию для логов
    log_file = logging_config.get("file", "logs/app.log")
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Настраиваем логирование
    logging.basicConfig(
        level=getattr(logging, logging_config.get("level", "INFO")),
        format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    global config_manager, providers_manager
    
    # Инициализация при запуске
    print("🚀 Запуск AI API Server...")
    
    # Загружаем конфигурацию
    config_manager = ConfigManager()
    config_manager.ensure_directories()
    
    # Настраиваем логирование
    setup_logging(config_manager)
    logger = logging.getLogger(__name__)
    
    logger.info("🔧 Инициализация AI API Server")
    
    # Создаем менеджер провайдеров
    logger.info("📦 Создание менеджера провайдеров...")
    providers_manager = ProvidersManager(config_manager.config)
    
    logger.info("🔑 Инициализация менеджера ключей...")
    await providers_manager.initialize()
    
    logger.info("🤖 Инициализация AI провайдеров...")
    # Устанавливаем менеджер в роутах
    set_manager(providers_manager)
    
    # Логируем информацию о провайдерах
    providers_info = await providers_manager.get_all_providers()
    for name, info in providers_info.items():
        status = "✅ доступен" if info["available"] else "❌ недоступен"
        logger.info(f"   {name}: {status}")
    
    logger.info("✅ AI API Server успешно инициализирован")
    print("✅ AI API Server готов к работе!")
    
    yield
    
    # Очистка при завершении
    logger.info("🛑 Завершение работы AI API Server")
    print("👋 AI API Server завершает работу...")


def create_app() -> FastAPI:
    """Создать экземпляр FastAPI приложения."""
    app = FastAPI(
        title="AI API Server",
        description="Модульный API сервер для работы с различными AI провайдерами",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Настройка CORS
    if config_manager:
        security_config = config_manager.get_security_config()
        cors_origins = security_config.get("cors_origins", ["*"])
    else:
        cors_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключаем роуты
    app.include_router(router, prefix="/api/v1")
    
    return app


# Создаем приложение
app = create_app()


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "AI API Server",
        "version": "1.0.0",
        "status": "running",
        "api_docs": "/docs",
        "api_base": "/api/v1"
    }


@app.get("/health")
async def health():
    """Простая проверка здоровья."""
    return {"status": "healthy", "service": "AI API Server"}


if __name__ == "__main__":
    import uvicorn
    
    # Загружаем конфигурацию для получения настроек сервера
    temp_config = ConfigManager()
    server_config = temp_config.get_server_config()
    
    # Запускаем сервер
    uvicorn.run(
        "main:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("debug", True),
        log_level="info"
    )