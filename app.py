import os
import json
import logging

from flask import Flask, request, jsonify,abort
import ezdxf
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


from dxf_extractor import DXFExtractor
from aws_utils.s3_utils import S3Utils
from  auth_handler import AuthHandler
from project_handler import ProjectHandler

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    
#############_________________FLASK APP______________________#################



# Define the upload folder
UPLOAD_FOLDER = 'files'
ALLOWED_EXTENSIONS = {'dxf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log_file.log"),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)

logger=logging.getLogger('main')

def allowed_file(filename):
    print(filename)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#Test Route
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/get_dxf_info', methods=['POST'])
def get_dxf_info():
    #if file is not present give error 406
    if 'file' not in request.files:
        logger.error('No File Provided')
        abort(406,description='No file part')
        
    
    #if file is not selected give error 406
    dxf_file = request.files['file']
    if dxf_file.filename == '':
        logger.error('No File Selected')
        abort(406,description='No selected file')

    #if density  is not present  give error 406
    density = float(request.form.get('density'))
    if not density:
        logger.error('No Density Provided')
        abort(406,description='Density value not provided')
        
    width=float(request.form.get('width'))
    if not width:
        logger.error('No width Provided by browser')
        abort(406,description='Width value not provided by browser')
        
    height=float(request.form.get('height'))
    if not height:
        logger.error('No height Provided by browser')
        abort(406,description='Height value not provided by browser')
        
    project_name=request.form.get('projectName')
    if not project_name:
        logger.error('No project name Provided by user')
        abort(406,description='Project name not provided by user')



    if dxf_file and allowed_file(dxf_file.filename):
        logging.info("DXF File Detected")
        filename = secure_filename(dxf_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        dxf_file.save(filepath)
        logging.info(f"DXF File path {filepath}")
        f=open("counter.txt","r")
        counter=int(f.read())
        f.close()
        f=open("counter.txt","w")
        counter=counter+1
        f.write(str(counter))
        f.close()
        

        try:
            # Read the DXF file
            doc = ezdxf.readfile(filepath)
            logger.info("File read Sucessfully")
            extractor=DXFExtractor(doc=doc,density=density)
            result_data=extractor.extract_parts_from_block(image_width=width,image_height=height)
            s3_util=S3Utils()
            try:
                filename=s3_util.upload_data_to_s3(project_name=project_name,string_json_data=json.dumps(result_data))
                return jsonify({'file_name': filename })
                
            except Exception as e:
                abort(406,description=str(e))
                
        except Exception as e:
            logger.error("Document is not acccording to the format specified")
            abort(406,description=str(e))
        finally:
            os.remove(filepath)
            logger.info(f"Removed file from {filepath}")
    else:
        logger.error("Not a DXF File")
        abort(406,description='Invalid File Format')
        

@app.route('/get_parts_info',methods=['GET'])
def get_parts_info():
    file_name=request.args.get('filename')
    s3_utils=S3Utils()
    try:
         json_body=s3_utils.download_data_from_s3(file_name)
         return jsonify({'data':json_body})
    except Exception as e:
        abort(406,description=str(e))
        
@app.route('/register', methods=['POST'])
def register():
    auth=AuthHandler()
    data = request.get_json()
    username = data['username']
    password = data['password'].encode('utf-8')
    if auth.register_user(username=username,password=password):
        return jsonify({'success':"User registerd successfully"}),201
    else:
        return jsonify({'error':"Username already exists"}),400
    
    
@app.route('/login',methods=['POST'])
def login():
        auth=AuthHandler()
        data = request.get_json()
        username = data['username']
        password = data['password'].encode('utf-8')
        
        if auth.user_login(username=username,password=password):
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message':'Invalid username or password'}),401

@app.route('/get_projects',methods=['GET'])
def get_projects():
    project_handler=ProjectHandler()
    user_name=request.args.get('username')
    project_list=project_handler.get_list_of_projects(username=user_name)
    
    if project_list==False:
        return jsonify({'message': 'Invalid Username'}),401
    else:
        return jsonify({'project_list':project_list}),200
    
    

@app.route('/add_project',methods=['POST'])
def add_project():
    project_handler=ProjectHandler()
    data = request.get_json()
    username=data['username']
    project_name=data['projectname']
    
    updated_list=project_handler.make_a_new_project(username,project_name)
    
    if updated_list==False:
        return jsonify({'message': 'Invalid Username'}),401
    else:
        return jsonify({'message':'project added sucessfully'}),200


@app.route('/get_project_files',methods=['GET'])
def get_project_files():
    projectname=request.args.get('projectname')
    s3_utils=S3Utils()
    try:
         file_list=s3_utils.get_files_for_project(project_name=projectname)
         return jsonify({'data':file_list}),200
    except Exception as e:
        abort(406,description=str(e))
    
    
    
   


if __name__ == '__main__':
    app.run(debug=True)
    