from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models.factura import Factura
from models.pago import Pago
from models.usuario import Usuario
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config

pagos_bp = Blueprint('pagos', __name__)

@pagos_bp.route('/pagos')
@login_required
def listar_pagos():
    # Obtener los pagos de este usuario
    pagos = Pago.get_by_usuario(str(current_user.id))
    
    # Obtener las facturas asociadas a esos pagos
    facturas = {}
    for pago in pagos:
        factura = Factura.get_by_id(pago.factura_id)
        if factura:
            facturas[pago.factura_id] = factura
    
    return render_template(
        'pagos/list.html',
        pagos=pagos,
        facturas=facturas
    )

@pagos_bp.route('/pagos/crear/<factura_id>', methods=['GET', 'POST'])
@login_required
def crear_pago(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar que el usuario pertenece a esta factura
    grupo_base = ((current_user.apartamento - 1) // 4) * 4 + 1
    if not (current_user.torre == factura.torre and factura.apartamento_base == grupo_base):
        flash('No tiene permisos para realizar pagos en esta factura', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar si ya existe un pago registrado por este usuario para esta factura
    pago_existente = Pago.get_by_factura_y_usuario(factura_id, str(current_user.id))
    if pago_existente:
        flash('Ya ha registrado un pago para esta factura', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        monto = float(request.form.get('monto'))
        fecha_pago = datetime.strptime(request.form.get('fecha_pago'), '%Y-%m-%d')
        
        # Manejo del comprobante de pago
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                comprobante = filename
        
        # Crear el nuevo pago
        nuevo_pago = Pago(
            factura_id=factura_id,
            usuario_id=str(current_user.id),
            monto=monto,
            fecha_pago=fecha_pago,
            comprobante=comprobante
        )
        nuevo_pago.save()
        
        flash('Pago registrado correctamente. Se notificará cuando sea confirmado.', 'success')
        return redirect(url_for('dashboard'))
    
    # Calcular el monto sugerido (parte proporcional)
    monto_sugerido = factura.calcular_valor_por_apartamento()
    
    return render_template(
        'pagos/create.html',
        factura=factura,
        monto_sugerido=monto_sugerido
    )

@pagos_bp.route('/pagos/confirmar/<pago_id>', methods=['POST'])
@login_required
def confirmar_pago(pago_id):
    # Solo administradores o usuarios principales pueden confirmar pagos
    if not (current_user.es_administrador or current_user.tiene_servicios):
        flash('No tiene permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard'))
    
    pago = Pago.get_by_id(pago_id)
    if not pago:
        flash('Pago no encontrado', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar que el administrador tiene acceso a este pago
    factura = Factura.get_by_id(pago.factura_id)
    if not factura:
        flash('Factura asociada no encontrada', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.es_administrador and (current_user.torre != factura.torre or current_user.apartamento != factura.apartamento_base):
        flash('No tiene permisos para confirmar este pago', 'danger')
        return redirect(url_for('dashboard'))
    
    # Actualizar el estado del pago
    pago.estado = 'confirmado'
    pago.save()
    
    # Si todos los usuarios asociados han pagado, marcar la factura como pagada
    pagos_factura = Pago.get_by_factura(pago.factura_id)
    apartamentos = factura.get_apartamentos_asociados()
    
    # Contar pagos confirmados
    pagos_confirmados = [p for p in pagos_factura if p.estado == 'confirmado']
    
    # Si todos los apartamentos han pagado, actualizar estado de la factura
    if len(pagos_confirmados) == len(apartamentos):
        factura.estado = 'pagada'
        factura.save()
    
    flash('Pago confirmado correctamente', 'success')
    return redirect(url_for('detalle_factura', factura_id=pago.factura_id))

@pagos_bp.route('/pagos/rechazar/<pago_id>', methods=['POST'])
@login_required
def rechazar_pago(pago_id):
    # Solo administradores o usuarios principales pueden rechazar pagos
    if not (current_user.es_administrador or current_user.tiene_servicios):
        flash('No tiene permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard'))
    
    pago = Pago.get_by_id(pago_id)
    if not pago:
        flash('Pago no encontrado', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar que el administrador tiene acceso a este pago
    factura = Factura.get_by_id(pago.factura_id)
    if not factura:
        flash('Factura asociada no encontrada', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.es_administrador and (current_user.torre != factura.torre or current_user.apartamento != factura.apartamento_base):
        flash('No tiene permisos para rechazar este pago', 'danger')
        return redirect(url_for('dashboard'))
    
    # Actualizar el estado del pago
    pago.estado = 'rechazado'
    pago.save()
    
    flash('Pago rechazado', 'warning')
    return redirect(url_for('detalle_factura', factura_id=pago.factura_id))