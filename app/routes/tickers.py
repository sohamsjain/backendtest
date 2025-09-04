from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.models import Ticker
from app.utils.schemas import TickerSchema

tickers_bp = Blueprint('tickers', __name__)

tickers_schema = TickerSchema(many=True)


# -----------------------
# SEARCH TICKERS
# -----------------------
@tickers_bp.route('/', methods=['GET'])
@jwt_required()
def search_tickers():
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if current_app.elastic_search and query:
        # Use Elasticsearch
        tickers, total = Ticker.search(query, page, per_page)
    else:
        # Fallback to SQLAlchemy search
        tickers = []
        total = 0
        if query:
            tickers = Ticker.query.filter(Ticker.symbol.ilike(f'{query}%')).all()
            total = len(tickers)

    return jsonify({
        'tickers': tickers_schema.dump(tickers),
        'total': total,
        'page': page,
        'per_page': per_page
    })
