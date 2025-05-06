from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models.factura import Factura
from models.pago import Pago
from models.usuario import Usuario
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config

facturas_bp = Blueprint('facturas', __name__)

@facturas_bp.route('/dashboard')
@login_required
def dashboard():
    # Obtener las facturas asociadas a este usuario
    facturas = Factura.get_by_torre_apartamento(current_user.torre, current_user.apartamento)
    
    # Organizar facturas por tipo de servicio
    facturas_por_servicio = {
        'agua': [],
        'energia': [],
        'gas': []
    }
    
    for factura in facturas:
        if factura.tipo_servicio in facturas_por_servicio:
            facturas_por_servicio[factura.tipo_servicio].append(factura)
    
    # Ordenar cada lista por fecha de vencimiento (más reciente primero)
    for tipo in facturas_por_servicio:
        facturas_por_servicio[tipo].sort(key=lambda x: x.fecha_vencimiento, reverse=True)
    
    # Obtener los pagos realizados por este usuario
    pagos_usuario = Pago.get_by_usuario(str(current_user.id))
    
    # Crear un diccionario de pagos por factura_id para acceso rápido
    pagos_por_factura = {}
    for pago in pagos_usuario:
        pagos_por_factura[pago.factura_id] = pago
    
    return render_template(
        'admin/dashboard.html', 
        facturas_por_servicio=facturas_por_servicio,
        pagos_por_factura=pagos_por_factura
    )

@facturas_bp.route('/facturas')
@facturas_bp.route('/facturas/<tipo>')
@login_required
def listar_facturas(tipo='todas'):
    if tipo == 'todas':
        facturas = Factura.get_by_torre_apartamento(current_user.torre, current_user.apartamento)
    elif tipo in ['agua', 'energia', 'gas']:
        facturas_todas = Factura.get_by_torre_apartamento(current_user.torre, current_user.apartamento)
        facturas = [f for f in facturas_todas if f.tipo_servicio == tipo]
    else:
        flash('Tipo de servicio no válido', 'danger')
        return redirect(url_for('listar_facturas', tipo='todas'))
    
    # Ordenar por fecha de vencimiento (más reciente primero)
    facturas.sort(key=lambda x: x.fecha_vencimiento, reverse=True)
    
    return render_template(
        'facturas/list.html', 
        facturas=facturas,
        tipo_actual=tipo
    )

@facturas_bp.route('/facturas/crear', methods=['GET', 'POST'])
@login_required
def crear_factura():
    # Solo administradores o usuarios con servicios directos pueden crear facturas
    if not (current_user.es_administrador or current_user.tiene_servicios):
        flash('No tiene permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        tipo_servicio = request.form.get('tipo_servicio')
        torre = int(request.form.get('torre'))
        apartamento_base = int(request.form.get('apartamento_base'))
        fecha_emision = datetime.strptime(request.form.get('fecha_emision'), '%Y-%m-%d')
        fecha_vencimiento = datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
        valor_total = float(request.form.get('valor_total'))
        consumo_total = float(request.form.get('consumo_total'))
        
        # Manejo de la imagen de la factura
        imagen_factura = None
        if 'imagen_factura' in request.files:
            file = request.files['imagen_factura']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Crear directorio si no existe
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                imagen_factura = filename
        
        # Crear la nueva factura
        nueva_factura = Factura(
            tipo_servicio=tipo_servicio,
            torre=torre,
            apartamento_base=apartamento_base,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            valor_total=valor_total,
            consumo_total=consumo_total,
            imagen_factura=imagen_factura
        )
        nueva_factura.save()
        
        flash('Factura registrada correctamente', 'success')
        return redirect(url_for('listar_facturas'))
    
    return render_template('facturas/create.html')

@facturas_bp.route('/facturas/<factura_id>')
@login_required
def detalle_factura(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Verificar que el usuario tiene acceso a esta factura
    grupo_base = ((current_user.apartamento - 1) // 4) * 4 + 1
    if not (current_user.es_administrador or (current_user.torre == factura.torre and factura.apartamento_base == grupo_base)):
        flash('No tiene permisos para ver esta factura', 'danger')
        return redirect(url_for('dashboard'))
    
    # Obtener los pagos asociados a esta factura
    pagos = Pago.get_by_factura(factura_id)
    
    # Obtener los usuarios asociados a esta factura
    apartamentos = factura.get_apartamentos_asociados()
    usuarios = []
    for apartamento in apartamentos:
        usuario = Usuario.get_by_torre_y_apartamento(factura.torre, apartamento)
        if usuario:
            usuarios.append(usuario)
    
    return render_template(
        'facturas/detail.html',
        factura=factura,
        pagos=pagos,
        usuarios=usuarios
    )

@facturas_bp.route('/facturas/editar/<factura_id>', methods=['GET', 'POST'])
@login_required
def editar_factura(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Verificar que el usuario puede editar esta factura
    if not (current_user.es_administrador or (current_user.torre == factura.torre and current_user.apartamento == factura.apartamento_base and current_user.tiene_servicios)):
        flash('No tiene permisos para editar esta factura', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        factura.tipo_servicio = request.form.get('tipo_servicio')
        factura.torre = int(request.form.get('torre'))
        factura.apartamento_base = int(request.form.get('apartamento_base'))
        factura.fecha_emision = datetime.strptime(request.form.get('fecha_emision'), '%Y-%m-%d')
        factura.fecha_vencimiento = datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
        factura.valor_total = float(request.form.get('valor_total'))
        factura.consumo_total = float(request.form.get('consumo_total'))
        factura.estado = request.form.get('estado')
        
        # Manejo de la imagen de la factura
        if 'imagen_factura' in request.files:
            file = request.files['imagen_factura']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # Si ya había una imagen, borrarla
                if factura.imagen_factura:
                    old_path = os.path.join(Config.UPLOAD_FOLDER, factura.imagen_factura)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                factura.imagen_factura = filename
        
        factura.save()
        flash('Factura actualizada correctamente', 'success')
        return redirect(url_for('detalle_factura', factura_id=factura.id))
    
    return render_template('facturas/edit.html', factura=factura)

@facturas_bp.route('/facturas/eliminar/<factura_id>', methods=['POST'])
@login_required
def eliminar_factura(factura_id):
    # Solo los administradores pueden eliminar facturas
    if not current_user.es_administrador:
        flash('No tiene permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard'))
    
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Eliminar la imagen si existe
    if factura.imagen_factura:
        file_path = os.path.join(Config.UPLOAD_FOLDER, factura.imagen_factura)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Eliminar la factura
    factura.delete()
    flash('Factura eliminada correctamente', 'success')
    return redirect(url_for('listar_facturas'))

@facturas_bp.route('/agua')
@login_required
def ver_agua():
    return redirect(url_for('listar_facturas', tipo='agua'))

@facturas_bp.route('/energia')
@login_required
def ver_energia():
    return redirect(url_for('listar_facturas', tipo='energia'))

@facturas_bp.route('/gas')
@login_required
def ver_gas():
    return redirect(url_for('listar_facturas', tipo='gas'))