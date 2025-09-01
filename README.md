# PostgreSQL Database Exporter

A tool with a graphical interface for exporting PostgreSQL databases to SQL files, allowing you to export the structure, the data, or both.
<img width="901" height="532" alt="image" src="https://github.com/user-attachments/assets/50d546ad-8ed8-41ca-aa73-0a73cebf751d" />
<img width="900" height="530" alt="image" src="https://github.com/user-attachments/assets/c13eafff-0549-43fa-b1ac-5f603008a4e7" />
<img width="899" height="843" alt="image" src="https://github.com/user-attachments/assets/226d5c29-232f-4eda-aa4f-588523cee2c3" />

## Features

- 🗄️ **Complete export**: PostgreSQL table structure and data
- 🎯 **Selective export**: Structure only or data only
- 🖥️ **Intuitive graphical interface**: Easy to use with tkinter
- 📊 **Batch processing**: Configurable for large tables
- 💾 **Multiple output formats**: View and download SQL files
- 🔒 **Secure connections**: Support for PostgreSQL authentication
- 📋 **Additional features**: Copy to clipboard, clear, etc.

## Requirements

- Python 3.7+
- PostgreSQL (any version compatible with psycopg2)

## Installation

1. **Clone the repository:**
```bash
  git clone https://github.com/BNN0/PostgreSQLExporter.git
  cd postgresql-exporter
  ```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Usage

### Graphical Interface

Run the application:
```bash
python main.py
```

#### Steps to use:

1. **Configure connection:**
   - Host: PostgreSQL server address
   - Port: connection port (default 5432)
   - Database: database name
   - User and password: access credentials

2. **Test connection** (optional but recommended)

3. **Configure options:**
   - Batch size: number of records per query
   - Schema: schema to export (default ‘public’)

4. **Select export type:**
   - **Structure only**: Generates CREATE TABLE, constraints, sequences
   - **Data only**: Generates INSERT statements
   - **Structure + Data**: Complete export

5. **Save result:**
   - Display on screen
   - Save as .sql file
   - Copy to clipboard

### Programmatic Use

```python
from src.database.connection import DatabaseConnection
from src.database.structure import StructureExporter
from src.database.data import DataExporter

# Configure connection
params = {
    'host': 'localhost',
    'database': 'my_db',
    'user': 'user',
    'password': 'password',
    'port': 5432
}

# Use context manager
with DatabaseConnection(**params) as db_conn:
    # Export structure only
    structure_exporter = StructureExporter(db_conn)
    structure_sql = structure_exporter.export_all_structures()
    
    # Only export data
    data_exporter = DataExporter(db_conn)
    data_sql = data_exporter.export_all_data(batch_size=1000)
    
    print(structure_sql)
    print(data_sql)
```

## Project Structure

```
postgresql_exporter/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
│
├── src/                   # Source code
│   ├── __init__.py
│   ├── database/         # DB modules
│   │   ├── __init__.py
│   │   ├── connection.py # Connections
│   │   ├── structure.py  # Structure export
│   │   └── data.py       # Data export
│   │
│   ├── utils/            # Utilities
│   │   ├── sql_formatter.py # SQL formatting
│   │   └── file_handler.py  # File handling
│   │
│   └── gui/              # Graphical interface
│       ├── __init__.py
│       ├── main_window.py   # Main window
│       └── dialogs.py      # Dialogues
│
└── README.md              # Documentation
```

## Technical Features

### Structure Export

- ✅ Tables with precise data types
- ✅ Constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK)
- ✅ Sequences and auto-increment
- ✅ Handling of identifiers with special characters
- ✅ Support for different schemas

### Data Export

- ✅ Batch processing (configurable)
- ✅ Correct escaping of special characters
- ✅ Handling of data types (strings, numbers, dates, booleans, NULL)
- ✅ Visual progress for large tables
- ✅ Memory optimization

### User Interface

- ✅ Connection field validation
- ✅ Connection test before exporting
- ✅ Progress indicators
- ✅ Error handling with clear messages
- ✅ Asynchronous operations (does not block the UI)

## Advanced Configuration

### Modify default batch size

In `src/gui/main_window.py`:
```python
self.batch_size_var = tk.StringVar(value=“5000”)  # Change from 1000 to 5000
```

### Add additional schemas

The application supports any schema. Simply change the value in the interface or programmatically:

```python
structure_sql = structure_exporter.export_all_structures(schema=‘my_schema’)
```

## Troubleshooting

### Connection error

1. Verify that PostgreSQL is running
2. Confirm host, port, and credentials
3. Verify user permissions in the database
4. Check the `pg_hba.conf` configuration if necessary

### Memory issues with large tables

1. Reduce batch size
2. Export tables individually
3. Consider using only structure if the data is very large

### Special characters in names

The application automatically handles identifiers with:
- Capital letters
- Spaces
- Special characters
- Reserved words

## Contribute

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am ‘Add new feature’`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Support

To report bugs or request new features, please create an issue in the GitHub repository.

---

**Note**: This tool is designed for use in development and testing. For production use, consider using official tools such as `pg_dump` for critical cases.
