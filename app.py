from flask import Flask, request, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import desc
from enum import Enum
import os
from werkzeug.utils import secure_filename
import time
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.config['UPLOAD_FOLDER'] = "/public_html/medias/"

app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'txt', 'pdf'}

def parse_artifact_type(input_str):
    if not input_str:
        return None

    normalized_input = input_str.strip().lower().replace(" ", "")

    type_map = {
        "video": ArtifactType.Video,
        "gifvideo": ArtifactType.Video,
        "movvideo": ArtifactType.Video,
        "mp4": ArtifactType.Video,

        "photo": ArtifactType.Photo,
        "picture": ArtifactType.Photo,
        "image": ArtifactType.Photo,
        "jpg": ArtifactType.Photo,
        "jpeg": ArtifactType.Photo,
        "png": ArtifactType.Photo,

        "sound": ArtifactType.Sound,
        "audio": ArtifactType.Sound,
        "music": ArtifactType.Sound,
        "mp3": ArtifactType.Sound,
        "wav": ArtifactType.Sound,

        "text": ArtifactType.Text,
        "document": ArtifactType.Text,
        "txt": ArtifactType.Text,
        "pdf": ArtifactType.Text,

        "other": ArtifactType.Other,
        "misc": ArtifactType.Other
    }

    for member in ArtifactType:
        if member.name.lower() == normalized_input:
            return member

    if normalized_input in type_map:
        return type_map[normalized_input]

    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
           
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'qwerteam_admin'
app.config['MYSQL_PASSWORD'] = '5UH$r{=BTthTI71,2Ei9'
app.config['MYSQL_DB'] = 'qwerteam_main_database'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://qwerteam_admin:5UH$r{=BTthTI71,2Ei9@localhost/qwerteam_main_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ArtifactType(Enum):
    Video = 0
    Photo = 1
    Sound = 2
    Text = 3
    Other = 4

class Artifact(db.Model):
    __tablename__ = 'artifacts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    votecount = db.Column(db.Integer, default=0, nullable=False)
    author = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    isNegative = db.Column(db.Boolean, default=False, nullable=False)
    isPositive = db.Column(db.Boolean, default=False, nullable=False)
    emoji = db.Column(db.String(255), nullable=True)
    artyfactType = db.Column(SQLAlchemyEnum(ArtifactType), nullable=False)
    filepath = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    def __repr__(self):
        return f"<Artifact(id={self.id}, title='{self.title}', type={self.artyfactType.name})>"

    def to_dict(self):
        return {
            'id': self.id,
            'votecount': self.votecount,
            'author': self.author,
            'title': self.title,
            'description': self.description,
            'isNegative': self.isNegative,
            'isPositive': self.isPositive,
            'emoji': self.emoji,
            'artyfactType': self.artyfactType.name,
            'filepath': self.filepath,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

def init_db():
    try:
        print("Creating database tables...")
        db.create_all()
        print("Database tables created (if they did not exist).")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")

with app.app_context():
    init_db()

@app.route('/')
def index():
    return "Flask app connected to MySQL using SQLAlchemy. Artifact model defined."

@app.route('/artifacts', methods=['POST'])
def create_artifact():
    title = request.form.get('title')
    author = request.form.get('author')
    artyfact_type_str = request.form.get('artyfactType')
    description = request.form.get('description')
    emoji = request.form.get('emoji')
    isNegative = request.form.get('isNegative', 'false').lower() == 'true'
    isPositive = request.form.get('isPositive', 'false').lower() == 'true'
    votecount = request.form.get('votecount', 0)
    try:
        votecount = int(votecount)
    except ValueError:
        abort(400, description="Invalid votecount format")

    if not title or not author or not artyfact_type_str:
        abort(400, description="Missing required fields (title, author, artyfactType)")

    artifact_type_enum = parse_artifact_type(artyfact_type_str)
    if artifact_type_enum is None:
        abort(400, description="Invalid or unrecognized artyfactType")

    filepath = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            pass
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(upload_path)
            filepath = upload_path

    new_artifact = Artifact(
        votecount=votecount,
        author=author,
        title=title,
        description=description,
        isNegative=isNegative,
        isPositive=isPositive,
        emoji=emoji,
        artyfactType=artifact_type_enum,
        filepath=filepath,
    )

    try:
        db.session.add(new_artifact)
        db.session.commit()
        return jsonify(new_artifact.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error creating artifact: {e}")

@app.route('/artifacts/all', methods=['GET'])
def get_all_artifacts():
    artifacts = Artifact.query.all()
    return jsonify([artifact.to_dict() for artifact in artifacts])

@app.route('/artifacts/<int:artifact_id>', methods=['GET'])
def get_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")
    return jsonify(artifact.to_dict())

@app.route('/artifacts/<int:artifact_id>', methods=['PUT'])
def update_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided")

    if 'author' in data:
        artifact.author = data['author']
    if 'title' in data:
        artifact.title = data['title']
    if 'description' in data:
        artifact.description = data['description']

    if 'isNegative' in data:
        artifact.isNegative = data['isNegative']
    if 'isPositive' in data:
        artifact.isPositive = data['isPositive']
    if 'emoji' in data:
        artifact.emoji = data['emoji']

    if 'artyfactType' in data:
        try:
            artifact.artyfactType = ArtifactType[data['artyfactType']]
        except KeyError:
            abort(400, description="Invalid artyfactType")
    if 'filepath' in data:
        artifact.filepath = data['filepath']

    try:
        db.session.commit()
        return jsonify(artifact.to_dict())
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error updating artifact: {e}")

@app.route('/artifacts/<int:artifact_id>', methods=['DELETE'])
def delete_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")

    try:
        db.session.delete(artifact)
        db.session.commit()
        return jsonify({'message': 'Artifact deleted successfully'})
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error deleting artifact: {e}")

@app.route('/artifacts/<int:artifact_id>/vote', methods=['POST'])
def vote_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")

    artifact.votecount += 1

    try:
        db.session.commit()
        return jsonify(artifact.to_dict())
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error voting for artifact: {e}")

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    leaderboard_items = Artifact.query.order_by(desc(Artifact.votecount)).paginate(page=page, per_page=per_page, error_out=False)

    items_data = [item.to_dict() for item in leaderboard_items.items]

    response = {
        'items': items_data,
        'total': leaderboard_items.total,
        'page': leaderboard_items.page,
        'per_page': leaderboard_items.per_page,
        'pages': leaderboard_items.pages,
        'has_next': leaderboard_items.has_next,
        'has_prev': leaderboard_items.has_prev,
        'next_num': leaderboard_items.next_num,
        'prev_num': leaderboard_items.prev_num
    }

    return jsonify(response)

@app.route('/artifacts/randoms/positive', methods=['GET'])
def get_random_positive_artifact():
    artifacts = Artifact.query.filter(Artifact.isPositive == True).order_by(db.func.random()).limit(4).all()
    return jsonify([artifact.to_dict() for artifact in artifacts])

@app.route('/artifacts/randoms/negative', methods=['GET'])
def get_random_negative_artifact():
    artifacts = Artifact.query.filter(Artifact.isNegative == True).order_by(db.func.random()).limit(4).all()
    return jsonify([artifact.to_dict() for artifact in artifacts])

@app.route('/artifacts/randoms/<string:author>', methods=['GET'])
def get_random_artifact_by_author(author):
    artifacts = Artifact.query.filter(Artifact.author == author).order_by(db.func.random()).limit(4).all()
    return jsonify([artifact.to_dict() for artifact in artifacts])

if __name__ == '__main__':
    with app.app_context():
        init_db()

    app.run(debug=True)
