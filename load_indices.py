from kite import Kite
from app import create_app, db
from app.models import Ticker

# List of index symbols to keep
indices = [
    "NIFTY 50",
    "NIFTY NEXT 50",
    "NIFTY BANK",
    "NIFTY FIN SERVICE",
    "NIFTY 100",
    "NIFTY 200",
    "NIFTY 500",
    "NIFTY MIDCAP 50",
    "NIFTY MIDCAP 100",
    "NIFTY SMLCAP 100",
    "INDIA VIX",
    "NIFTY MIDCAP 150",
    "NIFTY SMLCAP 250",
    "NIFTY MIDSML 400",
    "NIFTY AUTO",
    "NIFTY FINSRV25 50",
    "NIFTY FMCG",
    "NIFTY IT",
    "NIFTY MEDIA",
    "NIFTY METAL",
    "NIFTY PHARMA",
    "NIFTY PSU BANK",
    "NIFTY PVT BANK",
    "NIFTY REALTY",
    "NIFTY HEALTHCARE",
    "NIFTY CONSR DURBL",
    "NIFTY OIL AND GAS",
    "NIFTY MIDSMALL",
    "NIFTY CHEMICALS",
    "NIFTY500 HEALTHCARE",
]

kite = Kite().kite

# Fetch all NSE instruments
instruments = kite.instruments("NSE")
index = [i for i in instruments if i['segment'] == 'INDICES']

# Filter only required indices
index_instruments = [
    i for i in index
    if i["tradingsymbol"] in indices
]

app = create_app()

with app.app_context():
    for i in index_instruments:
        ticker = Ticker(
            symbol=i["tradingsymbol"],
            exchange=i["exchange"],
            instrument_token=i["instrument_token"],
            name=i["name"],
        )
        db.session.add(ticker)

    db.session.commit()
