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
    print(query)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if current_app.elastic_search and query:
        print("Using Elasticsearch")
        # Use Elasticsearch
        tickers, total = Ticker.search(query, page, per_page)
    else:
        print("Using SQLAlchemy")
        # Fallback to SQLAlchemy search
        sql_query = Ticker.query
        if query:
            sql_query = sql_query.filter(Ticker.symbol.ilike(f'{query}%'))
        resources = sql_query.paginate(page=page, per_page=per_page, error_out=False)
        tickers = resources.items
        total = resources.total

    return jsonify({
        'tickers': tickers_schema.dump(tickers),
        'total': total,
        'page': page,
        'per_page': per_page
    })
