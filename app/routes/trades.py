from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Trade, Ticker, Tag, TradeSide, TradeType
from app.utils.schemas import TradeReadSchema, TradeCreateSchema, TradeUpdateSchema
from app.utils.auth import get_current_user
from marshmallow import ValidationError
from datetime import datetime, timezone

trades_bp = Blueprint('trades', __name__)

trade_read_schema = TradeReadSchema()
trades_read_schema = TradeReadSchema(many=True)
trade_create_schema = TradeCreateSchema()
trade_update_schema = TradeUpdateSchema()


def infer_side_type(entry, stoploss, side, last_price):
    if stoploss is not None:
        side = TradeSide.BUY if entry >= stoploss else TradeSide.SELL
        if side == TradeSide.BUY:
            trade_type = TradeType.BREAKOUT if entry <= last_price else TradeType.PULLBACK
        else:  # Sell
            trade_type = TradeType.BREAKOUT if entry >= last_price else TradeType.PULLBACK
    else:
        if not side:
            raise ValidationError("Either 'Stoploss' or 'Side' must be provided.")
        if side == TradeSide.BUY:
            trade_type = TradeType.BREAKOUT if entry <= last_price else TradeType.PULLBACK
        else:
            trade_type = TradeType.BREAKOUT if entry >= last_price else TradeType.PULLBACK
    return side, trade_type


# -----------------------
# GET all trades
# -----------------------
@trades_bp.route('/', methods=['GET'])
@jwt_required()
def get_trades():
    current_user = get_current_user()
    status = request.args.get('status', '')
    symbol = request.args.get('symbol', '')
    trade_type = request.args.get('type', '')

    query = Trade.query.filter_by(user_id=current_user.id)

    if status:
        query = query.filter(Trade.status == status)
    if symbol:
        query = query.filter(Trade.symbol.ilike(f'%{symbol}%'))
    if trade_type:
        query = query.filter(Trade.type == trade_type)

    trades = query.order_by(Trade.updated_at.desc()).all()

    return jsonify({
        'trades': trades_read_schema.dump(trades),
        'total': len(trades),
    })


# -----------------------
# GET single trade
# -----------------------
@trades_bp.route('/<trade_id>', methods=['GET'])
@jwt_required()
def get_trade(trade_id):
    current_user = get_current_user()
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first_or_404()
    return jsonify({'trade': trade_read_schema.dump(trade)})


# -----------------------
# CREATE trade
# -----------------------
@trades_bp.route('/', methods=['POST'])
@jwt_required()
def create_trade():
    current_user = get_current_user()
    json_data = request.json

    try:
        data = trade_create_schema.load(json_data)
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.messages}), 400

    # Fetch ticker for last_price
    ticker = Ticker.query.get_or_404(data['ticker_id'])
    entry = data['entry']
    stoploss = data.get('stoploss')
    side = data.get('side')

    # Infer side and type
    side, trade_type = infer_side_type(entry, stoploss, side, ticker.last_price)
    data['side'] = side
    data['type'] = trade_type
    data['user_id'] = current_user.id

    # Handle tags
    tags_input = data.pop('tags', [])
    trade_tags = []
    for t in tags_input:
        tag = Tag.query.filter_by(name=t['name'], user_id=current_user.id).first()
        if not tag:
            tag = Tag(name=t['name'], user_id=current_user.id)
            db.session.add(tag)
        trade_tags.append(tag)

    trade = Trade(**data)
    trade.tags = trade_tags

    try:
        db.session.add(trade)
        db.session.commit()
        return jsonify({'message': 'Trade created successfully', 'trade': trade_read_schema.dump(trade)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create trade'}), 500


# -----------------------
# UPDATE trade
# -----------------------
@trades_bp.route('/<trade_id>', methods=['PUT'])
@jwt_required()
def update_trade(trade_id):
    current_user = get_current_user()
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first_or_404()
    json_data = request.json

    # Load and validate input
    try:
        data = trade_update_schema.load(json_data, partial=True)
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.messages}), 400

    # Update all fields except user_id and tags
    for field, value in data.items():
        if hasattr(trade, field) and field not in ('user_id', 'tags'):
            setattr(trade, field, value)

    trade.edited_at = datetime.utcnow()

    # Handle tags separately
    if 'tags' in json_data:
        new_tags_input = json_data['tags']
        new_tags = []
        for t in new_tags_input:
            # Check if tag exists for this user
            tag = Tag.query.filter_by(name=t['name'], user_id=current_user.id).first()
            if not tag:
                tag = Tag(name=t['name'], user_id=current_user.id)
                db.session.add(tag)
            new_tags.append(tag)
        # Assign new tags to trade (remove missing tags from trade, don't delete tags)
        trade.tags = new_tags

    try:
        db.session.commit()
        return jsonify({'message': 'Trade updated successfully', 'trade': trade_read_schema.dump(trade)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update trade'}), 500


# -----------------------
# DELETE trade
# -----------------------
@trades_bp.route('/<trade_id>', methods=['DELETE'])
@jwt_required()
def delete_trade(trade_id):
    current_user = get_current_user()
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(trade)
        db.session.commit()
        return jsonify({'message': 'Trade deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete trade'}), 500


# -----------------------
# DELETE multiple trades
# -----------------------
@trades_bp.route('/delete-multiple', methods=['POST'])
@jwt_required()
def delete_multiple_trades():
    current_user = get_current_user()
    json_data = request.json

    trade_ids = json_data.get('trade_ids')
    if not trade_ids or not isinstance(trade_ids, list):
        return jsonify({'error': 'trade_ids must be a non-empty list'}), 400

    # Fetch trades that belong to the user
    trades_to_delete = Trade.query.filter(Trade.id.in_(trade_ids), Trade.user_id == current_user.id).all()

    if not trades_to_delete:
        return jsonify({'error': 'No matching trades found'}), 404

    try:
        for trade in trades_to_delete:
            db.session.delete(trade)
        db.session.commit()
        return jsonify({'message': f'{len(trades_to_delete)} trade(s) deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete trades'}), 500
