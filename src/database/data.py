"""
Module for exporting data from the PostgreSQL database
"""

from typing import List, Optional, Any
from .connection import DatabaseConnection
from ..utils.sql_formatter import needs_quoting, format_sql_value

class DataExporter:
    """Class for exporting database data"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def get_data_sql(self, table_name: str, schema: str = 'public', batch_size: int = 1000) -> str:
        """Generate SQL INSERT for the data in a table"""
        try:
            escaped_table = f'"{table_name}"' if needs_quoting(table_name) else table_name
            
            with self.db_connection.get_cursor() as cur:
                # Count records
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{escaped_table}")
                total_rows = cur.fetchone()[0]
                
                if total_rows == 0:
                    return f"-- There is no data in {schema}.{escaped_table}\n\n"
                
                # Get column names
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                
                column_names = [row[0] for row in cur.fetchall()]
                escaped_columns = [f'"{col}"' if needs_quoting(col) else col for col in column_names]
                
                return self._export_table_data(
                    cur, table_name, schema, escaped_table, 
                    escaped_columns, total_rows, batch_size
                )
                
        except Exception as e:
            return f"-- Error exporting data from {table_name}: {e}\n\n"
    
    def _export_table_data(self, cur, table_name: str, schema: str, escaped_table: str,
                          escaped_columns: List[str], total_rows: int, batch_size: int) -> str:
        """Export data from a table in batches"""
        sql = f"-- Data for {schema}.{escaped_table} ({total_rows} records))\n"
        
        offset = 0
        while offset < total_rows:
            query = f"""
            SELECT {', '.join(escaped_columns)} 
            FROM {schema}.{escaped_table} 
            LIMIT {batch_size} OFFSET {offset}
            """
            
            cur.execute(query)
            rows = cur.fetchall()
            
            if rows:
                sql += f"INSERT INTO {schema}.{escaped_table} ({', '.join(escaped_columns)}) VALUES\n"
                
                value_lines = []
                for row in rows:
                    formatted_values = [format_sql_value(value) for value in row]
                    value_lines.append(f"    ({', '.join(formatted_values)})")
                
                sql += ",\n".join(value_lines) + ";\n\n"
            
            offset += batch_size
            
            # Show progress for large tables
            if total_rows > 1000:
                progress = min(offset, total_rows)
                print(f"  → {table_name}: {progress}/{total_rows} registers ({progress/total_rows*100:.1f}%)")
        
        return sql
    
    def export_all_data(self, tables: Optional[List[str]] = None, schema: str = 'public', 
                       batch_size: int = 1000) -> str:
        """Export data from all tables"""
        if tables is None:
            tables = self.db_connection.get_tables(schema)
        
        sql = "-- =============================================\n"
        sql += "-- TABLE DATA\n"
        sql += "-- =============================================\n\n"
        
        for table in tables:
            print(f"Exporting data from: {table}")
            sql += self.get_data_sql(table, schema, batch_size)
        
        return sql
    
    def get_table_row_count(self, table_name: str, schema: str = 'public') -> int:
        """Get the number of rows in a table"""
        try:
            escaped_table = f'"{table_name}"' if needs_quoting(table_name) else table_name
            with self.db_connection.get_cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{escaped_table}")
                return cur.fetchone()[0]
        except Exception:
            return 0
    
    def get_tables_info(self, tables: Optional[List[str]] = None, schema: str = 'public') -> dict:
        """Obtains basic information from tables (name and number of records)"""
        if tables is None:
            tables = self.db_connection.get_tables(schema)
        
        tables_info = {}
        for table in tables:
            row_count = self.get_table_row_count(table, schema)
            tables_info[table] = {
                'rows': row_count,
                'schema': schema
            }
        
        return tables_info