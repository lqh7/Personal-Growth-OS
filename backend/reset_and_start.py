"""
Reset database and start backend server.
This script will:
1. Delete the old database
2. Recreate database with new schema (including color field)
3. Start the FastAPI server
"""
import os
import sys
from pathlib import Path

# Get the backend directory
backend_dir = Path(__file__).parent

# Database file path
db_file = backend_dir / "personal_growth_os.db"

# Delete old database if exists
if db_file.exists():
    print(f"🗑️  Deleting old database: {db_file}")
    db_file.unlink()
    print("✅ Old database deleted")
else:
    print("ℹ️  No existing database found")

# Now start the server (database will be auto-created)
print("\n🚀 Starting backend server...")
print("   The database will be automatically created with the new schema")
print("   (including the 'color' field for projects)")
print("\n" + "="*60)

# Import and run the FastAPI app
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.core.config import settings

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
