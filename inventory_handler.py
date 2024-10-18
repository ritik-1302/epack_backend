import logging

from mongodb_handler import MongodbHandler


class InventoryHandler:
    def __init__(self):
        mongo=MongodbHandler()
        self.inventory_collection=mongo.mongo_collection('epack_test','inventory')
        self.project_access_collection=mongo.mongo_collection('epack_test', 'project_acess')
        self.logger=logging.getLogger(self.__class__.__name__)
    
    def get_inventory_list(self):
        inventory_list=self.inventory_collection.find({},{"_id":0})
        if inventory_list==[]:
            self.logger.error('no entry in the database')
        else:
            self.logger.info("Sucessfully retrived the list of the all Inventory")
        
        return list(inventory_list)
    
    def create_inventory_item(self,item):
        inventory_list=self.get_inventory_list()
        if item in inventory_list:
            self.logger.error(f"{item} already exists in the inventory")
        else:
            self.inventory_collection.insert_one(item)
            self.logger.info(f"Sucessfully created the inventory item {item}")
            
    def delete_inventory_item(self, item):
        inventory_list=self.get_inventory_list()
        if item not in inventory_list:
            self.logger.error(f"{item} does not exists in the inventory")
        else:
            self.inventory_collection.delete_one(item)
            self.logger.info(f"Sucessfully deleted the inventory item {item}")
            
            
    def update_inventory_access(self,users):
        self.project_access_collection.update_many(
        {"username": {"$in": users}},  # Filter documents where username is in the list
        {"$set": {"inventory_access": True}}  # Set inventory_access to True
        )
        self.logger.info(f"Sucessfully updated the inventory access for the users {users}")
             
    def revoke_inventory_access(self,users):
        self.project_access_collection.update_many(
        {"username": {"$in": users}},  # Filter documents where username is in the list
        {"$set": {"inventory_access": False}}  # Set inventory_access to True
        )
        self.logger.info(f"Sucessfully revoked the inventory access for the users {users}")
             
        


   
    


if __name__ == "__main__":
    print(InventoryHandler().get_inventory_list())