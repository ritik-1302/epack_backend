import logging
import bcrypt
from mongodb_handler import MongodbHandler

class UserHandler:
    def __init__(self) -> None:
        mongo=MongodbHandler()
        self.users_collection=mongo.mongo_collection('epack_test','users')
        self.projects_acess_collections=mongo.mongo_collection('epack_test','project_acess')
        self.logger=logging.getLogger(self.__class__.__name__)
        
    def register_user(self,username,password):
        # Check if user already exists
        if self.users_collection.find_one({'username': username}):
            self.logger.error("User already exist")
            return False

        # Hash the password
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        # Store the user in MongoDB
        self.users_collection.insert_one({'username': username, 'password': hashed_password})
        self.projects_acess_collections.insert_one({'username':username,'projects':[],'inventory_access':False})
        self.logger.info("User Succesfully registerd")

        return True
    
    def user_login(self,username,password):
        
        user=self.users_collection.find_one({'username':username})
        
        #check if user exist or not
        if not user:
            self.logger.error("User didnt exist")
            return False
        
        #comparing hash
        if bcrypt.checkpw(password,user['password']):
            self.logger.info("Password matched")
            return True
        else:
            self.logger.error("Password didnt matched")
            False
            
    
    def get_list_of_all_user(self):
        result=[]
        user_list=self.users_collection.find({},{"_id": 0, "username": 1})
        
        if user_list==[]:
            self.logger.error('no user in the project')
        else:
            self.logger.info("Sucessfully retrived the list of the users")
        for user in user_list:
            result.append(user['username'])
            
        return result 
        


# if __name__=="__main__":
#     print(UserHandler().get_list_of_all_user())
    