import os
import logging
import asyncio
from indexer import Indexer, Config
from pydantic import BaseModel
from async_queue import AsyncQueue
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

indexer = Indexer()
async_queue = AsyncQueue()
router = APIRouter()

class Query(BaseModel):
    query: str

@router.post(
    "/query", 
    response_description='Query local data storage',
)
async def query(request: Query):
    logger.info(f"Received query: {request.query}")
    try:
        result = indexer.find(request.query)
        logger.info(f"Found results for query: {request.query}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in processing query: {e}")
        return {"error": str(e)}
    
@router.post(
    "/embedding", 
    response_description='Get embedding for a query',
)
async def embedding(request: Query):
    logger.info(f"Received embedding request: {request}")
    try:
        result = indexer.embed(request.query)
        logger.info(f"Generated embedding for query: {request.query}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in processing embedding: {e}")
        return {"error": str(e)}

async def crawl_loop(queue: AsyncQueue):
    """Continuously scan for files that need indexing"""
    logger.info(f"Starting crawl loop with scan interval of {indexer.config.SCAN_INTERVAL_MINUTES} minutes")
    
    while True:
        try:
            scan_start_time = datetime.now()
            logger.info(f"Starting periodic scan at {scan_start_time}")
            
            # Get list of files that need indexing
            files_to_index = indexer.get_files_to_index()
            
            # Queue them for indexing
            for file_path in files_to_index:
                await queue.put({
                    "path": file_path,
                    "scan_time": scan_start_time
                })
                logger.info(f"Queued file for indexing: {file_path}")
            
            logger.info(f"Completed scan, found {len(files_to_index)} files to process")
            
            # Wait before next scan using configurable interval
            await asyncio.sleep(indexer.config.SCAN_INTERVAL_SECONDS)
            
        except Exception as e:
            logger.error(f"Error in crawl loop: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying after error

async def index_loop(queue: AsyncQueue, indexer: Indexer):
    """Process files from the queue and index them"""
    while True:
        try:
            # Get next file from queue
            message = await queue.get()
            
            # Process the file
            indexer.index(message)
            
            # Mark task as done
            queue.task_done()
            
        except asyncio.CancelledError:
            logger.info("Index loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in index loop: {e}")
            await asyncio.sleep(5)  # Brief pause before continuing

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Always start the indexing tasks - no more START_INDEXING flag
    tasks = [
        asyncio.create_task(crawl_loop(async_queue)),
        asyncio.create_task(index_loop(async_queue, indexer))
    ]
    
    try:
        yield
    finally:
        # Cleanup on shutdown
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

def create_app() -> FastAPI:
    app = FastAPI(
        openapi_url="/indexer/openapi.json",
        docs_url="/indexer/docs",
        lifespan=lifespan
    )
    app.include_router(router)
    return app

app = create_app()