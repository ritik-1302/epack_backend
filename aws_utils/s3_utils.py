from dotenv import load_dotenv
import os 
import logging
import hashlib
import json 
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

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
        
    
    def upload_data_to_s3(self,project_name:str,string_json_data:str)->str:
        file_name=f"{project_name}/{hashlib.md5(string_json_data.encode()).hexdigest()}"
        try:
            self.s3.put_object(
                Bucket=os.getenv('S3_BUCKET'),
                Key=file_name,
                Body=string_json_data,
                ContentType='application/json'
                
            )
            self.logger.info(f'File {file_name} uploaded successfully to {os.getenv("S3_BUCKET")} S3 BUCKET')
            return file_name

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
            self.logger.info(f"Sucessfully downloaded file {file_name} from {os.getenv('S3_BUCKET')}s3 bucket ")
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
        result =[]
        try :
            project_file_metadata=self.s3.list_objects(Bucket=os.getenv("S3_BUCKET"),Prefix=project_name) 
            
            if 'Contents' in project_file_metadata:
                self.logger.info("Recived Files from the project")
            else:
                self.logger.info("No Files in the Project")
                
            for file_metadata in project_file_metadata['Contents']:
                result.append(file_metadata['Key'])
            
            
            
            
        
        except NoCredentialsError:
            self.logger.error("Error: AWS credentials not found.")
        except PartialCredentialsError:
            self.logger.error("Error: Incomplete AWS credentials.")
        except ClientError as e:
            self.logger.error(f"Error: {e.response['Error']['Message']}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {str(e)}")        
        
        
        return result
        
        
        
        
        
    
    

# if __name__ =="__main__":
#     s3=S3Utils()
#     print(s3.get_files_for_project('test-epack'))