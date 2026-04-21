import os
import sys
import shutil
import zipfile
from io import BytesIO
import time

from minio import Minio

# Add the project root to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Settings
from src.logging_config import create_logger

# Use a clean logger
logger = create_logger("backup_bucket", __name__)

def main():
    settings = Settings()
    
    # Initialize Client (similar logic to StorageRepository)
    endpoint = settings.storage_endpoint
    endpoint = endpoint.replace("https://", "").replace("http://", "").strip("/")
    
    client = Minio(
        endpoint,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        secure=settings.storage_secure,
    )
    
    bucket_name = settings.storage_bucket
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    temp_dir = f"temp_backup_{timestamp}"
    zip_filename = f"backup_{bucket_name}_{timestamp}.zip"
    
    logger.info(f"Starting bucket backup: {bucket_name}")
    
    try:
        # 1. List all objects
        objects = client.list_objects(bucket_name, recursive=True)
        
        # 2. Download to temp directory
        file_count = 0
        for obj in objects:
            if obj.is_dir:
                continue
            
            local_path = os.path.join(temp_dir, obj.object_name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            logger.info(f"Downloading: {obj.object_name}...")
            client.fget_object(bucket_name, obj.object_name, local_path)
            file_count += 1
            
        if file_count == 0:
            logger.warning("Bucket is empty or no files found.")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return

        # 3. Create ZIP
        logger.info(f"Backing up {file_count} files to {zip_filename}...")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    
        # 4. Cleanup
        shutil.rmtree(temp_dir)
        
        logger.info(f"Finished! Backup successfully saved at: {os.path.abspath(zip_filename)}")
        print(f"\n--- SUCCESS ---")
        print(f"File backup: {zip_filename}")
        print(f"Total files: {file_count}")
        
    except Exception as e:
        logger.error(f"Failed to perform backup: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
