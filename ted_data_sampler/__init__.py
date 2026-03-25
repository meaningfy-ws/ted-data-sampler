from dotenv import load_dotenv
from ted_sws import MongoDBConfig

load_dotenv()

STANDARD_TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

config = MongoDBConfig()
