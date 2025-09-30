# 12mo Development Guide

## Quick Start

### Option 1: Enhanced Script (Recommended)
```bash
python start_dev.py
```

### Option 2: Simple Script
```bash
python dev.py
```

### Option 3: Windows Batch (All-in-one)
```bash
start.bat
```

### Option 4: Standard Django
```bash
python manage.py runserver
```

## Server URLs

When the server is running, you can access:

- **Main Application**: http://127.0.0.1:8000/
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Budgets**: http://127.0.0.1:8000/budgets/
- **Categories**: http://127.0.0.1:8000/budgets/categories/
- **Spaces**: http://127.0.0.1:8000/spaces/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## Hot Reload

✅ **Django has built-in hot reload enabled**

- **Python files** (.py): Auto-reload when changed
- **Templates** (.html): Auto-reload when changed
- **Static files** (.css, .js): Served automatically
- **Settings files**: Auto-reload when changed

### What triggers reload:
- Model changes
- View changes
- URL configuration changes
- Template changes
- Settings changes

### What doesn't trigger reload:
- Database schema changes (requires `python manage.py migrate`)
- New apps (requires restart)
- Certain configuration changes

## Development Features

### Enhanced Logging
The development server includes:
- Colored console output
- File watching notifications
- Request/response logging
- Error tracking

### Debug Mode
- DEBUG = True
- Detailed error pages
- Template debugging
- Static file serving
- SQL query logging (optional)

## Stopping the Server

Press `Ctrl+C` to stop the development server gracefully.

## Troubleshooting

### Port Already in Use
If port 8000 is busy, use a different port:
```bash
python manage.py runserver 8001
```

### Virtual Environment
Make sure your virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Dependencies
Install requirements:
```bash
pip install -r requirements.txt
```

## Performance Tips

- Keep the server running while developing
- Use the enhanced scripts for better visibility
- Monitor the console for file change notifications
- Restart only when necessary (new apps, major config changes)

## File Watching

Django watches these file types automatically:
- `*.py` - Python source files
- `*.html` - Django templates
- `*.txt` - Text files (like requirements.txt)
- `config/*.py` - Settings files

Changes to these files will trigger an automatic server reload.