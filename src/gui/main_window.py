"""
Main window of the PostgreSQL Exporter application
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from threading import Thread
from datetime import datetime
from typing import Optional

from ..database.connection import DatabaseConnection
from ..database.structure import StructureExporter
from ..database.data import DataExporter
from ..utils.file_handler import FileHandler
from ..utils.sql_formatter import generate_sql_header, generate_filename
from .dialogs import ConnectionTestDialog

class PostgreSQLExporterApp:
    """Main application for exporting PostgreSQL databases"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.current_sql_code = ""
        self.db_connection: Optional[DatabaseConnection] = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configure the user interface"""
        self.root.title("PostgreSQL Database Exporter")
        self.root.geometry("900x800")
        
        # Main frame with scroll
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_connection_frame(main_frame)
        self.create_options_frame(main_frame)
        self.create_sql_frame(main_frame)
        self.create_download_frame(main_frame)
    
    def create_connection_frame(self, parent):
        """Create the connection configuration frame"""
        connection_frame = ttk.LabelFrame(parent, text="Connection Settings", padding="10")
        connection_frame.pack(fill="x", pady=5)
        
        # Host
        tk.Label(connection_frame, text="Host:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.host_entry = tk.Entry(connection_frame, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=2)
        self.host_entry.insert(0, "localhost")
        
        # Port
        tk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.port_entry = tk.Entry(connection_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=2)
        self.port_entry.insert(0, "5432")
        
        # Database
        tk.Label(connection_frame, text="Database:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.database_entry = tk.Entry(connection_frame, width=30)
        self.database_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Username
        tk.Label(connection_frame, text="User:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.user_entry = tk.Entry(connection_frame, width=20)
        self.user_entry.grid(row=1, column=3, padx=5, pady=2)
        
        # Password
        tk.Label(connection_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.password_entry = tk.Entry(connection_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # Connection test button
        ttk.Button(connection_frame, text="Test Connection", 
                  command=self.test_connection).grid(row=2, column=2, columnspan=2, padx=5, pady=2)
    
    def create_options_frame(self, parent):
        """Create the export options frame"""
        options_frame = ttk.LabelFrame(parent, text="Export Options", padding="10")
        options_frame.pack(fill="x", pady=5)
        
        # Export buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Structure Only", 
                  command=self.generate_structure).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Data Only", 
                  command=self.generate_data).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Structure + Data", 
                  command=self.generate_both).pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(options_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Additional options
        options_inner_frame = ttk.Frame(options_frame)
        options_inner_frame.pack(fill="x")
        
        # Batch size
        tk.Label(options_inner_frame, text="Batch size:").pack(side="left", padx=5)
        self.batch_size_var = tk.StringVar(value="1000")
        batch_spin = tk.Spinbox(options_inner_frame, from_=100, to=10000, increment=100, 
                               textvariable=self.batch_size_var, width=10)
        batch_spin.pack(side="left", padx=5)
        
        # Schema
        tk.Label(options_inner_frame, text="Schema:").pack(side="left", padx=(20, 5))
        self.schema_var = tk.StringVar(value="public")
        schema_entry = tk.Entry(options_inner_frame, textvariable=self.schema_var, width=15)
        schema_entry.pack(side="left", padx=5)
    
    def create_sql_frame(self, parent):
        """Create the frame to display the SQL code"""
        sql_frame = ttk.LabelFrame(parent, text="Generated SQL Code", padding="10")
        sql_frame.pack(fill="both", expand=True, pady=5)
        
        # Text area with scrollbars
        self.sql_text = scrolledtext.ScrolledText(sql_frame, wrap=tk.WORD, height=25, width=100)
        self.sql_text.pack(fill="both", expand=True)
        
        # Frame for information
        info_frame = ttk.Frame(sql_frame)
        info_frame.pack(fill="x", pady=(5, 0))
        
        self.info_label = tk.Label(info_frame, text="", fg="gray")
        self.info_label.pack(side="left")
        
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(info_frame, textvariable=self.progress_var, fg="blue")
        self.progress_label.pack(side="right")
    
    def create_download_frame(self, parent):
        """Create the frame for downloading files"""
        download_frame = ttk.Frame(parent)
        download_frame.pack(fill="x", pady=5)
        
        ttk.Button(download_frame, text="💾 Save SQL", 
                  command=self.save_sql_file).pack(side="left", padx=5)
        ttk.Button(download_frame, text="🗑️ Clean", 
                  command=self.clear_sql).pack(side="left", padx=5)
        ttk.Button(download_frame, text="📋 Copy to Clipboard", 
                  command=self.copy_to_clipboard).pack(side="left", padx=5)
    
    def get_connection_params(self) -> dict:
        """Get the connection parameters from the UI"""
        return {
            'host': self.host_entry.get().strip(),
            'database': self.database_entry.get().strip(),
            'user': self.user_entry.get().strip(),
            'password': self.password_entry.get(),
            'port': int(self.port_entry.get().strip()) if self.port_entry.get().strip() else 5432
        }
    
    def validate_connection_params(self) -> bool:
        """Verify that all connection parameters are complete."""
        params = self.get_connection_params()
        required_fields = ['host', 'database', 'user', 'password']
        
        for field in required_fields:
            if not params.get(field):
                messagebox.showerror("Error", f"The ‘{field}’ field is required.")
                return False
        
        return True
    
    def test_connection(self):
        """Test the connection to the database"""
        if not self.validate_connection_params():
            return
        
        params = self.get_connection_params()
        
        def worker():
            db_conn = DatabaseConnection(**params)
            success, message = db_conn.test_connection()
            
            self.root.after(0, lambda: self.show_connection_result(success, message))
        
        Thread(target=worker, daemon=True).start()
    
    def show_connection_result(self, success: bool, message: str):
        """Display the connection test result"""
        if success:
            messagebox.showinfo("Successful Connection", message)
        else:
            messagebox.showerror("Connection Error", message)
    
    def show_sql_in_text_widget(self, sql_code: str):
        """Display the SQL code in the text widget"""
        self.current_sql_code = sql_code
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(1.0, sql_code)
        
        # Update information
        lines = len(sql_code.split('\n'))
        chars = len(sql_code)
        self.info_label.config(text=f"Lines: {lines:,} | Characters: {chars:,}")
        self.progress_var.set("")
    
    def update_progress(self, message: str):
        """Update the progress message"""
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def generate_structure(self):
        """Generate and display only the structure of the tables"""
        if not self.validate_connection_params():
            return
        
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(1.0, "Generating structure... Please wait...")
        self.update_progress("Connecting...")
        
        def worker():
            try:
                params = self.get_connection_params()
                schema = self.schema_var.get() or 'public'
                
                with DatabaseConnection(**params) as db_conn:
                    if not db_conn.connection:
                        raise Exception("Unable to establish connection")
                    
                    self.root.after(0, lambda: self.update_progress("Generating structure..."))
                    
                    structure_exporter = StructureExporter(db_conn)
                    
                    sql_code = generate_sql_header(params['database'])
                    sql_code += structure_exporter.export_all_structures(schema=schema)
                    
                    self.root.after(0, lambda: self.show_sql_in_text_widget(sql_code))
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", "Structure successfully generated"))
            
            except Exception as e:
                self.root.after(0, lambda: self.sql_text.delete(1.0, tk.END))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error generating structure: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.update_progress(""))
        
        Thread(target=worker, daemon=True).start()
    
    def generate_data(self):
        """Generate and display only the data from the tables"""
        if not self.validate_connection_params():
            return
        
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(1.0, "Generating data... Please wait...")
        self.update_progress("Connecting...")
        
        def worker():
            try:
                params = self.get_connection_params()
                schema = self.schema_var.get() or 'public'
                batch_size = int(self.batch_size_var.get())
                
                with DatabaseConnection(**params) as db_conn:
                    if not db_conn.connection:
                        raise Exception("Unable to establish connection")
                    
                    self.root.after(0, lambda: self.update_progress("Generating data..."))
                    
                    data_exporter = DataExporter(db_conn)
                    
                    sql_code = generate_sql_header(params['database'])
                    sql_code += data_exporter.export_all_data(schema=schema, batch_size=batch_size)
                    
                    self.root.after(0, lambda: self.show_sql_in_text_widget(sql_code))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Data successfully generated"))
            
            except Exception as e:
                self.root.after(0, lambda: self.sql_text.delete(1.0, tk.END))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error generating data: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.update_progress(""))
        
        Thread(target=worker, daemon=True).start()
    
    def generate_both(self):
        """Generates and displays structure and data"""
        if not self.validate_connection_params():
            return
        
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(1.0, "Generating structure and data... Please wait...")
        self.update_progress("Connecting...")
        
        def worker():
            try:
                params = self.get_connection_params()
                schema = self.schema_var.get() or 'public'
                batch_size = int(self.batch_size_var.get())
                
                with DatabaseConnection(**params) as db_conn:
                    if not db_conn.connection:
                        raise Exception("Unable to establish connection")
                    
                    self.root.after(0, lambda: self.update_progress("Creating structure..."))
                    
                    structure_exporter = StructureExporter(db_conn)
                    data_exporter = DataExporter(db_conn)
                    
                    sql_code = generate_sql_header(params['database'])
                    sql_code += structure_exporter.export_all_structures(schema=schema)
                    
                    self.root.after(0, lambda: self.update_progress("Generating data..."))
                    sql_code += data_exporter.export_all_data(schema=schema, batch_size=batch_size)
                    
                    self.root.after(0, lambda: self.show_sql_in_text_widget(sql_code))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Structure and data successfully generated"))
            
            except Exception as e:
                self.root.after(0, lambda: self.sql_text.delete(1.0, tk.END))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error while generating: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.update_progress(""))
        
        Thread(target=worker, daemon=True).start()
    
    def save_sql_file(self):
        """Save the SQL in a file"""
        if not self.current_sql_code or not self.current_sql_code.strip():
            messagebox.showwarning("Caution", "There is no SQL code to save.")
            return
        
        if "Por favor espere..." in self.current_sql_code:
            messagebox.showwarning("Caution", "Generation is in progress. Please wait.")
            return
        
        # Generate default file name
        database_name = self.database_entry.get().strip() or "database"
        default_filename = generate_filename(database_name)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            initialfile=default_filename,
            title="Save SQL file",
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
        )
        
        if file_path:
            if FileHandler.save_sql_file(self.current_sql_code, file_path):
                file_info = FileHandler.get_file_info(file_path)
                messagebox.showinfo("Success", 
                    f"File saved successfully:\n{file_path}\n\nSize: {file_info.get('size_formatted', 'N/A')}")
            else:
                messagebox.showerror("Error", "Error while saving the file")
    
    def clear_sql(self):
        """Clear the SQL text area"""
        self.sql_text.delete(1.0, tk.END)
        self.current_sql_code = ""
        self.info_label.config(text="")
        self.progress_var.set("")
    
    def copy_to_clipboard(self):
        """Copy the SQL content to the clipboard"""
        if not self.current_sql_code or not self.current_sql_code.strip():
            messagebox.showwarning("Caution", "There is no SQL code to copy.")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_sql_code)
            self.root.update()
            messagebox.showinfo("Success", "SQL code copied to clipboard")
        except Exception as e:
            messagebox.showerror("Succcess", f"Error copying to clipboard: {str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()