import logging
from mongodb_handler import MongodbHandler

class LayoutHandler:
    def __init__(self):
        mongo=MongodbHandler()
        self.file_metadata_collection=mongo.mongo_collection('epack_test','file_metadata')
        self.logger=logging.getLogger(self.__class__.__name__)
    
    def update_layout(self,table_metadata_object,hashed_filename):
        self.file_metadata_collection.update_one(
            {"hashed_file_name": hashed_filename},
            {"$set": {"table_metadata": table_metadata_object}}
        )
        self.logger.info("Succesfully updated the info of the layout")