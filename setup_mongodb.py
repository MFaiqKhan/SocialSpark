#!/usr/bin/env python

"""
Setup script for MongoDB collections and indexes for SocialSpark Orchestrator.

This script initializes the MongoDB collections and creates necessary indexes
for optimal performance. It supports both local MongoDB and MongoDB Atlas.
"""

import argparse
import logging
import sys
import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("socialspark.setup")

def setup_task_storage(client, db_prefix="socialspark"):
    """
    Set up the task storage collections and indexes.
    
    Args:
        client: MongoDB client
        db_prefix: Database name prefix
    """
    db_name = f"{db_prefix}"
    db = client[db_name]
    
    # Create tasks collection if it doesn't exist
    if "tasks" not in db.list_collection_names():
        db.create_collection("tasks")
        logger.info(f"Created tasks collection in {db_name} database")
    
    # Create indexes for tasks collection
    tasks = db.tasks
    tasks.create_index([("status", ASCENDING)])
    tasks.create_index([("source_agent_id", ASCENDING)])
    tasks.create_index([("target_agent_id", ASCENDING)])
    tasks.create_index([("updated_at", DESCENDING)])
    logger.info(f"Created indexes for tasks collection in {db_name} database")

def setup_content_scheduler_storage(client, db_prefix="socialspark"):
    """
    Set up the content scheduler storage collections and indexes.
    
    Args:
        client: MongoDB client
        db_prefix: Database name prefix
    """
    db_name = f"{db_prefix}_content_scheduler"
    db = client[db_name]
    
    # Create posts collection if it doesn't exist
    if "posts" not in db.list_collection_names():
        db.create_collection("posts")
        logger.info(f"Created posts collection in {db_name} database")
    
    # Create scheduler_jobs collection if it doesn't exist
    if "scheduler_jobs" not in db.list_collection_names():
        db.create_collection("scheduler_jobs")
        logger.info(f"Created scheduler_jobs collection in {db_name} database")
    
    # Create indexes for posts collection
    posts = db.posts
    posts.create_index([("status", ASCENDING)])
    posts.create_index([("user_id", ASCENDING)])
    posts.create_index([("schedule_time", ASCENDING)])
    posts.create_index([("created_at", DESCENDING)])
    logger.info(f"Created indexes for posts collection in {db_name} database")
    
    # Handle scheduler_jobs index carefully - it might already exist
    scheduler_jobs = db.scheduler_jobs
    try:
        # First check if we need to drop an existing incompatible index
        existing_indexes = list(scheduler_jobs.list_indexes())
        next_run_time_index_exists = False
        
        for index in existing_indexes:
            if 'next_run_time' in index['key']:
                # If the index exists but doesn't have sparse=True, drop it
                if index.get('sparse', False) != True:
                    logger.info(f"Dropping incompatible next_run_time index in {db_name} database")
                    scheduler_jobs.drop_index(index['name'])
                else:
                    next_run_time_index_exists = True
        
        # Only create the index if it doesn't exist or we dropped the incompatible one
        if not next_run_time_index_exists:
            scheduler_jobs.create_index([("next_run_time", ASCENDING)], sparse=True)
            logger.info(f"Created next_run_time index for scheduler_jobs in {db_name} database")
        else:
            logger.info(f"Reusing existing next_run_time index in {db_name} database")
            
    except Exception as e:
        logger.warning(f"Warning handling scheduler_jobs index: {e}")
        logger.info("Continuing setup process...")

def setup_facebook_agent_storage(client, db_prefix="socialspark"):
    """
    Set up the Facebook agent storage collections and indexes.
    
    Args:
        client: MongoDB client
        db_prefix: Database name prefix
    """
    db_name = f"{db_prefix}_facebook_agent"
    db = client[db_name]
    
    # Create facebook_credentials collection if it doesn't exist
    if "facebook_credentials" not in db.list_collection_names():
        db.create_collection("facebook_credentials")
        logger.info(f"Created facebook_credentials collection in {db_name} database")
    
    # Create facebook_posts collection if it doesn't exist
    if "facebook_posts" not in db.list_collection_names():
        db.create_collection("facebook_posts")
        logger.info(f"Created facebook_posts collection in {db_name} database")
    
    # Create indexes
    facebook_credentials = db.facebook_credentials
    facebook_credentials.create_index([("user_id", ASCENDING)], unique=True)
    
    facebook_posts = db.facebook_posts
    facebook_posts.create_index([("socialspark_post_id", ASCENDING)])
    facebook_posts.create_index([("platform_post_id", ASCENDING)])
    facebook_posts.create_index([("publish_time", DESCENDING)])
    
    logger.info(f"Created indexes for Facebook agent collections in {db_name} database")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup MongoDB for SocialSpark Orchestrator")
    parser.add_argument(
        "--mongodb-url", 
        type=str, 
        default=os.getenv("MONGODB_URL", "mongodb://localhost:27017/"),
        help="MongoDB connection URL (for Atlas use: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/)"
    )
    parser.add_argument(
        "--mongodb-db-prefix",
        type=str,
        default=os.getenv("MONGODB_DB_PREFIX", "socialspark"),
        help="Prefix for MongoDB database names"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5000,  # 5 seconds
        help="MongoDB connection timeout in milliseconds"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Continue setup even if some operations fail"
    )
    args = parser.parse_args()
    
    logger.info(f"Connecting to MongoDB at {args.mongodb_url}")
    
    # Configure client with timeouts
    try:
        client = MongoClient(
            args.mongodb_url,
            serverSelectionTimeoutMS=args.timeout,
            connectTimeoutMS=args.timeout,
            socketTimeoutMS=args.timeout
        )
        
        # Test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Set up collections and indexes
        success = True
        
        try:
            setup_task_storage(client, args.mongodb_db_prefix)
        except Exception as e:
            logger.error(f"Error setting up task storage: {e}")
            if not args.force:
                return 1
            success = False
            
        try:
            setup_content_scheduler_storage(client, args.mongodb_db_prefix)
        except Exception as e:
            logger.error(f"Error setting up content scheduler storage: {e}")
            if not args.force:
                return 1
            success = False
            
        try:
            setup_facebook_agent_storage(client, args.mongodb_db_prefix)
        except Exception as e:
            logger.error(f"Error setting up Facebook agent storage: {e}")
            if not args.force:
                return 1
            success = False
        
        if success:
            logger.info("MongoDB setup completed successfully")
        else:
            logger.info("MongoDB setup completed with some errors")
        
    except ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        if "mongodb+srv" in args.mongodb_url:
            logger.error("For MongoDB Atlas connections, ensure:")
            logger.error("1. Your username and password are correctly URL-encoded")
            logger.error("2. Your IP address is whitelisted in Atlas Network Access")
            logger.error("3. Your database user has the appropriate permissions")
        return 1
    except ServerSelectionTimeoutError as e:
        logger.error(f"Server selection timeout: {e}")
        if "mongodb+srv" in args.mongodb_url:
            logger.error("For MongoDB Atlas connections, ensure your cluster is running and accessible")
        else:
            logger.error("For local MongoDB, ensure the MongoDB service is running")
        return 1
    except Exception as e:
        logger.error(f"Error setting up MongoDB: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 