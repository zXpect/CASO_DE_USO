import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_changeme')
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/servicios_app')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'servicios_app')
    
    # Constantes para la aplicación
    TIPOS_SERVICIOS = ['agua', 'energia', 'gas']
    NUM_TORRES = 4
    APARTAMENTOS_POR_TORRE = 12
    SERVICIOS_POR_TORRE = 3
    APARTAMENTOS_POR_SERVICIO = 4  # Cada servicio es compartido por 4 apartamentos