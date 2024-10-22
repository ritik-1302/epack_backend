from dotenv import load_dotenv
import os 
import logging
import time
import hashlib
import json 
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from mongodb_handler import MongodbHandler
from datetime import datetime
import json

class S3Utils:
    def __init__(self) -> None:
        load_dotenv()
        session=boto3.Session(
            aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
            region_name=os.getenv('REGION')
        )
        self.s3=session.client('s3')
        self.logger=logging.getLogger(self.__class__.__name__)
        self.file_metadata_collection=MongodbHandler().mongo_collection("epack_test","file_metadata")
        
        
    
    def upload_data_to_s3(self,project_name:str,string_json_data:str,orignal_filename:str,username:str)->str:
        hashed_file_name=f"{project_name}/{hashlib.md5(string_json_data.encode()).hexdigest()}"
        parts_dict=json.loads(string_json_data)
        table_metadata={}
        for key,value in parts_dict.items():
            table_metadata[key]={"x":0,"y":0,"scale":0.5}
            
        
        
        try:
            self.s3.put_object(
                Bucket=os.getenv('S3_BUCKET'),
                Key=hashed_file_name,
                Body=string_json_data,
                ContentType='application/json'
                
            )
            self.logger.info(f'File {hashed_file_name} uploaded successfully to {os.getenv("S3_BUCKET")} S3 BUCKET')
            if   self.file_metadata_collection.find_one({"hashed_file_name":hashed_file_name,"orginal_file_name":orignal_filename}) :
                  self.logger.info("Attempt to upload duplicate")
            else:
                self.file_metadata_collection.insert_one({"hashed_file_name":hashed_file_name,"orginal_file_name":orignal_filename,"username":username,"time":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"table_metadata":table_metadata})
                self.logger.info(f'File {hashed_file_name} metaData uploaded successfully to MongoDB')
            
            return hashed_file_name

        except NoCredentialsError:
            self.logger.error("Error: AWS credentials not found.")
        except PartialCredentialsError:
            self.logger.error("Error: Incomplete AWS credentials.")
        except ClientError as e:
            self.logger.error(f"Error: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {str(e)}")
       
    
    def download_data_from_s3(self,file_name):
        try:
            response = self.s3.get_object(Bucket=os.getenv('S3_BUCKET'), Key=file_name)
            file_content = response['Body'].read().decode('utf-8')
            self.logger.info(f"Sucessfully downloaded file {file_name} from {os.getenv('S3_BUCKET')} s3 bucket ")
            return json.loads(file_content)
            
        except self.s3.exceptions.NoSuchKey:
            self.logger.error(f"Error: File {file_name} not found in bucket {os.getenv('S3_BUCKET')}.")    
        except NoCredentialsError:
            self.logger.error("Error: AWS credentials not found.")
            
        except PartialCredentialsError:
            self.logger.error("Error: Incomplete AWS credentials.")
            
        except ClientError as e:
            self.logger.error(f"Error: {e.response['Error']['Message']}")
            
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {str(e)}")
            
            
    def get_files_for_project(self,project_name):
        hashed_file_list =[]
       
        try :
            project_file_metadata=self.s3.list_objects(Bucket=os.getenv("S3_BUCKET"),Prefix=project_name) 
            
            if 'Contents' in project_file_metadata:
                self.logger.info("Recived Files from the project")
            else:
                self.logger.info("No Files in the Project")
                
            for file_metadata in project_file_metadata['Contents']:
                hashed_file_list.append(file_metadata['Key'])
            
            self.logger.info("Fetching files from the metadata")
            documents=self.file_metadata_collection.find({
                "hashed_file_name":{"$in":hashed_file_list},
                
            },{"_id":0})
           
            
            return list(documents)
            
            
            
            
           
            
            
        
        except NoCredentialsError:
            self.logger.error("Error: AWS credentials not found.")
        except PartialCredentialsError:
            self.logger.error("Error: Incomplete AWS credentials.")
        except ClientError as e:
            self.logger.error(f"Error: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {str(e)}")        
        
        
       
        
        
        
        
        
    
    

if __name__ =="__main__":
    s3=S3Utils()
    print(s3.get_files_for_project('epack-test'))