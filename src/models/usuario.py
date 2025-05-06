from models import usuarios_collection
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from bson.objectid import ObjectId

class Usuario(UserMixin):
    def __init__(self, nombre, email, torre, apartamento, es_administrador=False, password=None, id=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.torre = torre  # Número de torre (1-4)
        self.apartamento = apartamento  # Número de apartamento (1-12)
        self.es_administrador = es_administrador  # Si es admin o normal
        self.password_hash = generate_password_hash(password) if password else None
        
        # Calculamos automáticamente si el apartamento tiene servicio directo
        # Solo los primeros apartamentos de cada bloque de 4 tendrán servicios
        self.tiene_servicios = (apartamento % 4 == 1)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        if not self.id:
            usuario_data = {
                'nombre': self.nombre,
                'email': self.email,
                'torre': self.torre,
                'apartamento': self.apartamento,
                'es_administrador': self.es_administrador,
                'password_hash': self.password_hash,
                'tiene_servicios': self.tiene_servicios
            }
            result = usuarios_collection.insert_one(usuario_data)
            self.id = str(result.inserted_id)
            return self
        else:
            usuarios_collection.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'nombre': self.nombre,
                    'email': self.email,
                    'torre': self.torre,
                    'apartamento': self.apartamento,
                    'es_administrador': self.es_administrador,
                    'password_hash': self.password_hash,
                    'tiene_servicios': self.tiene_servicios
                }}
            )
            return self
    
    @staticmethod
    def get_by_id(user_id):
        user_data = usuarios_collection.find_one({'_id': ObjectId(user_id)})
        if user_data:
            user = Usuario(
                id=str(user_data['_id']),
                nombre=user_data['nombre'],
                email=user_data['email'],
                torre=user_data['torre'],
                apartamento=user_data['apartamento'],
                es_administrador=user_data['es_administrador']
            )
            user.password_hash = user_data['password_hash']
            user.tiene_servicios = user_data['tiene_servicios']
            return user
        return None
    
    @staticmethod
    def get_by_email(email):
        user_data = usuarios_collection.find_one({'email': email})
        if user_data:
            user = Usuario(
                id=str(user_data['_id']),
                nombre=user_data['nombre'],
                email=user_data['email'],
                torre=user_data['torre'],
                apartamento=user_data['apartamento'],
                es_administrador=user_data['es_administrador']
            )
            user.password_hash = user_data['password_hash']
            user.tiene_servicios = user_data['tiene_servicios']
            return user
        return None
    
    @staticmethod
    def get_by_torre_y_apartamento(torre, apartamento):
        user_data = usuarios_collection.find_one({'torre': torre, 'apartamento': apartamento})
        if user_data:
            user = Usuario(
                id=str(user_data['_id']),
                nombre=user_data['nombre'],
                email=user_data['email'],
                torre=user_data['torre'],
                apartamento=user_data['apartamento'],
                es_administrador=user_data['es_administrador']
            )
            user.password_hash = user_data['password_hash']
            user.tiene_servicios = user_data['tiene_servicios']
            return user
        return None
    
    @staticmethod
    def get_all():
        usuarios = []
        for user_data in usuarios_collection.find():
            user = Usuario(
                id=str(user_data['_id']),
                nombre=user_data['nombre'],
                email=user_data['email'],
                torre=user_data['torre'],
                apartamento=user_data['apartamento'],
                es_administrador=user_data['es_administrador']
            )
            user.password_hash = user_data['password_hash']
            user.tiene_servicios = user_data['tiene_servicios']
            usuarios.append(user)
        return usuarios

    def get_apartamentos_asociados(self):
        """Obtiene los apartamentos que comparten servicios con este apartamento"""
        base_apt = ((self.apartamento - 1) // 4) * 4 + 1
        return [base_apt + i for i in range(4)]
        
    def get_id(self):
        return str(self.id)