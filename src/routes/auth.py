from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario import Usuario
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = Usuario.get_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            flash('Sesión iniciada correctamente', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas. Por favor, intente nuevamente.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        torre = int(request.form.get('torre'))
        apartamento = int(request.form.get('apartamento'))
        password = request.form.get('password')
        
        # Verificar si ya existe un usuario con este email
        usuario_existente = Usuario.get_by_email(email)
        if usuario_existente:
            flash('Ya existe un usuario con este correo electrónico', 'danger')
            return redirect(url_for('register'))
        
        # Verificar si ya existe un usuario con esta torre y apartamento
        usuario_existente = Usuario.get_by_torre_y_apartamento(torre, apartamento)
        if usuario_existente:
            flash('Ya existe un usuario registrado para este apartamento', 'danger')
            return redirect(url_for('register'))
        
        # Crear el nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            torre=torre,
            apartamento=apartamento,
            password=password
        )
        nuevo_usuario.save()
        
        flash('¡Registro exitoso! Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/admin/crear', methods=['GET', 'POST'])
@login_required
def crear_admin():
    # Solo los administradores pueden crear otros administradores
    if not current_user.es_administrador:
        flash('No tiene permisos para realizar esta acción', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar si ya existe un usuario con este email
        usuario_existente = Usuario.get_by_email(email)
        if usuario_existente:
            flash('Ya existe un usuario con este correo electrónico', 'danger')
            return redirect(url_for('crear_admin'))
        
        # Crear el nuevo usuario administrador
        # Nota: los administradores no necesitan torre ni apartamento específicos
        nuevo_admin = Usuario(
            nombre=nombre,
            email=email,
            torre=0,  # 0 indica que es un admin general
            apartamento=0,
            es_administrador=True,
            password=password
        )
        nuevo_admin.save()
        
        flash('Administrador creado correctamente', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/admin.html')