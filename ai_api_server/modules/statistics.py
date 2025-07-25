"""
Система статистики использования AI моделей.
"""

import sqlite3
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class StatisticsManager:
    """Менеджер статистики использования."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация менеджера статистики.
        
        Args:
            config: Конфигурация статистики
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.database_file = config.get("database_file", "data/statistics.db")
        self.track_usage = config.get("track_usage", True)
        self.track_response_time = config.get("track_response_time", True)
        self.track_errors = config.get("track_errors", True)
        
        # Создаем директорию если не существует
        db_dir = Path(self.database_file).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = asyncio.Lock()
    
    async def initialize_database(self) -> None:
        """Инициализировать базу данных."""
        if not self.enabled:
            return
        
        async with aiosqlite.connect(self.database_file) as db:
            # Таблица использования моделей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    request_tokens INTEGER,
                    response_tokens INTEGER,
                    total_tokens INTEGER,
                    response_time_ms INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)
            
            # Таблица статистики провайдеров
            await db.execute("""
                CREATE TABLE IF NOT EXISTS provider_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    failed_requests INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    avg_response_time_ms REAL DEFAULT 0,
                    UNIQUE(provider_name, date)
                )
            """)
            
            # Таблица популярности моделей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_popularity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    usage_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    avg_response_time_ms REAL DEFAULT 0,
                    UNIQUE(provider_name, model_id, date)
                )
            """)
            
            # Индексы для оптимизации
            await db.execute("CREATE INDEX IF NOT EXISTS idx_model_usage_timestamp ON model_usage(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_model_usage_provider ON model_usage(provider_name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_model_usage_model ON model_usage(model_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_provider_stats_date ON provider_stats(date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_model_popularity_date ON model_popularity(date)")
            
            await db.commit()
    
    async def record_usage(self, 
                          provider_name: str,
                          model_id: str,
                          request_tokens: Optional[int] = None,
                          response_tokens: Optional[int] = None,
                          response_time_ms: Optional[int] = None,
                          success: bool = True,
                          error_message: Optional[str] = None) -> None:
        """
        Записать использование модели.
        
        Args:
            provider_name: Имя провайдера
            model_id: ID модели
            request_tokens: Количество токенов в запросе
            response_tokens: Количество токенов в ответе
            response_time_ms: Время ответа в миллисекундах
            success: Успешность запроса
            error_message: Сообщение об ошибке
        """
        if not self.enabled or not self.track_usage:
            return
        
        async with self._lock:
            total_tokens = None
            if request_tokens is not None and response_tokens is not None:
                total_tokens = request_tokens + response_tokens
            
            async with aiosqlite.connect(self.database_file) as db:
                # Записываем детальную статистику
                await db.execute("""
                    INSERT INTO model_usage 
                    (provider_name, model_id, request_tokens, response_tokens, 
                     total_tokens, response_time_ms, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (provider_name, model_id, request_tokens, response_tokens,
                      total_tokens, response_time_ms, success, error_message))
                
                # Обновляем агрегированную статистику провайдера
                await self._update_provider_stats(db, provider_name, total_tokens or 0, 
                                                 response_time_ms or 0, success)
                
                # Обновляем популярность модели
                await self._update_model_popularity(db, provider_name, model_id, 
                                                   total_tokens or 0, response_time_ms or 0)
                
                await db.commit()
    
    async def _update_provider_stats(self, db: aiosqlite.Connection, 
                                   provider_name: str, tokens: int, 
                                   response_time: int, success: bool) -> None:
        """Обновить статистику провайдера."""
        today = datetime.now().date()
        
        # Получаем текущую статистику
        cursor = await db.execute("""
            SELECT total_requests, successful_requests, failed_requests, 
                   total_tokens, avg_response_time_ms
            FROM provider_stats 
            WHERE provider_name = ? AND date = ?
        """, (provider_name, today))
        
        row = await cursor.fetchone()
        
        if row:
            # Обновляем существующую запись
            total_requests, successful_requests, failed_requests, total_tokens, avg_response_time = row
            
            new_total_requests = total_requests + 1
            new_successful_requests = successful_requests + (1 if success else 0)
            new_failed_requests = failed_requests + (0 if success else 1)
            new_total_tokens = total_tokens + tokens
            
            # Вычисляем новое среднее время ответа
            if response_time > 0:
                new_avg_response_time = ((avg_response_time * total_requests) + response_time) / new_total_requests
            else:
                new_avg_response_time = avg_response_time
            
            await db.execute("""
                UPDATE provider_stats 
                SET total_requests = ?, successful_requests = ?, failed_requests = ?,
                    total_tokens = ?, avg_response_time_ms = ?
                WHERE provider_name = ? AND date = ?
            """, (new_total_requests, new_successful_requests, new_failed_requests,
                  new_total_tokens, new_avg_response_time, provider_name, today))
        else:
            # Создаем новую запись
            await db.execute("""
                INSERT INTO provider_stats 
                (provider_name, date, total_requests, successful_requests, failed_requests,
                 total_tokens, avg_response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (provider_name, today, 1, 1 if success else 0, 0 if success else 1,
                  tokens, response_time if response_time > 0 else 0))
    
    async def _update_model_popularity(self, db: aiosqlite.Connection,
                                     provider_name: str, model_id: str,
                                     tokens: int, response_time: int) -> None:
        """Обновить популярность модели."""
        today = datetime.now().date()
        
        # Получаем текущую статистику модели
        cursor = await db.execute("""
            SELECT usage_count, total_tokens, avg_response_time_ms
            FROM model_popularity 
            WHERE provider_name = ? AND model_id = ? AND date = ?
        """, (provider_name, model_id, today))
        
        row = await cursor.fetchone()
        
        if row:
            # Обновляем существующую запись
            usage_count, total_tokens_current, avg_response_time = row
            
            new_usage_count = usage_count + 1
            new_total_tokens = total_tokens_current + tokens
            
            # Вычисляем новое среднее время ответа
            if response_time > 0:
                new_avg_response_time = ((avg_response_time * usage_count) + response_time) / new_usage_count
            else:
                new_avg_response_time = avg_response_time
            
            await db.execute("""
                UPDATE model_popularity 
                SET usage_count = ?, total_tokens = ?, avg_response_time_ms = ?
                WHERE provider_name = ? AND model_id = ? AND date = ?
            """, (new_usage_count, new_total_tokens, new_avg_response_time,
                  provider_name, model_id, today))
        else:
            # Создаем новую запись
            await db.execute("""
                INSERT INTO model_popularity 
                (provider_name, model_id, date, usage_count, total_tokens, avg_response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (provider_name, model_id, today, 1, tokens, 
                  response_time if response_time > 0 else 0))
    
    async def get_popular_providers(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получить популярные провайдеры.
        
        Args:
            days: Количество дней для анализа
            
        Returns:
            List[Dict[str, Any]]: Список популярных провайдеров
        """
        if not self.enabled:
            return []
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        async with aiosqlite.connect(self.database_file) as db:
            cursor = await db.execute("""
                SELECT provider_name, 
                       SUM(total_requests) as total_requests,
                       SUM(successful_requests) as successful_requests,
                       SUM(failed_requests) as failed_requests,
                       SUM(total_tokens) as total_tokens,
                       AVG(avg_response_time_ms) as avg_response_time
                FROM provider_stats 
                WHERE date >= ?
                GROUP BY provider_name
                ORDER BY total_requests DESC
            """, (start_date,))
            
            rows = await cursor.fetchall()
            
            providers = []
            for row in rows:
                providers.append({
                    "provider_name": row[0],
                    "total_requests": row[1],
                    "successful_requests": row[2],
                    "failed_requests": row[3],
                    "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    "total_tokens": row[4],
                    "avg_response_time_ms": round(row[5], 2) if row[5] else 0
                })
            
            return providers
    
    async def get_popular_models(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить популярные модели.
        
        Args:
            days: Количество дней для анализа
            limit: Максимальное количество моделей
            
        Returns:
            List[Dict[str, Any]]: Список популярных моделей
        """
        if not self.enabled:
            return []
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        async with aiosqlite.connect(self.database_file) as db:
            cursor = await db.execute("""
                SELECT provider_name, model_id,
                       SUM(usage_count) as total_usage,
                       SUM(total_tokens) as total_tokens,
                       AVG(avg_response_time_ms) as avg_response_time
                FROM model_popularity 
                WHERE date >= ?
                GROUP BY provider_name, model_id
                ORDER BY total_usage DESC
                LIMIT ?
            """, (start_date, limit))
            
            rows = await cursor.fetchall()
            
            models = []
            for row in rows:
                models.append({
                    "provider_name": row[0],
                    "model_id": row[1],
                    "usage_count": row[2],
                    "total_tokens": row[3],
                    "avg_response_time_ms": round(row[4], 2) if row[4] else 0
                })
            
            return models
    
    async def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Получить общую сводку статистики.
        
        Returns:
            Dict[str, Any]: Сводка статистики
        """
        if not self.enabled:
            return {"enabled": False}
        
        async with aiosqlite.connect(self.database_file) as db:
            # Общая статистика за все время
            cursor = await db.execute("""
                SELECT COUNT(*) as total_requests,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                       SUM(total_tokens) as total_tokens,
                       AVG(response_time_ms) as avg_response_time
                FROM model_usage
            """)
            
            row = await cursor.fetchone()
            
            # Статистика за последние 24 часа
            yesterday = datetime.now() - timedelta(hours=24)
            cursor = await db.execute("""
                SELECT COUNT(*) as requests_24h,
                       SUM(total_tokens) as tokens_24h
                FROM model_usage
                WHERE timestamp >= ?
            """, (yesterday,))
            
            recent_row = await cursor.fetchone()
            
            # Количество уникальных провайдеров и моделей
            cursor = await db.execute("""
                SELECT COUNT(DISTINCT provider_name) as providers_count,
                       COUNT(DISTINCT model_id) as models_count
                FROM model_usage
            """)
            
            unique_row = await cursor.fetchone()
            
            return {
                "enabled": True,
                "total_requests": row[0] if row[0] else 0,
                "successful_requests": row[1] if row[1] else 0,
                "success_rate": (row[1] / row[0] * 100) if row[0] and row[1] else 0,
                "total_tokens": row[2] if row[2] else 0,
                "avg_response_time_ms": round(row[3], 2) if row[3] else 0,
                "requests_24h": recent_row[0] if recent_row[0] else 0,
                "tokens_24h": recent_row[1] if recent_row[1] else 0,
                "unique_providers": unique_row[0] if unique_row[0] else 0,
                "unique_models": unique_row[1] if unique_row[1] else 0
            }