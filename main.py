#!/usr/bin/env python3
"""
PostgreSQL Database Exporter
Main entry point of the application
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'src'))

from src.gui.main_window import PostgreSQLExporterApp

def main():
    """Main function of the application"""
    try:
        app = PostgreSQLExporterApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Application closed by the user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()