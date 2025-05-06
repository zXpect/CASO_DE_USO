from models import pagos_collection
from bson.objectid import ObjectId
from datetime import datetime

class Pago:
    def __init__(self, factura_id, usuario_id, monto, fecha_pago=None, 
                 comprobante=None, estado="pendiente", id=None):
        self.id = id
        self.factura_id = factura_id
        self.usuario_id = usuario_id
        self.monto = monto
        self.fecha_pago = fecha_pago if fecha_pago else datetime.now()
        self.comprobante = comprobante  # URL o nombre de archivo del comprobante
        self.estado = estado  # pendiente, confirmado, rechazado
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
    
    def save(self):
        if not self.id:
            pago_data = {
                'factura_id': self.factura_id,
                'usuario_id': self.usuario_id,
                'monto': self.monto,
                'fecha_pago': self.fecha_pago,
                'comprobante': self.comprobante,
                'estado': self.estado,
                'fecha_creacion': self.fecha_creacion,
                'fecha_actualizacion': self.fecha_actualizacion
            }
            result = pagos_collection.insert_one(pago_data)
            self.id = str(result.inserted_id)
            return self
        else:
            self.fecha_actualizacion = datetime.now()
            pagos_collection.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'factura_id': self.factura_id,
                    'usuario_id': self.usuario_id,
                    'monto': self.monto,
                    'fecha_pago': self.fecha_pago,
                    'comprobante': self.comprobante,
                    'estado': self.estado,
                    'fecha_actualizacion': self.fecha_actualizacion
                }}
            )
            return self
    
    def delete(self):
        if self.id:
            pagos_collection.delete_one({'_id': ObjectId(self.id)})
            return True
        return False
    
    @staticmethod
    def get_by_id(pago_id):
        pago_data = pagos_collection.find_one({'_id': ObjectId(pago_id)})
        if pago_data:
            return Pago(
                id=str(pago_data['_id']),
                factura_id=pago_data['factura_id'],
                usuario_id=pago_data['usuario_id'],
                monto=pago_data['monto'],
                fecha_pago=pago_data['fecha_pago'],
                comprobante=pago_data.get('comprobante'),
                estado=pago_data['estado']
            )
        return None
    
    @staticmethod
    def get_by_factura(factura_id):
        pagos = []
        for pago_data in pagos_collection.find({'factura_id': factura_id}):
            pagos.append(Pago(
                id=str(pago_data['_id']),
                factura_id=pago_data['factura_id'],
                usuario_id=pago_data['usuario_id'],
                monto=pago_data['monto'],
                fecha_pago=pago_data['fecha_pago'],
                comprobante=pago_data.get('comprobante'),
                estado=pago_data['estado']
            ))
        return pagos
    
    @staticmethod
    def get_by_usuario(usuario_id):
        pagos = []
        for pago_data in pagos_collection.find({'usuario_id': usuario_id}):
            pagos.append(Pago(
                id=str(pago_data['_id']),
                factura_id=pago_data['factura_id'],
                usuario_id=pago_data['usuario_id'],
                monto=pago_data['monto'],
                fecha_pago=pago_data['fecha_pago'],
                comprobante=pago_data.get('comprobante'),
                estado=pago_data['estado']
            ))
        return pagos
        
    @staticmethod
    def get_by_factura_y_usuario(factura_id, usuario_id):
        pago_data = pagos_collection.find_one({
            'factura_id': factura_id,
            'usuario_id': usuario_id
        })
        if pago_data:
            return Pago(
                id=str(pago_data['_id']),
                factura_id=pago_data['factura_id'],
                usuario_id=pago_data['usuario_id'],
                monto=pago_data['monto'],
                fecha_pago=pago_data['fecha_pago'],
                comprobante=pago_data.get('comprobante'),
                estado=pago_data['estado']
            )
        return None