from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.models import Tag
from app.utils.schemas import TagReadSchema

tags_bp = Blueprint('tags', __name__)

tags_schema = TagReadSchema(many=True)


# -----------------------
# SEARCH TAGS
# -----------------------
@tags_bp.route('/', methods=['GET'])
@jwt_required()
def search_tags():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    if current_app.elastic_search and query:
        # Use Elasticsearch
        tags, total = Tag.search(query, page, per_page)
    else:
        # Fallback to SQLAlchemy search
        tags = []
        total = 0
        if query:
            tags = Tag.query.filter(Tag.name.ilike(f'{query}%')).all()
            total = len(tags)

    return jsonify({
        'tags': tags_schema.dump(tags),
        'total': total,
        'page': page,
        'per_page': per_page
    })
