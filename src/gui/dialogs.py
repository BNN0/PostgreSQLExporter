"""
Dialog boxes and secondary windows for the application
"""

import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from ..database.connection import DatabaseConnection

class ConnectionTestDialog:
    """Dialog box for testing database connection"""
    
    def __init__(self, parent, connection_params: dict):
        self.parent = parent
        self.connection_params = connection_params
        self.result = None
        self.dialog = None
        
    def show(self) -> bool:
        """Displays the dialog and returns True if the connection was successful."""
        self.create_dialog()
        self.test_connection()
        
        # Wait for the dialog box to close
        self.parent.wait_window(self.dialog)
        
        return self.result is not None and self.result[0]
    
    def create_dialog(self):
        """Create the dialog box"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Testing Connection")
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center in parent window
        self.center_dialog()
        
        # Content
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Testing connection to PostgreSQL...", 
                              font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Connection information
        info_frame = ttk.LabelFrame(main_frame, text="Connection Data", padding="10")
        info_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(info_frame, text=f"Host: {self.connection_params['host']}:{self.connection_params['port']}").pack(anchor="w")
        tk.Label(info_frame, text=f"Database: {self.connection_params['database']}").pack(anchor="w")
        tk.Label(info_frame, text=f"User: {self.connection_params['user']}").pack(anchor="w")
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.start()
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Connecting...", fg="blue")
        self.status_label.pack()
        
        # Frame for buttons
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(side="bottom", fill="x", pady=(20, 0))
    
    def center_dialog(self):
        """Center the dialog in the parent window"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def test_connection(self):
        """Test the connection in a separate thread"""
        def worker():
            try:
                db_conn = DatabaseConnection(**self.connection_params)
                success, message = db_conn.test_connection()
                
                self.dialog.after(0, lambda: self.show_result(success, message))
                
            except Exception as e:
                self.dialog.after(0, lambda: self.show_result(False, f"Error inesperado: {str(e)}"))
        
        Thread(target=worker, daemon=True).start()
    
    def show_result(self, success: bool, message: str):
        """Display the test result"""
        self.result = (success, message)
        
        # Stop progress bar
        self.progress.stop()
        self.progress.pack_forget()
        
        # Update status
        if success:
            self.status_label.config(text="✅ Successful connection", fg="green")
        else:
            self.status_label.config(text="❌ Connection error", fg="red")
        
        # Show detailed message
        message_frame = ttk.Frame(self.dialog)
        message_frame.pack(fill="x", padx=20, pady=10)
        
        message_text = tk.Text(message_frame, height=4, wrap=tk.WORD)
        message_text.pack(fill="x")
        message_text.insert("1.0", message)
        message_text.config(state="disabled")
        
        # Add close button
        ttk.Button(self.button_frame, text="Close", 
                  command=self.close_dialog).pack()
    
    def close_dialog(self):
        """Close the dialog box"""
        if self.dialog:
            self.dialog.destroy()

class TableSelectionDialog:
    """Dialog box for selecting specific tables"""
    
    def __init__(self, parent, tables: list):
        self.parent = parent
        self.tables = tables
        self.selected_tables = []
        self.dialog = None
        
    def show(self) -> list:
        """Display the dialog and return the selected tables"""
        if not self.tables:
            messagebox.showwarning("Caution", "No tables available")
            return []
        
        self.create_dialog()
        
        # Wait for the dialog box to close
        self.parent.wait_window(self.dialog)
        
        return self.selected_tables
    
    def create_dialog(self):
        """Create the dialog box"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Tables")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Select tables to export", 
                              font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame for scrollable checkboxes
        list_frame = ttk.LabelFrame(main_frame, text="Tables available", padding="10")
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Scrollable frame
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Variables for checkboxes
        self.table_vars = {}
        
        for table in self.tables:
            var = tk.BooleanVar(value=True)  
            self.table_vars[table] = var
            
            checkbox = tk.Checkbutton(scrollable_frame, text=table, variable=var)
            checkbox.pack(anchor="w", padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(control_frame, text="Select All", 
                  command=self.select_all).pack(side="left", padx=(0, 5))
        ttk.Button(control_frame, text="Deselect Todo", 
                  command=self.deselect_all).pack(side="left")
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Accept", 
                  command=self.accept).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side="right")
    
    def select_all(self):
        """Select all tables"""
        for var in self.table_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deselect all tables"""
        for var in self.table_vars.values():
            var.set(False)
    
    def accept(self):
        """Accept selection"""
        self.selected_tables = [
            table for table, var in self.table_vars.items() 
            if var.get()
        ]
        
        if not self.selected_tables:
            messagebox.showwarning("Caution", "You must select at least one table.")
            return
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel selection"""
        self.selected_tables = []
        self.dialog.destroy()

class ProgressDialog:
    """Progress dialogue for long operations"""
    
    def __init__(self, parent, title="Processing..."):
        self.parent = parent
        self.title = title
        self.dialog = None
        self.cancelled = False
        
    def show(self):
        """Display the progress dialog"""
        self.create_dialog()
        
    def create_dialog(self):
        """Create the dialog box"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Do not allow closing with X
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Starting...", font=("Arial", 10))
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=(0, 20))
        self.progress.start()
        
        # Cancel button
        ttk.Button(main_frame, text="Cancel", 
                  command=self.cancel).pack()
    
    def update_status(self, message: str):
        """Update the status message"""
        if self.dialog:
            self.status_label.config(text=message)
            self.dialog.update_idletasks()
    
    def cancel(self):
        """Cancel the operation"""
        self.cancelled = True
        self.close()
    
    def close(self):
        """Close the dialog box"""
        if self.dialog:
            self.progress.stop()
            self.dialog.destroy()
            self.dialog = None
    
    def on_close(self):
        """Handler for the window close event"""
        self.cancel()
    
    def is_cancelled(self) -> bool:
        """Returns True if the operation was canceled."""
        return self.cancelled