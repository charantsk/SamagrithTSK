from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
import os
import base64
from PIL import Image
from io import BytesIO
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

STATIC_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
THUMBNAIL_SIZE = (200, 200)  # Define thumbnail size

# Ensure the static image folder exists
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Resources Table
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    post_body = db.Column(db.Text)
    post_summary = db.Column(db.String(500))
    main_image = db.Column(db.String(500))
    thumbnail_image = db.Column(db.String(500))
    featured = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(50))
    col_span = db.Column(db.Integer, default=1)
    service_category = db.Column(db.String(200))
    normal_category = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cms_link = db.Column(db.String(500))

    def generate_cms_link(self):
        return f"/cms/resource/{self.slug}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'post_body': self.post_body,
            'post_summary': self.post_summary,
            'main_image': self.main_image,
            'thumbnail_image': self.thumbnail_image,
            'featured': self.featured,
            'color': self.color,
            'col_span': self.col_span,
            'service_category': self.service_category,
            'normal_category': self.normal_category,
            'created_at': self.created_at.isoformat(),
            'cms_link': self.cms_link

        }



# Jobs Table
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cms_link = db.Column(db.String(500))

    def generate_cms_link(self):
        return f"/cms/job/{self.id}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'cms_link': self.cms_link
        }



# Basic CMS template
CMS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ item.name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .navbar {
            background-color: #004d00;
            color: #fff;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar a {
            color: #fff;
            text-decoration: none;
            margin: 0 10px;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .content {
            max-width: 100%;
            margin: 20px;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .header {
            margin-bottom: 20px;
            text-align: left;
        }
        .header h1 {
            color: #004d00;
            margin-bottom: 10px;
        }
        .metadata {
            color: #666;
            margin: 10px 0;
            font-size: 14px;
            text-align: left;
        }
        .metadata p {
            margin: 5px 0;
        }
        .image-container {
            display: flex;
            justify-content: left;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .description {
            text-align: justify;
            margin-top: 20px;
        }

        .logo {
            display: flex;
            gap:20px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            <img src="{{ url_for('static', filename='images/samagrith-logo-in-nav-bar-p-500.png') }}" width="80" height="80" alt="Main Image">
            <h1>SAMAGRITH</h1> 
        </div>
        <div class="links">
            <a href="#">About Us</a>
            <a href="#">Team</a>
            <a href="#">Our Services</a>
            <a href="#">Resources</a>
            <a href="#">Engage with Us</a>
        </div>
    </div>
    
    <div class="content">
        <div class="header">
            <h1>{{ item.name }}</h1>
        </div>

        <div class="metadata">
            <p><strong>Category:</strong> {{ item.service_category or item.normal_category }}</p>
            <p><strong>Posted On:</strong> {{ item.post_date }}</p>
        </div>

        <div class="image-container">
            {% if item.main_image %}
                <img src="{{ url_for('static', filename='images/' + item.main_image) }}" alt="Main Image">
            {% endif %}
            {% if item.thumbnail_image %}
                <img src="{{ url_for('static', filename='images/' + item.thumbnail_image) }}" alt="Thumbnail">
            {% endif %}
        </div>

        <div class="description">
            <p>{{ item.post_summary }}</p>
            <div>{{ item.post_body | safe }}</div>
        </div>
    </div>
</body>
</html>
"""



# Routes for Resources
@app.route('/api/resources', methods=['POST'])
def create_resource():
    try:
        data = request.json

        # Extract and decode the base64 image
        main_image_b64 = data.get('main_image')
        if not main_image_b64:
            return jsonify({'error': 'main_image is required'}), 400

        print("Main Image :",main_image_b64[:10])
        # Decode base64 and save as an image
        if main_image_b64.startswith("data:image/png;base64,"):
            main_image_b64 = main_image_b64.split(",")[1] # Remove base64 prefix
        
        image_data = base64.b64decode(main_image_b64)
        image = Image.open(BytesIO(image_data))

        # Generate filenames
        filename = f"{data['slug']}.png"
        thumbnail_filename = f"{data['slug']}_thumb.png"

        # Define full paths
        main_image_path = os.path.join(STATIC_FOLDER, filename)
        thumbnail_path = os.path.join(STATIC_FOLDER, thumbnail_filename)

        # Save the main image
        image.save(main_image_path, format="PNG")
        
        # Create and save a thumbnail
        image.thumbnail(THUMBNAIL_SIZE)
        image.save(thumbnail_path, format="PNG")

        # Store paths in the database
        new_resource = Resource(
            name=data['name'],
            slug=data['slug'],
            post_body=data.get('post_body'),
            post_summary=data.get('post_summary'),
            main_image=filename,  # Store relative path
            thumbnail_image=thumbnail_filename,
            featured=data.get('featured', False),
            color=data.get('color'),
            col_span=data.get('col_span', 1),
            service_category=data.get('service_category'),
            normal_category=data.get('normal_category')
        )

        new_resource.cms_link = "http://127.0.0.1:5000" + new_resource.generate_cms_link()
        db.session.add(new_resource)
        db.session.commit()

        return jsonify({'message': 'Resource created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Routes for Jobs
@app.route('/api/jobs', methods=['POST'])
def create_job():
    try:
        data = request.json
        new_job = Job(
            name=data['name'],
            title=data['title'],
            description=data.get('description')
        )

        new_job.cms_link = new_job.generate_cms_link()
        db.session.add(new_job)
        db.session.commit()
        return jsonify({'message': 'Job created successfully', 'job': new_job.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400



# Dynamic CMS Pages
@app.route('/cms/<item_type>/<identifier>')
def cms_page(item_type, identifier):
    if item_type == 'resource':
        item = Resource.query.filter_by(slug=identifier).first_or_404()
    elif item_type == 'job':
        item = Job.query.get_or_404(identifier)
    else:
        return jsonify({'error': 'Invalid item type'}), 400

    return render_template_string(CMS_TEMPLATE, item=item, item_type=item_type)

# Get Resources
@app.route('/api/resources', methods=['GET'])
def get_resources():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = Resource.query.order_by(desc(Resource.created_at)).paginate(
        page=page, per_page=per_page, error_out=False)
    
    resources = pagination.items

    return jsonify({
        'resources': [resource.to_dict() for resource in resources],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })



# Get Jobs
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = Job.query.order_by(desc(Job.created_at)).paginate(
        page=page, per_page=per_page, error_out=False)

    jobs = pagination.items

    return jsonify({
        'jobs': [job.to_dict() for job in jobs],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })

# Update Resource by Name
@app.route('/api/resources/<int:id>', methods=['PUT'])
def update_resource(id):
    try:
        resource = Resource.query.get(id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404

        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update only provided fields
        updatable_fields = {
            'name', 'slug', 'post_body', 'post_summary', 'main_image', 'thumbnail_image',
            'featured', 'color', 'col_span', 'service_category', 'normal_category'
        }

        for key, value in data.items():
            if key in updatable_fields:
                setattr(resource, key, value)

        # Regenerate CMS link if needed
        resource.cms_link = resource.generate_cms_link()

        db.session.commit()
        return jsonify({'message': 'Resource updated successfully', 'resource': resource.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Delete Resource by Name
@app.route('/api/resources', methods=['DELETE'])
def delete_resource():
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'Resource name is required'}), 400

        resource = Resource.query.filter_by(name=name).first()
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404

        db.session.delete(resource)
        db.session.commit()
        return jsonify({'message': 'Resource deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)