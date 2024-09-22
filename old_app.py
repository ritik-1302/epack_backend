from flask import Flask, request, jsonify
import ezdxf
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from ezdxf.math import Vec2

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def hello_world():
    return 'Hello, World!'

lines_info = []
block_names = []
data = []
all_vertices = []
density = 1

def get_block_names(doc):
    block_records = doc.blocks
    for block in block_records:
        if block.name.startswith('detail_'):
            block_names.append(block.name)

def create_record(block_name, length, width, area):
    # Swap length and width if length is less than width
    if length < width:
        length, width = width, length
    parts = block_name.split('_')
    thickness = int(parts[-2])
    quantity = parts[-1]
    volume = area * float(thickness)
    data.append({
        'Block Name': parts[1].upper(),
        'Thickness (mm)': thickness,
        'Quantity': quantity,
        'Length (mm)': length,
        'Width (mm)': width,
        'Area (m2)': area,
        'Volume (m3)': volume,
        'Weight (kg)': volume * float(density),
    })

def check_entity_types_in_block(doc, block_name):
    # Access the specified block
    block = doc.blocks.get(block_name)
    if block is None:
        return None, "Block not found"

    # Track the types of entities in the block
    entity_types = set()

    # Iterate through each entity in the block
    for entity in block:
        entity_types.add(entity.dxftype())

    # Check if there is only one unique entity type
    if len(entity_types) == 1:
        if 'LWPOLYLINE' in entity_types:
            get_polyline_dimensions_and_area(doc, block_name)
        if 'LINE' in entity_types:
            get_line_dimensions(doc, block_name)
    elif len(entity_types) == 2:
        if 'LWPOLYLINE' in entity_types and 'LINE' in entity_types:
            get_line_and_polyline_dimensions_and_area(doc, block_name)
    else:
        pass

def get_all_vertices(block):
    vertices = []
    # Collect vertices from lines and polylines
    for entity in block:
        if entity.dxftype() == 'LINE':
            # Extract only X and Y for start and end points
            vertices.append((entity.dxf.start.x, entity.dxf.start.y))
            vertices.append((entity.dxf.end.x, entity.dxf.end.y))
        elif entity.dxftype() == 'LWPOLYLINE':
            # Extract only X and Y for each vertex point
            vertices.extend((point[0], point[1]) for point in entity.vertices())  # Corrected to handle vertex tuples directly
    return vertices

def close_loop(vertices):
    # Ensure the vertices form a closed loop
    if not Vec2(vertices[0]).isclose(Vec2(vertices[-1])):
        vertices.append(vertices[0])
    return vertices

def calculate_area_for_lines_and_polylines(vertices):
    # Calculate the area using the Shoelace formula
    n = len(vertices)
    area = 0.0
    for i in range(n-1):
        x1, y1 = vertices[i]
        x2, y2 = vertices[i+1]
        area += x1 * y2 - y1 * x2
    return abs(area) / 2.0

def calculate_bounding_box(vertices):
    # Calculate the bounding box and therefore width and length
    x_coords, y_coords = zip(*vertices)
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    return max_x - min_x, max_y - min_y

def get_line_and_polyline_dimensions_and_area(doc, block_name):
    vertices = get_all_vertices(doc.blocks.get(block_name))
    vertices = close_loop(vertices)
    area = calculate_area_for_lines_and_polylines(vertices)
    width, length = calculate_bounding_box(vertices)
    create_record(block_name, length, width, area)
    all_vertices.append({
                'block_name': block_name,
                'vertices': vertices
            })

def get_line_dimensions(doc, block_name):
    # Access the block
    block = doc.blocks.get(block_name)
    # Get all the lines in the block
    lines = [entity for entity in block if entity.dxftype() == 'LINE']
    # Check for closed loop
    is_closed_loop = is_closed(lines)
    if is_closed_loop:
        area, length, width = calculate_area_and_dim_for_lines(lines)
        all_vertices.append({
                'block_name': block_name,
                'vertices': [(line.dxf.start.x, line.dxf.start.y) for line in lines] + [(lines[-1].dxf.end.x, lines[-1].dxf.end.y)]
            })
        create_record(block_name, length, width, area)

def is_closed(lines):
    # This function checks if the sequence of lines forms a closed loop
    if len(lines) < 3:
        return False
    coordinate_count = {}
    for line in lines:
        # Calculate the length of the line
        length = ((line.dxf.end.x - line.dxf.start.x)**2 + (line.dxf.end.y - line.dxf.start.y)**2)**0.5

        x1, y1 = line.dxf.start.x, line.dxf.start.y
        x2, y2 = line.dxf.end.x, line.dxf.end.y
        # Increment the count for the start and end coordinates
        coordinate_count[(x1, y1)] = coordinate_count.get((x1, y1), 0) + 1
        coordinate_count[(x2, y2)] = coordinate_count.get((x2, y2), 0) + 1
    # Check if each coordinate pair appears exactly twice
    for count in coordinate_count.values():
        if count != 2:
            return False
    return True

def calculate_area_and_dim_for_lines(lines):
    length = max([((line.dxf.end.x - line.dxf.start.x)**2 + (line.dxf.end.y - line.dxf.start.y)**2)**0.5 for line in lines])
    width = min([((line.dxf.end.x - line.dxf.start.x)**2 + (line.dxf.end.y - line.dxf.start.y)**2)**0.5 for line in lines])

    area = 0
    for i in range(len(lines)):
        x1, y1 = lines[i].dxf.start.x, lines[i].dxf.start.y
        x2, y2 = lines[(i+1) % len(lines)].dxf.start.x, lines[(i+1) % len(lines)].dxf.start.y
        area += (x1 * y2 - x2 * y1)

    area = abs(area) / 2
    # Area in m2
    area = area / 1000000

    return area, length, width

def get_polyline_dimensions_and_area(doc, block_name):
    # Access the block
    block = doc.blocks.get(block_name)
    if block is None:
        return f"No block found with name {block_name}"

    # Iterate through each entity in the block
    for entity in block:
        if entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
            vertices = list(entity.vertices())

            x_coords = [v[0] for v in vertices]
            y_coords = [v[1] for v in vertices]

            # Calculate dimensions
            length = max(x_coords) - min(x_coords)
            width = max(y_coords) - min(y_coords)

            # Exchange length and width if length is less than width
            if length < width:
                length, width = width, length

            # Calculate area
            area = 0
            for i in range(len(vertices) - 1):
                area += vertices[i][0] * vertices[i+1][1] - vertices[i+1][0] * vertices[i][1]
            area += vertices[-1][0] * vertices[0][1] - vertices[0][0] * vertices[-1][1]  # Close the loop
            area = abs(area) / 2

            # Area in m2
            area = area / 1000000
            all_vertices.append({
                'block_name': block_name,
                'vertices': vertices
            })

            # Store information
            create_record(block_name, length, width, area)

# Define the upload folder
UPLOAD_FOLDER = 'backend/files'
ALLOWED_EXTENSIONS = {'dxf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    print(filename)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/get_dxf_info', methods=['POST'])
def get_dxf_info():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    print("File received saar")

    dxf_file = request.files['file']
    if dxf_file.filename == '':
        return jsonify({'error': 'No selected file'})

    temp = request.form.get('density')  # Retrieve the density value from the request
    # Convert temp to integer
    density = int(temp)
    print("Density is: ", density)

    if not density:
        return jsonify({'error': 'Density value not provided'})

    if dxf_file and allowed_file(dxf_file.filename):
        # Save the uploaded file
        filename = secure_filename(dxf_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        dxf_file.save(filepath)
        print(filepath)

        try:
            # Read the DXF file
            doc = ezdxf.readfile(filepath)
            get_block_names(doc)

            for block_name in block_names:
                print(block_name)
                check_entity_types_in_block(doc, block_name)

            # Return the data as a JSON array
            return jsonify({'data': data, 'columns': list(data[0].keys()), 'vertices': all_vertices})

        except Exception as e:
            return jsonify({'error': str(e)})
        finally:
            # Clear the data and block names
            data.clear()
            block_names.clear()
            all_vertices.clear()
            #clear the file folder
            # os.remove(filepath)
    else:
        return jsonify({'error': 'Invalid file format'})

if __name__ == '__main__':
    app.run(debug=True)