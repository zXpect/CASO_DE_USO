from pymongo import MongoClient
from config import Config

# Conexión a MongoDB
client = MongoClient(Config.MONGODB_URI)
db = client[Config.DATABASE_NAME]

# Colecciones
usuarios_collection = db.usuarios
facturas_collection = db.facturas
pagos_collection = db.pagos