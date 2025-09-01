"""
Utilities for formatting and managing SQL
"""

import re
from typing import Any
from datetime import datetime

def needs_quoting(identifier: str) -> bool:
    """
    Determine whether an identifier needs double quotes in PostgreSQL
    """
    if not identifier:
        return True
    
    # If it contains uppercase letters
    if identifier != identifier.lower():
        return True
        
    # If it contains special characters
    if re.search(r'[^a-z0-9_]', identifier):
        return True
        
    # Reserved words
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
    
    # If it starts with a number
    if identifier[0].isdigit():
        return True
        
    return False

def format_sql_value(value: Any) -> str:
    """
    Format a value for SQL insertion
    """
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        escaped_value = value.replace("'", "''").replace("\\", "\\\\")
        return f"'{escaped_value}'"
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    elif hasattr(value, 'isoformat'):  # datetime objects
        return f"'{value.isoformat()}'"
    else:
        return f"'{str(value)}'"

def generate_sql_header(database_name: str) -> str:
    """
    Generates the standard header for SQL files.
    """
    return f"""-- PostgreSQL backup
-- Database: {database_name}
-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Generated with PostgreSQL Database Exporter

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF-8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

"""

def escape_identifier(identifier: str) -> str:
    """
    Escape an SQL identifier if necessary
    """
    return f'"{identifier}"' if needs_quoting(identifier) else identifier

def generate_filename(database_name: str, export_type: str = "complete") -> str:
    """
    Generate standard file name
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"export_{database_name}_{export_type}_{timestamp}.sql"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"