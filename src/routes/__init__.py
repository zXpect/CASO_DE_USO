from flask import Blueprint

# Import blueprint modules
from routes.auth import auth_bp
from routes.facturas import facturas_bp
from routes.pagos import pagos_bp

# Function to register all blueprints
def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(pagos_bp)