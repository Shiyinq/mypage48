#!/usr/bin/env python3
"""
Database Seed Script for JKT48 Members and Setlists

This script contains both the seed data and the seeding logic.
Run manually - NOT exposed as an API endpoint for security.

Usage:
    source .venv/bin/activate
    python scripts/seed_database.py [--members] [--setlists] [--all]
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import database_instance

# JKT48 Active Members Data
def load_members_data():
    """Load members data from JSON file"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'members_seed.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading members data: {e}")
        return []

JKT48_MEMBERS_DATA = load_members_data()

# JKT48 Theater Setlists Data
def load_setlists_data():
    """Load setlists data from JSON file"""
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'setlists_seed.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading setlists data: {e}")
        return []

JKT48_SETLISTS_DATA = load_setlists_data()


async def seed_members(db) -> int:
    """Seed the database with JKT48 member data"""
    collection = db["members"]
    
    # Clear existing data
    await collection.delete_many({})
    
    # Insert new data
    result = await collection.insert_many(JKT48_MEMBERS_DATA)
    return len(result.inserted_ids)


async def seed_setlists(db) -> int:
    """Seed the database with JKT48 setlist data"""
    collection = db["setlists"]
    
    # Clear existing data
    await collection.delete_many({})
    
    # Insert new data
    result = await collection.insert_many(JKT48_SETLISTS_DATA)
    return len(result.inserted_ids)


async def main():
    parser = argparse.ArgumentParser(
        description="Seed the database with JKT48 data"
    )
    parser.add_argument(
        "--members", action="store_true", help="Seed only members data"
    )
    parser.add_argument(
        "--setlists", action="store_true", help="Seed only setlists data"
    )
    parser.add_argument(
        "--all", action="store_true", help="Seed all data (default)"
    )
    
    args = parser.parse_args()
    
    # Default to --all if no specific option is provided
    seed_all = args.all or (not args.members and not args.setlists)
    
    print("=" * 50)
    print("JKT48 Database Seed Script")
    print("=" * 50)
    print("\n⚠️  WARNING: This will DELETE and REPLACE existing data!")
    print("Press Ctrl+C to cancel...\n")
    
    # Wait 3 seconds to give user a chance to cancel
    await asyncio.sleep(3)
    
    print("Initializing database connection...")
    
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            await database_instance.connect()
            await database_instance.database.command("ping")
            print("✓ Successfully connected to MongoDB!")
            break
        except Exception as e:
            print(f"Waiting for database... (Attempt {i+1}/{max_retries}) Error: {e}")
            if i < max_retries - 1:
                await asyncio.sleep(retry_interval)
            else:
                print("✗ Could not connect to database after multiple attempts.")
                sys.exit(1)
    
    try:
        db = database_instance.database
        
        if seed_all or args.members:
            print("\nSeeding members data...")
            members_count = await seed_members(db)
            print(f"✓ Seeded {members_count} members successfully!")
        
        if seed_all or args.setlists:
            print("\nSeeding setlists data...")
            setlists_count = await seed_setlists(db)
            print(f"✓ Seeded {setlists_count} setlists successfully!")
        
        print("\n" + "=" * 50)
        print("Database seeding completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        sys.exit(1)
    finally:
        print("\nClosing database connection...")
        await database_instance.close()


if __name__ == "__main__":
    asyncio.run(main())
