"""Script untuk sync current schedule events ke MongoDB."""
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Change working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from pymongo.collection import Collection

from jkt48scraper import fetch_schedule_data


def parse_date(date_value) -> datetime:
    """Parse date string to datetime object.
    
    MongoDB akan menyimpan dengan format: 2011-12-17T00:00:00.000+00:00
    """
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try other common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_value, fmt)
            except ValueError:
                continue
    
    raise ValueError(f"Cannot parse date: {date_value}")


def prepare_event_for_db(event: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare event data for MongoDB insertion."""
    # Create a copy to avoid modifying original
    db_event = event.copy()
    
    # Ensure date is datetime object
    if 'date' in db_event:
        db_event['date'] = parse_date(db_event['date'])
    
    # Add metadata
    db_event['updatedAt'] = datetime.now()
    
    return db_event


def upsert_events(collection: Collection, events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Upsert events to MongoDB collection based on event id."""
    stats = {
        'inserted': 0,
        'updated': 0,
        'errors': 0
    }
    
    for event in events:
        try:
            # Prepare event for database
            db_event = prepare_event_for_db(event)
            event_id = db_event.get('id')
            
            if not event_id:
                print(f"  ⚠️  Skipping event without id: {db_event.get('title', 'Unknown')}")
                stats['errors'] += 1
                continue
            
            # Upsert: update if exists, insert if not
            result = collection.update_one(
                {'id': event_id},  # Filter by event id
                {'$set': db_event},  # Update with new data
                upsert=True  # Insert if not found
            )
            
            if result.upserted_id:
                stats['inserted'] += 1
                print(f"  ✅ Inserted: {db_event.get('title', 'Unknown')} (ID: {event_id})")
            elif result.modified_count > 0:
                stats['updated'] += 1
                print(f"  🔄 Updated: {db_event.get('title', 'Unknown')} (ID: {event_id})")
            else:
                print(f"  ⏭️  No change: {db_event.get('title', 'Unknown')} (ID: {event_id})")
                
        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Error processing event: {e}")
    
    return stats


def main():
    """Main function to sync current schedule to MongoDB."""
    # MongoDB connection settings
    # Default to localhost, can be overridden with environment variable
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'mypage48')
    collection_name = 'events'
    
    print("=" * 50)
    print("JKT48 Schedule to MongoDB Sync")
    print("=" * 50)
    print(f"\n📡 MongoDB URI: {mongo_uri}")
    print(f"📂 Database: {db_name}")
    print(f"📁 Collection: {collection_name}")
    
    # Connect to MongoDB
    print("\n🔌 Connecting to MongoDB...")
    try:
        client = MongoClient(mongo_uri)
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    db = client[db_name]
    collection = db[collection_name]
    
    # Fetch current schedule data
    print("\n📅 Fetching current schedule from JKT48...")
    try:
        schedule_data = fetch_schedule_data()
        events = schedule_data.get('events', [])
        print(f"✅ Fetched {len(events)} events")
    except Exception as e:
        print(f"❌ Failed to fetch schedule: {e}")
        client.close()
        sys.exit(1)
    
    if not events:
        print("⚠️  No events to sync")
        client.close()
        return
    
    # Upsert events to MongoDB
    print(f"\n💾 Upserting {len(events)} events to MongoDB...")
    stats = upsert_events(collection, events)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SYNC SUMMARY")
    print("=" * 50)
    print(f"  📥 Inserted: {stats['inserted']}")
    print(f"  🔄 Updated:  {stats['updated']}")
    print(f"  ❌ Errors:   {stats['errors']}")
    print(f"  📊 Total:    {len(events)}")
    
    # Close connection
    client.close()
    print("\n✅ Sync completed!")


if __name__ == '__main__':
    main()
