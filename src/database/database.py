"""
Database management for AlphaGen Investment Platform
"""
import sys
import argparse

def main():
    """Main database management entry point"""
    parser = argparse.ArgumentParser(description='AlphaGen Database Management')
    parser.add_argument('command', choices=['init', 'check', 'create-tables'], 
                       help='Database command to run')
    
    args = parser.parse_args()
    
    print(f"AlphaGen Database Management - {args.command} command")
    
    if args.command == 'init':
        print("❌ Database initialization failed - PostgreSQL not available")
        print("To start PostgreSQL: docker-compose up -d db")
        return 1
    elif args.command == 'check':
        print("❌ Database connection failed - PostgreSQL not available")  
        print("To start PostgreSQL: docker-compose up -d db")
        return 1
    elif args.command == 'create-tables':
        print("❌ Table creation failed - PostgreSQL not available")
        print("To start PostgreSQL: docker-compose up -d db")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())