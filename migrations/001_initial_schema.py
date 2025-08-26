"""
Database migration script for AlphaGen Investment Platform
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def run_migration():
    """Run database migration"""
    try:
        # Import after path setup
        from src.database.database import init_database, db_manager
        from src.utils.logger import get_logger
        
        logger = get_logger(__name__)
        logger.info("Starting database migration...")
        
        # Initialize database with all tables and extensions
        await init_database()
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Database migration failed: {e}")
        return False
    finally:
        try:
            await db_manager.close()
        except:
            pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AlphaGen Database Migration")
    parser.add_argument('--force', action='store_true', help='Force migration even if tables exist')
    args = parser.parse_args()
    
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)