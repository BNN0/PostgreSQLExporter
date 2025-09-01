"""
Module for exporting PostgreSQL database structure
"""

from typing import List, Optional
from .connection import DatabaseConnection
from ..utils.sql_formatter import needs_quoting

class StructureExporter:
    """Class for exporting database structure"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def get_structure_sql(self, table_name: str, schema: str = 'public') -> str:
        """Generate SQL CREATE TABLE for a table"""
        try:
            with self.db_connection.get_cursor() as cur:
                # Get columns
                cur.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        character_maximum_length,
                        is_nullable, 
                        column_default,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                
                columns = cur.fetchall()
                
                if not columns:
                    return f"-- Structure could not be obtained for {table_name}\n\n"
                
                # Get constraints
                cur.execute("""
                    SELECT 
                        conname, 
                        contype, 
                        pg_get_constraintdef(oid) as definition
                    FROM pg_constraint
                    WHERE conrelid = (
                        SELECT oid FROM pg_class 
                        WHERE relname = %s 
                        AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
                    )
                    ORDER BY contype
                """, (table_name, schema))
                
                constraints = cur.fetchall()
                
                return self._build_create_table_sql(table_name, schema, columns, constraints)
                
        except Exception as e:
            return f"-- Error obtaining structure of {table_name}: {e}\n\n"
    
    def _build_create_table_sql(self, table_name: str, schema: str, columns: List, constraints: List) -> str:
        """Build the SQL CREATE TABLE"""
        escaped_table = f'"{table_name}"' if needs_quoting(table_name) else table_name
        sql = f"-- Tabla: {schema}.{escaped_table}\n"
        sql += f"DROP TABLE IF EXISTS {schema}.{escaped_table} CASCADE;\n"
        sql += f"CREATE TABLE {schema}.{escaped_table} (\n"
        
        column_definitions = []
        sequences_info = []
        
        for col_name, data_type, char_max_len, is_nullable, default_val, num_precision, num_scale in columns:
            escaped_col = f'"{col_name}"' if needs_quoting(col_name) else col_name
            col_def = f"    {escaped_col} "
            
            # Determine data type
            col_def += self._format_data_type(data_type, char_max_len, num_precision, num_scale)
            
            # NOT NULL
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            
            # DEFAULT
            if default_val:
                if 'nextval' in str(default_val):
                    # Save sequence info for later
                    seq_name = default_val.split("'")[1].split("'")[0]
                    sequences_info.append((escaped_col, seq_name))
                else:
                    col_def += f" DEFAULT {default_val}"
            
            column_definitions.append(col_def)
        
        sql += ",\n".join(column_definitions)
        
        # Add constraints
        if constraints:
            constraint_definitions = []
            for con_name, con_type, con_def in constraints:
                if con_type in ['p', 'u', 'c', 'f']:  # primary, unique, check, foreign
                    constraint_definitions.append(f"    CONSTRAINT {con_name} {con_def}")
            
            if constraint_definitions:
                sql += ",\n" + ",\n".join(constraint_definitions)
        
        sql += "\n);\n\n"
        
        # Add sequences
        for col_name, seq_name in sequences_info:
            sql += f"-- Sequence for {col_name}\n"
            sql += f"CREATE SEQUENCE IF NOT EXISTS {seq_name};\n"
            sql += f"ALTER TABLE {schema}.{escaped_table} ALTER COLUMN {col_name} SET DEFAULT nextval('{seq_name}');\n\n"
        
        return sql
    
    def _format_data_type(self, data_type: str, char_max_len: Optional[int], 
                         num_precision: Optional[int], num_scale: Optional[int]) -> str:
        """Format the SQL data type"""
        if data_type == 'character varying' and char_max_len:
            return f"VARCHAR({char_max_len})"
        elif data_type == 'character' and char_max_len:
            return f"CHAR({char_max_len})"
        elif data_type == 'numeric' and num_precision:
            if num_scale:
                return f"NUMERIC({num_precision},{num_scale})"
            else:
                return f"NUMERIC({num_precision})"
        elif data_type == 'timestamp without time zone':
            return "TIMESTAMP"
        elif data_type == 'timestamp with time zone':
            return "TIMESTAMPTZ"
        else:
            return data_type.upper()
    
    def export_all_structures(self, tables: Optional[List[str]] = None, schema: str = 'public') -> str:
        """Export structure of all tables"""
        if tables is None:
            tables = self.db_connection.get_tables(schema)
        
        sql = "-- =============================================\n"
        sql += "-- TABLE STRUCTURE\n"
        sql += "-- =============================================\n\n"
        
        for table in tables:
            print(f"Creating structure for: {table}")
            sql += self.get_structure_sql(table, schema)
        
        return sql