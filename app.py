import os
import json
import logging
import io

from flask import Flask, request, jsonify,abort,Response,send_file,make_response

import ezdxf
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


from dxf_extractor import DXFExtractor
from s3_utils import S3Utils
from  user_handler import UserHandler
from project_handler import ProjectHandler
from excel_generator import ExcelGenerator
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
        hashed_filename = secure_filename(dxf_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], hashed_filename)
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
                hashed_filename=s3_util.upload_data_to_s3(project_name=project_name,string_json_data=json.dumps(result_data),orignal_filename=dxf_file.filename)
                return jsonify({'file_name': hashed_filename })
                
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
    auth=UserHandler()
    data = request.get_json()
    username = data['username']
    password = data['password'].encode('utf-8')
    if auth.register_user(username=username,password=password):
        return jsonify({'success':"User registerd successfully"}),201
    else:
        return jsonify({'error':"Username already exists"}),400
    
    
@app.route('/login',methods=['POST'])
def login():
        auth=UserHandler()
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
    usernames=data['username']
    project_names=data['projectname']
    is_new=data["isnew"]
    
    updated_list=project_handler.make_a_new_project(usernames,project_names,is_new=is_new)
    
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
        
        
@app.route('/get_all_users',methods=['GET'])
def get_all_users():
    user_handler=UserHandler()
    try:
        user_list=user_handler.get_list_of_all_user()
        return jsonify({'data':user_list}),200
    except Exception as e:
        abort(406,description=str(e))
        
@app.route('/download_boq', methods=['GET'])        
def download_boq():
    file_name = request.args.get('filename')
    phase=request.args.get("phase")
    s3_utils = S3Utils()
    

    try:
        # Download data from S3 and parse JSON
        json_body = s3_utils.download_data_from_s3(file_name)
        # dump = json.loads(json_body)

        # Generate Excel file as a binarreturnsy object (assuming generate_excel_for_phase returns file-like object)
        
        excel_generator = ExcelGenerator(json_body)
        excel_file = excel_generator.generate_excel_for_phase(phase_name=phase)

        # Create in-memory file-like object
        output = io.BytesIO()
        excel_file.save(output)
        output.seek(0)

        # Create a response object and set headers
        response = make_response(send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                           as_attachment=True,
                                           download_name=f"{file_name}.xlsx"))
        
        response.headers['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return response

    except Exception as e:
        abort(406, description=str(e))
    

@app.route('/remove_project_access',methods=['DELETE'])
def remove_project_access():
    project_handler=ProjectHandler()
    data = request.get_json()
    usernames=data['username']
    project_names=data['projectname']
    updated_list=project_handler.remove_project_access(project_names=project_names,usernames=usernames)
    
    if updated_list==False:
        return jsonify({'message': 'Invalid Username'}),401
    else:
        return jsonify({'message':'project added sucessfully'}),200
    

@app.route('/get_project_access_list',methods=["GET"])
def get_project_acess_list():
   project_handler= ProjectHandler()
   project_acesss_list=project_handler.get_all_project_access_list()
   
   if project_acesss_list==[]:
        return jsonify({'message': 'No entires found in the colllection'}),401
   else:
        return jsonify({'data':project_acesss_list}),200
    

@app.route('/remove_project',methods=["DELETE"])
def remove_project():
    project_name=request.args.get('projectname')
    project_handler=ProjectHandler()
    res=project_handler.delete_project(project_name=project_name)
    
    if res:
        return jsonify({'message': 'Sucessfully deleted the project'}),200
    else:
        return jsonify({'message': 'Cannot delete the project'}),400    
    
   


if __name__ == '__main__':
    app.run(debug=True)
    