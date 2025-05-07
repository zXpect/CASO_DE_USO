from models import facturas_collection
from bson.objectid import ObjectId
from datetime import datetime

class Factura:
    def __init__(self, tipo_servicio, torre, apartamento_base, fecha_emision, fecha_vencimiento, 
                 valor_total, consumo_total, usuario_id=None, imagen_factura=None, estado="pendiente", id=None):
        self.id = id
        self.tipo_servicio = tipo_servicio  # agua, energia, gas
        self.torre = torre  # 1-4
        self.apartamento_base = apartamento_base  # Apartamento principal que recibe la factura
        self.fecha_emision = fecha_emision
        self.fecha_vencimiento = fecha_vencimiento
        self.valor_total = valor_total
        self.consumo_total = consumo_total  # En unidades (m³, kWh, etc.)
        self.imagen_factura = imagen_factura  # URL o nombre de archivo de la imagen
        self.estado = estado  # pendiente, pagada, vencida
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        self.usuario_id = usuario_id
    
    def save(self):
        if not self.id:
            factura_data = {
                'tipo_servicio': self.tipo_servicio,
                'torre': self.torre,
                'apartamento_base': self.apartamento_base,
                'fecha_emision': self.fecha_emision,
                'fecha_vencimiento': self.fecha_vencimiento,
                'valor_total': self.valor_total,
                'consumo_total': self.consumo_total,
                'imagen_factura': self.imagen_factura,
                'estado': self.estado,
                'fecha_creacion': self.fecha_creacion,
                'fecha_actualizacion': self.fecha_actualizacion,
                'usuario_id': self.usuario_id
            }
            result = facturas_collection.insert_one(factura_data)
            self.id = str(result.inserted_id)
            return self
        else:
            self.fecha_actualizacion = datetime.now()
            facturas_collection.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'tipo_servicio': self.tipo_servicio,
                    'torre': self.torre,
                    'apartamento_base': self.apartamento_base,
                    'fecha_emision': self.fecha_emision,
                    'fecha_vencimiento': self.fecha_vencimiento,
                    'valor_total': self.valor_total,
                    'consumo_total': self.consumo_total,
                    'imagen_factura': self.imagen_factura,
                    'estado': self.estado,
                    'fecha_actualizacion': self.fecha_actualizacion,
                    'usuario_id': self.usuario_id
                }}
            )
            return self
    
    def delete(self):
        if self.id:
            facturas_collection.delete_one({'_id': ObjectId(self.id)})
            return True
        return False
    
    @staticmethod
    def get_by_id(factura_id):
        factura_data = facturas_collection.find_one({'_id': ObjectId(factura_id)})
        if factura_data:
            return Factura(
                id=str(factura_data['_id']),
                tipo_servicio=factura_data['tipo_servicio'],
                torre=factura_data['torre'],
                apartamento_base=factura_data['apartamento_base'],
                fecha_emision=factura_data['fecha_emision'],
                fecha_vencimiento=factura_data['fecha_vencimiento'],
                valor_total=factura_data['valor_total'],
                consumo_total=factura_data['consumo_total'],
                imagen_factura=factura_data.get('imagen_factura'),
                estado=factura_data['estado']
            )
        return None
    
    @staticmethod
    def get_all():
        facturas = []
        for factura_data in facturas_collection.find().sort('fecha_vencimiento', -1):
            facturas.append(Factura(
                id=str(factura_data['_id']),
                tipo_servicio=factura_data['tipo_servicio'],
                torre=factura_data['torre'],
                apartamento_base=factura_data['apartamento_base'],
                fecha_emision=factura_data['fecha_emision'],
                fecha_vencimiento=factura_data['fecha_vencimiento'],
                valor_total=factura_data['valor_total'],
                consumo_total=factura_data['consumo_total'],
                imagen_factura=factura_data.get('imagen_factura'),
                estado=factura_data['estado']
            ))
        return facturas
    
    @staticmethod
    def get_by_torre_apartamento(torre, apartamento):
        """
        Obtiene las facturas donde este apartamento es el base o está asociado
        """
        # Calculamos a qué grupo pertenece este apartamento
        grupo_base = ((apartamento - 1) // 4) * 4 + 1
        
        facturas = []
        for factura_data in facturas_collection.find({
            'torre': torre,
            'apartamento_base': grupo_base
        }).sort('fecha_vencimiento', -1):
            facturas.append(Factura(
                id=str(factura_data['_id']),
                tipo_servicio=factura_data['tipo_servicio'],
                torre=factura_data['torre'],
                apartamento_base=factura_data['apartamento_base'],
                fecha_emision=factura_data['fecha_emision'],
                fecha_vencimiento=factura_data['fecha_vencimiento'],
                valor_total=factura_data['valor_total'],
                consumo_total=factura_data['consumo_total'],
                imagen_factura=factura_data.get('imagen_factura'),
                estado=factura_data['estado']
            ))
        return facturas
    
    @staticmethod
    def get_by_tipo_servicio(tipo_servicio):
        facturas = []
        for factura_data in facturas_collection.find({'tipo_servicio': tipo_servicio}).sort('fecha_vencimiento', -1):
            facturas.append(Factura(
                id=str(factura_data['_id']),
                tipo_servicio=factura_data['tipo_servicio'],
                torre=factura_data['torre'],
                apartamento_base=factura_data['apartamento_base'],
                fecha_emision=factura_data['fecha_emision'],
                fecha_vencimiento=factura_data['fecha_vencimiento'],
                valor_total=factura_data['valor_total'],
                consumo_total=factura_data['consumo_total'],
                imagen_factura=factura_data.get('imagen_factura'),
                estado=factura_data['estado']
            ))
        return facturas
        
    def calcular_valor_por_apartamento(self):
        """Devuelve el valor que debe pagar cada apartamento"""
        return self.valor_total / 4  # Dividido entre 4 apartamentos
    
    def get_apartamentos_asociados(self):
        """Obtiene los 4 apartamentos que comparten esta factura"""
        base = self.apartamento_base
        return [base, base + 1, base + 2, base + 3]