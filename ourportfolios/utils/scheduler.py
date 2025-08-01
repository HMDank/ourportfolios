import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


# Load environment variables
load_dotenv()


class Settings:
    # Establish connection to NeonDB with SQLAlchemy
    connection_string = os.getenv("DATABASE_URL")
    conn = create_engine(url=connection_string)

    # Reload period in seconds
    interval: int = 60 * 60 * 5


db_settings = Settings()

# DB scheduler
executors = {"default": ThreadPoolExecutor(2), "processpool": ProcessPoolExecutor(2)}
db_jobstores = {"default": SQLAlchemyJobStore(url=db_settings.connection_string)}
db_scheduler = BackgroundScheduler(executors=executors, jobstores=db_jobstores)

# internal sheduler
local_scheduler = BackgroundScheduler(executors=executors)
