#!/usr/bin/env python3
"""
Скрипт для запуска AI API Server.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Проверить установленные зависимости."""
    try:
        import fastapi
        import uvicorn
        import openai
        import pydantic
        import google.generativeai
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False


def check_api_keys():
    """Проверить наличие файла с API ключами."""
    api_keys_file = Path("api_keys.yaml")
    
    if not api_keys_file.exists():
        print("⚠️  Файл api_keys.yaml не найден")
        print("💡 Создайте файл api_keys.yaml с API ключами для работы провайдеров")
        return False
    
    print("✅ Файл api_keys.yaml найден")
    return True


def check_config():
    """Проверить конфигурационный файл."""
    config_file = Path("config.yaml")
    
    if not config_file.exists():
        print("⚠️  Файл config.yaml не найден")
        return False
    
    print("✅ Файл config.yaml найден")
    return True


def create_directories():
    """Создать необходимые директории."""
    directories = ["data", "logs"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Директория {directory}/ создана")


def main():
    """Главная функция."""
    print("🚀 Запуск AI API Server")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_requirements():
        sys.exit(1)
    
    # Проверяем API ключи
    if not check_api_keys():
        print("\n💡 Для работы сервера необходимо настроить API ключи в api_keys.yaml")
        print("   Сервер может запуститься, но провайдеры будут недоступны")
        
        response = input("\nПродолжить запуск? (y/N): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Проверяем конфигурацию
    if not check_config():
        print("⚠️  Будет использована конфигурация по умолчанию")
    
    # Создаем директории
    create_directories()
    
    print("\n🎯 Запуск сервера...")
    print("📍 API будет доступен по адресу: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("🔍 Альтернативная документация: http://localhost:8000/redoc")
    print("\n⏹️  Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запускаем сервер
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "ai_api_server.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()