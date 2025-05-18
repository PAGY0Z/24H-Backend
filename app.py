from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import desc
from enum import Enum

app = Flask(__name__)

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
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    emoji = db.Column(db.String(255), nullable=True)
    author = db.Column(db.String(255), nullable=False)
    artyfactType = db.Column(SQLAlchemyEnum(ArtifactType), nullable=False)
    filepath = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    def __repr__(self):
        return f"<Artifact(id={self.id}, title='{self.title}', type={self.artyfactType.name})>"

    # Method to easily convert Artifact object to a dictionary
    def to_dict(self):
        return {
            'id': self.id,
            'votecount': self.votecount,
            'title': self.title,
            'description': self.description,
            'emoji': self.emoji,
            'author': self.author,
            'artyfactType': self.artyfactType.name, # Return the enum name
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

@app.route('/')
def index():
    return "Flask app connected to MySQL using SQLAlchemy. Artifact model defined."

# Route to Create an artifact
@app.route('/artifacts', methods=['POST'])
def create_artifact():
    data = request.get_json()
    if not data or not 'title' in data or not 'author' in data or not 'artyfactType' in data:
        abort(400, description="Missing required fields (title, author, artyfactType)")

    # Validate artyfactType
    try:
        artifact_type_enum = ArtifactType[data['artyfactType']]
    except KeyError:
        abort(400, description="Invalid artyfactType")

    new_artifact = Artifact(
        title=data['title'],
        description=data.get('description'),
        emoji=data.get('emoji'),
        author=data['author'],
        artyfactType=artifact_type_enum,
        filepath=data.get('filepath'),
        votecount=data.get('votecount', 0) # Allow setting initial votecount, defaults to 0
    )

    try:
        db.session.add(new_artifact)
        db.session.commit()
        return jsonify(new_artifact.to_dict()), 201 # 201 Created
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error creating artifact: {e}")

# Route to Get all artifacts
@app.route('/artifacts', methods=['GET'])
def get_all_artifacts():
    artifacts = Artifact.query.all()
    return jsonify([artifact.to_dict() for artifact in artifacts])

# Route to Get an artifact by its ID
@app.route('/artifacts/<int:artifact_id>', methods=['GET'])
def get_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")
    return jsonify(artifact.to_dict())

# Route to Update an artifact by its ID
@app.route('/artifacts/<int:artifact_id>', methods=['PUT'])
def update_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided")

    if 'title' in data:
        artifact.title = data['title']
    if 'description' in data:
        artifact.description = data['description']
    if 'emoji' in data:
        artifact.emoji = data['emoji']
    if 'author' in data:
        artifact.author = data['author']
    if 'artyfactType' in data:
        try:
            artifact.artyfactType = ArtifactType[data['artyfactType']]
        except KeyError:
            abort(400, description="Invalid artyfactType")
    if 'filepath' in data:
        artifact.filepath = data['filepath']
    # votecount is updated via the vote route, not here

    try:
        db.session.commit()
        return jsonify(artifact.to_dict())
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error updating artifact: {e}")

# Route to Delete an artifact by its ID
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

# Route to vote for an artifact by its ID
@app.route('/artifacts/<int:artifact_id>/vote', methods=['POST'])
def vote_artifact(artifact_id):
    artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        abort(404, description="Artifact not found")

    # Increment the votecount
    artifact.votecount += 1

    try:
        db.session.commit()
        return jsonify(artifact.to_dict())
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error voting for artifact: {e}")

# Route to retrieve the leaderboard by page
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # Number of items per page

    # Query artifacts ordered by votecount descending, with pagination
    leaderboard_items = Artifact.query.order_by(desc(Artifact.votecount)).paginate(page=page, per_page=per_page, error_out=False)

    # Prepare response data
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


if __name__ == '__main__':
    with app.app_context():
        init_db()

    app.run(debug=True)
