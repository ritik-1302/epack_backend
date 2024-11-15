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
            return user["projects"],user['inventory_access']
        
    
    def make_a_new_project(self,usernames,project_names,is_new):
        
        #update in username 
        for username in usernames:
            user_project_list,blank=self.get_list_of_projects(username=username)
            for projectname in project_names:
                if projectname not in user_project_list:
                    updated= self.project_access_collection.find_one_and_update({"username":username},{"$push":{"projects":projectname}},return_document=True)
        
        # update in admin acessss
        if is_new:
                user_project_list,blank=self.get_list_of_projects(username="epack")
                for projetname in project_names:
                    if projectname not in user_project_list:
                        admin_project_list= self.project_access_collection.find_one_and_update({"username":'epack'},{"$push":{"projects":projetname}},return_document=True)
    
        
        else:
            self.logger.info("Updated the project list of the users")
            return True
        
        
    def remove_project_access(self,project_names,usernames):
        for username in usernames:
            user_project_list=self.get_list_of_projects(username=username)
            for project_name in project_names:
                if project_name in user_project_list:
                    self.project_access_collection.find_one_and_update({"username":username},{"$pull":{"projects":project_name}})
                    
        self.logger.info("Deleted  the projects from the user")
        return True
    
    def get_all_project_access_list(self):
        project_access_list=self.project_access_collection.find({},{"_id":0})
        if project_access_list==[]:
            self.logger.error('no entry in the daatbase')
        else:
            self.logger.info("Sucessfully retrived the list of the all projects")
        
        return list(project_access_list)
        
    def delete_project(self,project_name):
        query_res=self.project_access_collection.update_many({"projects":project_name},{ "$pull": { "projects": project_name } })
        
        
        if query_res.modified_count:
            self.logger.info(f"there is no project named {project_name}")
        else:
            self.logger.info(f"{project_name } project sucessfully deleted")
        
        return query_res
        
        
        
            
if __name__ =="__main__":
    print(ProjectHandler().delete_project('abc'))
    
            
        
        