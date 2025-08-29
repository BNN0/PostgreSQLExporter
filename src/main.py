import psycopg2
import os
from datetime import datetime

def export_database_sql(host, database, user, password, output_file=None, port=5432):
    """
    Exporta una base de datos PostgreSQL a SQL usando Python puro
    """
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backup_{database}_{timestamp}.sql"
    
    conn = None
    cur = None
    
    try:
        # Establecer conexión
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        cur = conn.cursor()
        print("✅ Conexión establecida")
        
        # Obtener lista de tablas
        print("Obteniendo lista de tablas...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"Encontradas {len(tables)} tablas: {', '.join(tables)}")
        
        # Crear archivo SQL
        with open(output_file, 'w', encoding='utf-8') as f:
            # Escribir header
            f.write(f"-- Backup de PostgreSQL\n")
            f.write(f"-- Base de datos: {database}\n")
            f.write(f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Generado con Python puro\n\n")
            
            # Configuraciones iniciales
            f.write("SET statement_timeout = 0;\n")
            f.write("SET lock_timeout = 0;\n")
            f.write("SET client_encoding = 'UTF8';\n")
            f.write("SET standard_conforming_strings = on;\n")
            f.write("SET check_function_bodies = false;\n")
            f.write("SET client_min_messages = warning;\n\n")
            
            # Crear base de datos
            f.write(f"-- Crear base de datos\n")
            f.write(f"CREATE DATABASE {database};\n")
            f.write(f"\\c {database};\n\n")
            
            # ========================================
            # ESTRUCTURA DE TABLAS
            # ========================================
            f.write("-- =============================================\n")
            f.write("-- ESTRUCTURA DE TABLAS\n")
            f.write("-- =============================================\n\n")
            
            for table in tables:
                print(f"Generando estructura para: {table}")
                create_sql = get_create_table_sql(cur, table)
                f.write(create_sql)
            
            # ========================================
            # DATOS DE TABLAS
            # ========================================
            f.write("-- =============================================\n")
            f.write("-- DATOS DE TABLAS\n")
            f.write("-- =============================================\n\n")
            
            for table in tables:
                print(f"Exportando datos de: {table}")
                data_sql = get_table_data_sql(cur, table)
                f.write(data_sql)
            
            f.write("-- Backup completado exitosamente\n")
        
        # Información del archivo creado
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        print(f"✅ Backup creado exitosamente: {output_file}")
        print(f"📁 Tamaño del archivo: {file_size:.2f} MB")
        return output_file
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("🔌 Conexión cerrada")

def get_create_table_sql(cur, table_name, schema='public'):
    """Generar SQL CREATE TABLE para una tabla"""
    try:
        # Obtener información de columnas
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
            return f"-- No se pudo obtener estructura de {table_name}\n\n"
        
        # Obtener constraints
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
        
        # Construir CREATE TABLE con nombres escapados
        escaped_table = f'"{table_name}"' if needs_quoting(table_name) else table_name
        sql = f"-- Tabla: {schema}.{escaped_table}\n"
        sql += f"DROP TABLE IF EXISTS {schema}.{escaped_table} CASCADE;\n"
        sql += f"CREATE TABLE {schema}.{escaped_table} (\n"
        
        # Definir columnas con nombres escapados
        column_definitions = []
        for col_name, data_type, char_max_len, is_nullable, default_val, num_precision, num_scale in columns:
            escaped_col = f'"{col_name}"' if needs_quoting(col_name) else col_name
            col_def = f"    {escaped_col} "
            
            # Tipo de dato con precisión si es necesario
            if data_type == 'character varying' and char_max_len:
                col_def += f"VARCHAR({char_max_len})"
            elif data_type == 'character' and char_max_len:
                col_def += f"CHAR({char_max_len})"
            elif data_type == 'numeric' and num_precision:
                if num_scale:
                    col_def += f"NUMERIC({num_precision},{num_scale})"
                else:
                    col_def += f"NUMERIC({num_precision})"
            elif data_type == 'timestamp without time zone':
                col_def += "TIMESTAMP"
            elif data_type == 'timestamp with time zone':
                col_def += "TIMESTAMPTZ"
            else:
                col_def += data_type.upper()
            
            # NOT NULL
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            
            # DEFAULT
            if default_val:
                if 'nextval' in str(default_val):
                    # Es una secuencia (SERIAL)
                    pass  # Lo manejamos después
                else:
                    col_def += f" DEFAULT {default_val}"
            
            column_definitions.append(col_def)
        
        sql += ",\n".join(column_definitions)
        
        # Agregar constraints
        if constraints:
            constraint_definitions = []
            for con_name, con_type, con_def in constraints:
                if con_type == 'p':  # Primary key
                    constraint_definitions.append(f"    CONSTRAINT {con_name} {con_def}")
                elif con_type == 'u':  # Unique
                    constraint_definitions.append(f"    CONSTRAINT {con_name} {con_def}")
                elif con_type == 'c':  # Check
                    constraint_definitions.append(f"    CONSTRAINT {con_name} {con_def}")
                elif con_type == 'f':  # Foreign key
                    constraint_definitions.append(f"    CONSTRAINT {con_name} {con_def}")
            
            if constraint_definitions:
                sql += ",\n" + ",\n".join(constraint_definitions)
        
        sql += "\n);\n\n"
        
        # Crear secuencias si es necesario (para campos SERIAL)
        for col_name, data_type, char_max_len, is_nullable, default_val, num_precision, num_scale in columns:
            if default_val and 'nextval' in str(default_val):
                seq_name = default_val.split("'")[1].split("'")[0]
                escaped_col = f'"{col_name}"' if needs_quoting(col_name) else col_name
                sql += f"-- Secuencia para {escaped_col}\n"
                sql += f"CREATE SEQUENCE IF NOT EXISTS {seq_name};\n"
                sql += f"ALTER TABLE {schema}.{escaped_table} ALTER COLUMN {escaped_col} SET DEFAULT nextval('{seq_name}');\n\n"
        
        return sql
        
    except Exception as e:
        return f"-- Error al obtener estructura de {table_name}: {e}\n\n"

def get_table_data_sql(cur, table_name, schema='public', batch_size=1000):
    """Generar SQL INSERT para los datos de una tabla"""
    try:
        # Escapar nombre de tabla para consultas
        escaped_table = f'"{table_name}"' if needs_quoting(table_name) else table_name
        
        # Contar registros
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{escaped_table}")
        total_rows = cur.fetchone()[0]
        
        if total_rows == 0:
            return f"-- No hay datos en {schema}.{escaped_table}\n\n"
        
        # Obtener nombres de columnas
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        
        column_names = [row[0] for row in cur.fetchall()]
        escaped_columns = [f'"{col}"' if needs_quoting(col) else col for col in column_names]
        
        sql = f"-- Datos para {schema}.{escaped_table} ({total_rows} registros)\n"
        
        # Exportar datos en lotes para tablas grandes
        offset = 0
        while offset < total_rows:
            # Obtener lote de datos usando nombres de columnas escapados
            query = f"""
            SELECT {', '.join(escaped_columns)} 
            FROM {schema}.{escaped_table} 
            LIMIT {batch_size} OFFSET {offset}
            """
            
            cur.execute(query)
            rows = cur.fetchall()
            
            if rows:
                # Crear INSERT statement con nombres escapados
                sql += f"INSERT INTO {schema}.{escaped_table} ({', '.join(escaped_columns)}) VALUES\n"
                
                value_lines = []
                for row in rows:
                    formatted_values = []
                    for value in row:
                        if value is None:
                            formatted_values.append('NULL')
                        elif isinstance(value, str):
                            # Escapar comillas simples y caracteres especiales
                            escaped_value = value.replace("'", "''").replace("\\", "\\\\")
                            formatted_values.append(f"'{escaped_value}'")
                        elif isinstance(value, bool):
                            formatted_values.append('TRUE' if value else 'FALSE')
                        elif isinstance(value, (int, float)):
                            formatted_values.append(str(value))
                        elif hasattr(value, 'isoformat'):  # datetime objects
                            formatted_values.append(f"'{value.isoformat()}'")
                        else:
                            formatted_values.append(f"'{str(value)}'")
                    
                    value_lines.append(f"    ({', '.join(formatted_values)})")
                
                sql += ",\n".join(value_lines) + ";\n\n"
            
            offset += batch_size
            
            # Mostrar progreso para tablas grandes
            if total_rows > 1000:
                progress = min(offset, total_rows)
                print(f"  → {table_name}: {progress}/{total_rows} registros ({progress/total_rows*100:.1f}%)")
        
        return sql
        
    except Exception as e:
        return f"-- Error al exportar datos de {table_name}: {e}\n\n"

def needs_quoting(identifier):
    """
    Determina si un identificador necesita comillas dobles en PostgreSQL
    """
    import re
    
    # Si está vacío, contiene mayúsculas, espacios, o caracteres especiales
    if not identifier:
        return True
    
    # Si contiene mayúsculas
    if identifier != identifier.lower():
        return True
        
    # Si contiene espacios o caracteres especiales
    if re.search(r'[^a-z0-9_]', identifier):
        return True
        
    # Si es una palabra reservada de PostgreSQL (lista básica)
    reserved_words = {
        'select', 'from', 'where', 'table', 'create', 'drop', 'alter',
        'insert', 'update', 'delete', 'user', 'order', 'group', 'having',
        'limit', 'offset', 'join', 'inner', 'left', 'right', 'full',
        'union', 'all', 'distinct', 'as', 'on', 'and', 'or', 'not',
        'null', 'true', 'false', 'primary', 'foreign', 'key', 'unique',
        'constraint', 'index', 'view', 'sequence', 'trigger', 'function'
    }
    
    if identifier.lower() in reserved_words:
        return True
    
    # Si comienza con número
    if identifier[0].isdigit():
        return True
        
    return False

# Uso - exactamente igual que tu código original
if __name__ == "__main__":
    backup_file = export_database_sql(
        host="localhost",
        database="Suppliers_Test",
        user="postgres",
        password="admin"
    )
    
    if backup_file:
        print(f"🎉 ¡Exportación completada exitosamente!")
        print(f"📄 Archivo: {backup_file}")
    else:
        print("💥 La exportación falló")