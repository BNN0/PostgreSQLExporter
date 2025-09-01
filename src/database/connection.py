"""
Module for managing connections to PostgreSQL
"""

import psycopg2
from typing import Optional, List, Tuple
from contextlib import contextmanager

class DatabaseConnection:
    """Class for managing connections to PostgreSQL"""
    
    def __init__(self, host: str, database: str, user: str, password: str, port: int = 5432):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Establish connection to the database"""
        try:
            print("Connecting to the database...")
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.connection.cursor()
            print("✅ Connection established")
            return True
        except psycopg2.Error as e:
            print(f"❌ PostgreSQL error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def disconnect(self):
        """Close the connection to the database"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
        print("🔌 Closed connection")
    
    @contextmanager
    def get_cursor(self):
        """Context manager to obtain cursor"""
        if not self.connection or not self.cursor:
            raise Exception("No active connection")
        
        try:
            yield self.cursor
        except Exception:
            self.connection.rollback()
            raise
    
    def get_tables(self, schema: str = 'public') -> List[str]:
        """Get list of tables from a schema"""
        try:
            with self.get_cursor() as cur:
                print("Obtaining list of tables...")
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, (schema,))
                tables = [row[0] for row in cur.fetchall()]
                print(f"{len(tables)} tables found: {', '.join(tables)}")
                return tables
        except Exception as e:
            print(f"Error retrieving tables: {e}")
            return []
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection and return status and message"""
        try:
            if self.connect():
                with self.get_cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                self.disconnect()
                return True, f"Successful connection. {version[:50]}..."
            else:
                return False, "Unable to establish connection"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()