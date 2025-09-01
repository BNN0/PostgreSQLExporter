"""
File management utilities
"""

import os
from typing import Optional
from datetime import datetime
from .sql_formatter import format_file_size

class FileHandler:
    """SQL file management class"""
    
    @staticmethod
    def save_sql_file(content: str, file_path: str) -> bool:
        """
        Save SQL content to a file
        """
        try:
            # Create directory if it does not exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        Get information from a file
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size": stat.st_size,
                "size_formatted": format_file_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime)
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    @staticmethod
    def validate_file_path(file_path: str) -> tuple[bool, str]:
        """
        Validates whether a file path is valid
        """
        try:
            # Verify that the parent directory exists or can be created
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    return False, f"The directory cannot be created.: {e}"
            
            # Verify write permissions
            if os.path.exists(file_path):
                if not os.access(file_path, os.W_OK):
                    return False, "You do not have write permissions for the file."
            else:
                # Check permissions in the parent directory
                parent_dir = directory if directory else "."
                if not os.access(parent_dir, os.W_OK):
                    return False, "You do not have write permissions for the directory."
            
            return True, "Invalid route"
            
        except Exception as e:
            return False, f"Error validating route: {e}"
    
    @staticmethod
    def generate_default_filename(database_name: str, export_type: str = "complete") -> str:
        """
        Generate default file name
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"export_{database_name}_{export_type}_{timestamp}.sql"
    
    @staticmethod
    def read_sql_file(file_path: str) -> Optional[str]:
        """
        Read an SQL file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    @staticmethod
    def backup_existing_file(file_path: str) -> bool:
        """
        Create a backup of an existing file
        """
        if not os.path.exists(file_path):
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(file_path, backup_path)
            print(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False