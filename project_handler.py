from mongodb_handler import MongodbHandler
import logging


class ProjectHandler:
    def  __init__(self):
        mongo=MongodbHandler()
        self.project_access_collection=mongo.mongo_collection('epack_test','project_acess')
        self.logger=logging.getLogger(self.__class__.__name__)
        
        
    def get_list_of_projects(self,username):
        user=self.project_access_collection.find_one({'username':username})
        
        if not user:
            self.logger.error("User didnt exist")
            return False
        
        else:
            self.logger.info(f"Recived the list of project for user {username}")
            return user["projects"]
        
    
    def make_a_new_project(self,username,project_name):
        project_list= self.project_access_collection.find_one_and_update({"username":username},{"$push":{"projects":project_name}},return_document=True)
        print(project_list)
        if not project_list:
            self.logger.error("Username didnt exist")
            return False
        
        else:
            self.logger.info("Updated the project list of the user")
            return True
            
            
        
        
# if __name__ =="__main__":
#     print(ProjectHandler().make_a_new_project('ritik1302','test1302'))
    
            
        
        