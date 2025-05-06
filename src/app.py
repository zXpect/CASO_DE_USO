from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
import os
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from config import Config
from models.usuario import Usuario
from models.factura import Factura
from models.pago import Pago

app = Flask(__name__)
app.config.from_object(Config)

# Configuración de Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get_by_id(user_id)

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = Usuario.get_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        torre = int(request.form.get('torre'))
        apartamento = int(request.form.get('apartamento'))
        password = request.form.get('password')
        
        # Verificar si ya existe un usuario con ese email
        if Usuario.get_by_email(email):
            flash('Ya existe un usuario con ese correo', 'danger')
            return render_template('auth/register.html')
        
        # Verificar si ya existe un usuario con esa torre y apartamento
        if Usuario.get_by_torre_y_apartamento(torre, apartamento):
            flash('Ya existe un usuario para ese apartamento', 'danger')
            return render_template('auth/register.html')
        
        # Crear el nuevo usuario
        user = Usuario(nombre=nombre, email=email, torre=torre, 
                       apartamento=apartamento, password=password)
        user.save()
        
        flash('Cuenta creada exitosamente. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Ruta principal
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener facturas relevantes para el usuario
    facturas = Factura.get_by_torre_apartamento(current_user.torre, current_user.apartamento)
    
    # Agrupar facturas por tipo de servicio
    facturas_por_servicio = {
        'agua': [],
        'energia': [],
        'gas': []
    }
    
    for factura in facturas:
        facturas_por_servicio[factura.tipo_servicio].append(factura)
    
    # Obtener pagos del usuario
    pagos = Pago.get_by_usuario(current_user.id)
    
    # Crear un diccionario de pagos por factura para fácil acceso
    pagos_por_factura = {}
    for pago in pagos:
        pagos_por_factura[pago.factura_id] = pago
    
    return render_template('dashboard.html', 
                          facturas=facturas,
                          facturas_por_servicio=facturas_por_servicio,
                          pagos_por_factura=pagos_por_factura)

# Rutas para facturas
@app.route('/facturas')
@login_required
def listar_facturas():
    tipo = request.args.get('tipo', 'todas')
    
    if tipo != 'todas' and tipo in Config.TIPOS_SERVICIOS:
        facturas = Factura.get_by_tipo_servicio(tipo)
    else:
        facturas = Factura.get_all()
    
    # Si no es administrador ni tiene servicios, filtrar solo las facturas que le corresponden
    if not current_user.es_administrador and not current_user.tiene_servicios:
        facturas = [f for f in facturas if current_user.torre == f.torre and 
                   current_user.apartamento in f.get_apartamentos_asociados()]
    
    return render_template('facturas/list.html', facturas=facturas, tipo_actual=tipo)

@app.route('/facturas/crear', methods=['GET', 'POST'])
@login_required
def crear_factura():
    # Solo administradores o usuarios con servicios pueden crear facturas
    if not current_user.es_administrador and not current_user.tiene_servicios:
        flash('No tienes permiso para crear facturas', 'danger')
        return redirect(url_for('listar_facturas'))
    
    if request.method == 'POST':
        tipo_servicio = request.form.get('tipo_servicio')
        torre = int(request.form.get('torre'))
        apartamento_base = int(request.form.get('apartamento_base'))
        fecha_emision = datetime.strptime(request.form.get('fecha_emision'), '%Y-%m-%d')
        fecha_vencimiento = datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
        valor_total = float(request.form.get('valor_total'))
        consumo_total = float(request.form.get('consumo_total'))
        
        # Verificar que el apartamento base sea válido (debe ser el primero de un bloque de 4)
        if apartamento_base % 4 != 1:
            flash('El apartamento base debe ser el primero de un bloque de 4', 'danger')
            return render_template('facturas/create.html')
        
        # Crear la factura
        factura = Factura(
            tipo_servicio=tipo_servicio,
            torre=torre,
            apartamento_base=apartamento_base,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            valor_total=valor_total,
            consumo_total=consumo_total
        )
        factura.save()
        
        flash('Factura creada exitosamente', 'success')
        return redirect(url_for('listar_facturas'))
    
    return render_template('facturas/create.html')

@app.route('/facturas/<factura_id>')
@login_required
def detalle_factura(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Verificar permiso (administrador o usuario con acceso a esta factura)
    if not current_user.es_administrador and not (
        current_user.torre == factura.torre and 
        current_user.apartamento in factura.get_apartamentos_asociados()
    ):
        flash('No tienes permiso para ver esta factura', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Obtener pagos realizados para esta factura
    pagos = Pago.get_by_factura(factura_id)
    
    # Calcular cuánto ha pagado cada apartamento
    pagos_por_apartamento = {}
    for apto in factura.get_apartamentos_asociados():
        pagos_por_apartamento[apto] = {
            'pagado': 0,
            'estado': 'pendiente'
        }
    
    for pago in pagos:
        usuario = Usuario.get_by_id(pago.usuario_id)
        if usuario:
            pagos_por_apartamento[usuario.apartamento]['pagado'] = pago.monto
            pagos_por_apartamento[usuario.apartamento]['estado'] = pago.estado
    
    # Verificar si el usuario actual ya ha pagado
    pago_usuario = Pago.get_by_factura_y_usuario(factura_id, current_user.id)
    
    return render_template('facturas/detail.html', 
                          factura=factura,
                          pagos=pagos,
                          pagos_por_apartamento=pagos_por_apartamento,
                          pago_usuario=pago_usuario)

@app.route('/facturas/<factura_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_factura(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Solo administradores o el propietario del apartamento base pueden editar
    if not current_user.es_administrador and not (
        current_user.torre == factura.torre and 
        current_user.apartamento == factura.apartamento_base and
        current_user.tiene_servicios
    ):
        flash('No tienes permiso para editar esta factura', 'danger')
        return redirect(url_for('listar_facturas'))
    
    if request.method == 'POST':
        factura.tipo_servicio = request.form.get('tipo_servicio')
        factura.fecha_emision = datetime.strptime(request.form.get('fecha_emision'), '%Y-%m-%d')
        factura.fecha_vencimiento = datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
        factura.valor_total = float(request.form.get('valor_total'))
        factura.consumo_total = float(request.form.get('consumo_total'))
        factura.estado = request.form.get('estado')
        
        factura.save()
        
        flash('Factura actualizada exitosamente', 'success')
        return redirect(url_for('detalle_factura', factura_id=factura_id))
    
    return render_template('facturas/edit.html', factura=factura)

@app.route('/facturas/<factura_id>/eliminar', methods=['POST'])
@login_required
def eliminar_factura(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Solo administradores pueden eliminar facturas
    if not current_user.es_administrador:
        flash('No tienes permiso para eliminar facturas', 'danger')
        return redirect(url_for('detalle_factura', factura_id=factura_id))
    
    # Eliminar los pagos asociados
    pagos = Pago.get_by_factura(factura_id)
    for pago in pagos:
        pago.delete()
    
    # Eliminar la factura
    factura.delete()
    
    flash('Factura eliminada exitosamente', 'success')
    return redirect(url_for('listar_facturas'))

# Rutas para pagos
@app.route('/pagos/crear/<factura_id>', methods=['GET', 'POST'])
@login_required
def crear_pago(factura_id):
    factura = Factura.get_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Verificar que el usuario pertenezca a los apartamentos de esta factura
    if not (current_user.torre == factura.torre and 
            current_user.apartamento in factura.get_apartamentos_asociados()):
        flash('No tienes permiso para pagar esta factura', 'danger')
        return redirect(url_for('listar_facturas'))
    
    # Verificar si ya existe un pago para esta factura y este usuario
    pago_existente = Pago.get_by_factura_y_usuario(factura_id, current_user.id)
    if pago_existente:
        flash('Ya has registrado un pago para esta factura', 'warning')
        return redirect(url_for('detalle_factura', factura_id=factura_id))
    
    if request.method == 'POST':
        monto = float(request.form.get('monto'))
        
        # Crear el pago
        pago = Pago(
            factura_id=factura_id,
            usuario_id=current_user.id,
            monto=monto
        )
        pago.save()
        
        flash('Pago registrado exitosamente', 'success')
        return redirect(url_for('detalle_factura', factura_id=factura_id))
    
    # Calcular el monto que le corresponde a este usuario
    monto_sugerido = factura.calcular_valor_por_apartamento()
    
    return render_template('pagos/create.html', factura=factura, monto_sugerido=monto_sugerido)

@app.route('/pagos/<pago_id>/confirmar', methods=['POST'])
@login_required
def confirmar_pago(pago_id):
    pago = Pago.get_by_id(pago_id)
    if not pago:
        flash('Pago no encontrado', 'danger')
        return redirect(url_for('dashboard'))
    
    factura = Factura.get_by_id(pago.factura_id)
    if not factura:
        flash('Factura asociada no encontrada', 'danger')
        return redirect(url_for('dashboard'))
    
    # Solo el dueño del apartamento base o administrador puede confirmar pagos
    if not current_user.es_administrador and not (
        current_user.torre == factura.torre and 
        current_user.apartamento == factura.apartamento_base and
        current_user.tiene_servicios
    ):
        flash('No tienes permiso para confirmar pagos', 'danger')
        return redirect(url_for('detalle_factura', factura_id=factura.id))
    
    pago.estado = 'confirmado'
    pago.save()
    
    # Verificar si todos los pagos están confirmados para marcar la factura como pagada
    todos_pagos = Pago.get_by_factura(factura.id)
    todos_confirmados = all(p.estado == 'confirmado' for p in todos_pagos)
    if todos_confirmados and len(todos_pagos) == 4:  # Si están los 4 pagos
        factura.estado = 'pagada'
        factura.save()
    
    flash('Pago confirmado exitosamente', 'success')
    return redirect(url_for('detalle_factura', factura_id=factura.id))

@app.route('/pagos/<pago_id>/rechazar', methods=['POST'])
@login_required
def rechazar_pago(pago_id):
    pago = Pago.get_by_id(pago_id)
    if not pago:
        flash('Pago no encontrado', 'danger')
        return redirect(url_for('dashboard'))
    
    factura = Factura.get_by_id(pago.factura_id)
    if not factura:
        flash('Factura asociada no encontrada', 'danger')
        return redirect(url_for('dashboard'))
    
    # Solo el dueño del apartamento base o administrador puede rechazar pagos
    if not current_user.es_administrador and not (
        current_user.torre == factura.torre and 
        current_user.apartamento == factura.apartamento_base and
        current_user.tiene_servicios
    ):
        flash('No tienes permiso para rechazar pagos', 'danger')
        return redirect(url_for('detalle_factura', factura_id=factura.id))
    
    pago.estado = 'rechazado'
    pago.save()
    
    flash('Pago rechazado', 'warning')
    return redirect(url_for('detalle_factura', factura_id=factura.id))

@app.route('/admin/crear-admin', methods=['GET', 'POST'])
@login_required
def crear_admin():
    # Solo administradores pueden crear otros administradores
    if not current_user.es_administrador:
        flash('No tienes permiso para acceder a esta página', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar si ya existe un usuario con ese email
        if Usuario.get_by_email(email):
            flash('Ya existe un usuario con ese correo', 'danger')
            return render_template('auth/create_admin.html')
        
        # Crear el nuevo administrador
        user = Usuario(
            nombre=nombre, 
            email=email, 
            torre=0,  # No asociado a una torre específica
            apartamento=0,  # No asociado a un apartamento específico
            es_administrador=True,
            password=password
        )
        user.save()
        
        flash('Administrador creado exitosamente', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/create_admin.html')

# Rutas para filtros específicos
@app.route('/agua')
@login_required
def ver_agua():
    facturas = Factura.get_by_tipo_servicio('agua')
    
    # Si no es administrador ni tiene servicios, filtrar solo las facturas que le corresponden
    if not current_user.es_administrador and not current_user.tiene_servicios:
        facturas = [f for f in facturas if current_user.torre == f.torre and 
                   current_user.apartamento in f.get_apartamentos_asociados()]
    
    return render_template('servicios/agua.html', facturas=facturas)

@app.route('/energia')
@login_required
def ver_energia():
    facturas = Factura.get_by_tipo_servicio('energia')
    
    # Si no es administrador ni tiene servicios, filtrar solo las facturas que le corresponden
    if not current_user.es_administrador and not current_user.tiene_servicios:
        facturas = [f for f in facturas if current_user.torre == f.torre and 
                   current_user.apartamento in f.get_apartamentos_asociados()]
    
    return render_template('servicios/energia.html', facturas=facturas)

@app.route('/gas')
@login_required
def ver_gas():
    facturas = Factura.get_by_tipo_servicio('gas')
    
    # Si no es administrador ni tiene servicios, filtrar solo las facturas que le corresponden
    if not current_user.es_administrador and not current_user.tiene_servicios:
        facturas = [f for f in facturas if current_user.torre == f.torre and 
                   current_user.apartamento in f.get_apartamentos_asociados()]
    
    return render_template('servicios/gas.html', facturas=facturas)

if __name__ == '__main__':
    app.run(debug=True)