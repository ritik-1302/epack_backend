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
            return []
        
        else:
            self.logger.info(f"Recived the list of project for user {username}")
            return user["projects"]
        
    
    def make_a_new_project(self,usernames,project_names,is_new):
        
        #update in username 
        for username in usernames:
            user_project_list=self.get_list_of_projects(username=username)
            for projectname in project_names:
                if projectname not in user_project_list:
                    updated= self.project_access_collection.find_one_and_update({"username":username},{"$push":{"projects":projectname}},return_document=True)
        
        # update in admin acessss
        if is_new:
                user_project_list=self.get_list_of_projects(username="epack")
                for projetname in project_names:
                    if projectname not in user_project_list:
                        admin_project_list= self.project_access_collection.find_one_and_update({"username":'epack'},{"$push":{"projects":projetname}},return_document=True)
        
        # if not user_project_list:
        #     self.logger.error("Username didnt exist")
        #     return False
        
        else:
            self.logger.info("Updated the project list of the users")
            return True
        
            
# if __name__ =="__main__":
#     print(ProjectHandler().make_a_new_project('ritik1302','test1302'))
    
            
        
        