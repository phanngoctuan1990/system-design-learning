"""
MySQL Adapter - Implementation of DatabasePort for MySQL
"""
import mysql.connector
from mysql.connector import pooling
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from core.interfaces.database_port import DatabasePort


class MySQLAdapter(DatabasePort):
    def __init__(self, host: str, port: int, user: str, password: str, database: str, pool_size: int = 5):
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=pool_size,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    
    def _get_connection(self):
        return self.pool.get_connection()
    
    @contextmanager
    def transaction(self):
        """
        Context manager cho transaction.
        Usage:
            with db.transaction() as tx:
                tx.insert(...)
                tx.insert(...)
            # Auto-commit nếu không có exception
            # Auto-rollback nếu có exception
        """
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        tx = TransactionContext(conn, cursor)
        try:
            yield tx
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    def execute(self, query: str, params: tuple = None) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def insert(self, query: str, params: tuple = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()
    
    def ping(self) -> bool:
        try:
            conn = self._get_connection()
            conn.ping(reconnect=True)
            conn.close()
            return True
        except Exception:
            return False


class TransactionContext:
    """Helper class for transaction operations"""
    
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor
        self.last_insert_id = None
    
    def execute(self, query: str, params: tuple = None) -> None:
        self.cursor.execute(query, params or ())
    
    def insert(self, query: str, params: tuple = None) -> int:
        self.cursor.execute(query, params or ())
        self.last_insert_id = self.cursor.lastrowid
        return self.last_insert_id
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()

