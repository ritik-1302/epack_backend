import logging

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongodbHandler:
    def __init__(self) -> None:
        self.uri = "mongodb+srv://vulture1302:ba6lLAq2rHl58PSG@cluster0.lcz7v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&ssl=true"
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        self.logger=logging.getLogger(self.__class__.__name__)
        try:
            self.client.admin.command('ping')
            self.logger.info("You are successfully connected to MongoDB!")
        except Exception as e:
            self.logger.error(str(e))
        
        
    def mongo_collection(self,database_name,collection):
        return self.client[database_name][collection]
    