from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.utils.schemas import UserSchema
from app.utils.auth import admin_required
from marshmallow import ValidationError

users_bp = Blueprint('users', __name__)
user_schema = UserSchema()
users_schema = UserSchema(many=True)


@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    users = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'users': users_schema.dump(users.items),
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    })


@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    # current_user_id = get_jwt_identity()
    # current_user = User.query.get(current_user_id)
    #
    # # Users can only view their own profile unless they're admin
    # if user_id != current_user_id and not current_user.is_admin:
    #     return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)
    return jsonify({'user': user_schema.dump(user)})


@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Users can only update their own profile unless they're admin
    if user_id != current_user_id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)

    try:
        data = user_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.messages}), 400

    # Update user fields
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    try:
        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': user_schema.dump(user)
        })
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500


@users_bp.route('/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500