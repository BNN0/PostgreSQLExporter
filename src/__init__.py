# src/__init__.py
"""
PostgreSQL Database Exporter
A tool for exporting PostgreSQL databases to SQL files
"""

__version__ = "1.0.0"
__author__ = "BNN0"
__description__ = "Tool for exporting PostgreSQL databases"

# src/database/__init__.py
"""
Modules for managing PostgreSQL databases
"""

from .database.connection import DatabaseConnection
from .database.structure import StructureExporter
from .database.data import DataExporter

__all__ = ['DatabaseConnection', 'StructureExporter', 'DataExporter']

# src/utils/__init__.py
"""
General utilities for the project
"""

from .utils.sql_formatter import (
    needs_quoting, 
    format_sql_value, 
    generate_sql_header, 
    escape_identifier,
    generate_filename,
    format_file_size
)
from .utils.file_handler import FileHandler

__all__ = [
    'needs_quoting', 
    'format_sql_value', 
    'generate_sql_header', 
    'escape_identifier',
    'generate_filename',
    'format_file_size',
    'FileHandler'
]

# src/gui/__init__.py
"""
Graphical interface modules
"""

from .gui.main_window import PostgreSQLExporterApp
from .gui.dialogs import ConnectionTestDialog, TableSelectionDialog, ProgressDialog

__all__ = ['PostgreSQLExporterApp', 'ConnectionTestDialog', 'TableSelectionDialog', 'ProgressDialog']