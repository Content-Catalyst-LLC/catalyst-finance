import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI") or "sqlite:////Users/tariqahmad/GitHub/catalyst-finance/app.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # register P/E blueprint
    from app.routes.pe import bp as pe_bp
    app.register_blueprint(pe_bp)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}, 200

    return app
