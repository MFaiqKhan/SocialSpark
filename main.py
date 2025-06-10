"""
SocialSpark Orchestrator - Main Launcher.

This script launches the SocialSpark agent ecosystem with the specified agents.
"""

import os
import sys
import argparse
import asyncio
import logging
from typing import List
import multiprocessing
import signal
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.agents.content_scheduler.agent import ContentSchedulerAgent
from src.agents.platform_posting.facebook.agent import FacebookPostingAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("socialspark.main")


def run_content_scheduler_agent(mongodb_url, db_name="socialspark_content_scheduler"):
    """
    Run the Content & Scheduling Agent.
    
    Args:
        mongodb_url: MongoDB connection URL
        db_name: Database name for this agent
    """
    try:
        # Create and setup the agent
        agent = ContentSchedulerAgent(
            port=8001,
            connection_string=mongodb_url,
            db_name=db_name,
            media_storage_path="./data/media"
        )
        
        # Run the agent - this will start the scheduler and FastAPI
        agent.run()
        
    except KeyboardInterrupt:
        logger.info("Content & Scheduling Agent stopped")
    except Exception as e:
        logger.error(f"Error running Content & Scheduling Agent: {e}")
        import traceback
        logger.error(traceback.format_exc())


def run_facebook_agent(mongodb_url, db_name="socialspark_facebook_agent"):
    """
    Run the Facebook Platform Posting Agent.
    
    Args:
        mongodb_url: MongoDB connection URL
        db_name: Database name for this agent
    """
    try:
        agent = FacebookPostingAgent(
            port=8002,
            connection_string=mongodb_url,
            db_name=db_name
        )
        agent.run()
    except KeyboardInterrupt:
        logger.info("Facebook Platform Posting Agent stopped")
    except Exception as e:
        logger.error(f"Error running Facebook Platform Posting Agent: {e}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="SocialSpark Orchestrator")
    
    parser.add_argument(
        "--agents",
        type=str,
        nargs="+",
        default=["content-scheduler", "facebook"],
        help="Agents to run (options: content-scheduler, facebook)"
    )
    
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
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure data directories exist
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./data/media", exist_ok=True)
    
    logger.info("Starting SocialSpark Orchestrator...")
    logger.info(f"Using MongoDB at: {args.mongodb_url}")
    
    # Construct database names
    cs_db_name = f"{args.mongodb_db_prefix}_content_scheduler"
    fb_db_name = f"{args.mongodb_db_prefix}_facebook_agent"
    
    processes = []
    
    try:
        # Start Content & Scheduler Agent if requested
        if "content-scheduler" in args.agents:
            logger.info(f"Starting Content & Scheduling Agent (DB: {cs_db_name})...")
            cs_process = multiprocessing.Process(
                target=run_content_scheduler_agent,
                args=(args.mongodb_url, cs_db_name)
            )
            cs_process.start()
            processes.append(cs_process)
            
        # Start Facebook Platform Posting Agent if requested
        if "facebook" in args.agents:
            logger.info(f"Starting Facebook Platform Posting Agent (DB: {fb_db_name})...")
            fb_process = multiprocessing.Process(
                target=run_facebook_agent,
                args=(args.mongodb_url, fb_db_name)
            )
            fb_process.start()
            processes.append(fb_process)
            
        # Wait for all processes to complete
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        logger.info("Shutting down SocialSpark Orchestrator...")
        
        # Terminate all processes
        for process in processes:
            if process.is_alive():
                process.terminate()
                
        # Wait for processes to terminate
        for process in processes:
            process.join(timeout=5)
            
        logger.info("All agents stopped")
    
    except Exception as e:
        logger.error(f"Error running SocialSpark Orchestrator: {e}")
        
        # Terminate all processes on error
        for process in processes:
            if process.is_alive():
                process.terminate()


if __name__ == "__main__":
    main() 