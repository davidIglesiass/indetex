import os
import sqlite3
from functools import wraps

from flask import Flask, render_template, url_for, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

import database

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-insecure-key-change-me')
app.config['DATABASE'] = os.environ.get('DATABASE', os.path.join(app.instance_path, 'indetex.sqlite'))

os.makedirs(app.instance_path, exist_ok=True)
database.init_app(app)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para continuar.')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Acceso solo para administradores.')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def get_products():
    db = database.get_db()
    return db.execute('SELECT * FROM product ORDER BY id').fetchall()


def get_product_or_404(product_id):
    db = database.get_db()
    product = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        flash('Producto no encontrado.')
    return product


@app.route('/')
def index():
    return render_template('index.html', products=get_products())


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/AdminPro')
@admin_required
def Adminpro():
    return render_template('adminProduct.html', products=get_products())


@app.route('/BlogDetail')
def BlogD():
    db = database.get_db()
    comments = db.execute('SELECT * FROM comment ORDER BY id DESC').fetchall()
    return render_template('blog-detail.html', comments=comments)


@app.route('/BlogDetail/comentar', methods=['POST'])
def comentar_blog():
    body = request.form.get('cmt', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    website = request.form.get('web', '').strip()
    if not body or not name:
        flash('El comentario y el nombre son obligatorios.')
        return redirect(url_for('BlogD'))
    db = database.get_db()
    db.execute(
        'INSERT INTO comment (name, email, website, body) VALUES (?, ?, ?, ?)',
        (name, email, website, body),
    )
    db.commit()
    flash('Comentario publicado.')
    return redirect(url_for('BlogD'))


@app.route('/Blog')
def Blog():
    return render_template('blog.html')


@app.route('/producto')
def producto():
    return render_template('product.html', products=get_products())


@app.route('/DetallePro/<int:product_id>')
def detallePro(product_id):
    product = get_product_or_404(product_id)
    if product is None:
        return redirect(url_for('producto'))
    return render_template('product-detail.html', product=product)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = f'{nombre} {apellidos}'.strip()

        if not name or not email or not password:
            flash('Nombre, email y contraseña son obligatorios.')
            return redirect(url_for('registro'))

        db = database.get_db()
        try:
            db.execute(
                'INSERT INTO user (name, email, password_hash) VALUES (?, ?, ?)',
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash('Ya existe una cuenta con ese email.')
            return redirect(url_for('registro'))

        flash('Cuenta creada. Ya puedes iniciar sesión.')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = database.get_db()
        user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Email o contraseña incorrectos.')
            return redirect(url_for('login'))

        session.clear()
        session['user_id'] = user['id']
        session['is_admin'] = bool(user['is_admin'])
        flash(f"Bienvenido, {user['name']}.")
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.')
    return redirect(url_for('index'))


@app.route('/contactanos', methods=['GET', 'POST'])
def contac():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        message = request.form.get('msg', '').strip()
        if not email or not message:
            flash('Email y mensaje son obligatorios.')
            return redirect(url_for('contac'))
        db = database.get_db()
        db.execute('INSERT INTO contact_message (email, message) VALUES (?, ?)', (email, message))
        db.commit()
        flash('Gracias, tu mensaje fue enviado.')
        return redirect(url_for('contac'))

    return render_template('contact.html')


def _product_form_to_fields():
    try:
        price = float(request.form.get('precioProducto', '0') or 0)
        stock = int(request.form.get('stockProducto', '0') or 0)
    except ValueError:
        return None
    # ponytail: the theme's create/edit form only exposes talla/color pickers,
    # not a product category — every admin-created product lands in 'women'
    # so it still shows up in the isotope grid. Add a category select if the
    # catalog needs real classification later.
    return {
        'ref': request.form.get('refProducto', '').strip(),
        'name': request.form.get('nombreProducto', '').strip(),
        'price': price,
        'stock': stock,
        'category': 'women',
        'description': request.form.get('desProducto', '').strip(),
    }


@app.route('/crearProducto', methods=['GET', 'POST'])
@admin_required
def crear():
    if request.method == 'POST':
        fields = _product_form_to_fields()
        if fields is None or not fields['name']:
            flash('Revisa los datos del producto: precio y stock deben ser numéricos.')
            return redirect(url_for('crear'))
        db = database.get_db()
        db.execute(
            'INSERT INTO product (ref, name, price, stock, category, description) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (fields['ref'], fields['name'], fields['price'], fields['stock'],
             fields['category'], fields['description']),
        )
        db.commit()
        flash('Producto creado.')
        return redirect(url_for('Adminpro'))

    return render_template('crearProducto.html')


@app.route('/EditarProducto/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def editar(product_id):
    product = get_product_or_404(product_id)
    if product is None:
        return redirect(url_for('Adminpro'))

    if request.method == 'POST':
        fields = _product_form_to_fields()
        if fields is None or not fields['name']:
            flash('Revisa los datos del producto: precio y stock deben ser numéricos.')
            return redirect(url_for('editar', product_id=product_id))
        db = database.get_db()
        db.execute(
            'UPDATE product SET ref = ?, name = ?, price = ?, stock = ?, category = ?, description = ? '
            'WHERE id = ?',
            (fields['ref'], fields['name'], fields['price'], fields['stock'],
             fields['category'], fields['description'], product_id),
        )
        db.commit()
        flash('Producto actualizado.')
        return redirect(url_for('Adminpro'))

    return render_template('editarProducto.html', product=product)


@app.route('/EliminarProducto/<int:product_id>')
@admin_required
def eliminarProducto(product_id):
    db = database.get_db()
    db.execute('DELETE FROM product WHERE id = ?', (product_id,))
    db.commit()
    flash('Producto eliminado.')
    return redirect(url_for('Adminpro'))


@app.route('/Favoritos')
@login_required
def favoritos():
    db = database.get_db()
    items = db.execute(
        'SELECT product.* FROM wishlist_item '
        'JOIN product ON product.id = wishlist_item.product_id '
        'WHERE wishlist_item.user_id = ? ORDER BY wishlist_item.id',
        (session['user_id'],),
    ).fetchall()
    return render_template('favoritos.html', items=items)


@app.route('/favoritos/agregar/<int:product_id>')
@login_required
def agregarFavorito(product_id):
    # ponytail: GET mutates state so the theme's plain <a> hearts work without
    # rewriting every card into a <form>. Upgrade to POST if this app grows
    # past a single-user demo and CSRF/caching matter.
    db = database.get_db()
    exists = db.execute(
        'SELECT 1 FROM wishlist_item WHERE user_id = ? AND product_id = ?',
        (session['user_id'], product_id),
    ).fetchone()
    if not exists:
        db.execute(
            'INSERT INTO wishlist_item (user_id, product_id) VALUES (?, ?)',
            (session['user_id'], product_id),
        )
        db.commit()
    return redirect(request.referrer or url_for('producto'))


@app.route('/favoritos/eliminar/<int:product_id>')
@login_required
def eliminarFavorito(product_id):
    db = database.get_db()
    db.execute(
        'DELETE FROM wishlist_item WHERE user_id = ? AND product_id = ?',
        (session['user_id'], product_id),
    )
    db.commit()
    flash('Eliminado de favoritos.')
    return redirect(url_for('favoritos'))


@app.route('/ShopingCart')
@login_required
def carroCom():
    db = database.get_db()
    items = db.execute(
        'SELECT cart_item.id AS item_id, cart_item.quantity, product.* '
        'FROM cart_item JOIN product ON product.id = cart_item.product_id '
        'WHERE cart_item.user_id = ? ORDER BY cart_item.id',
        (session['user_id'],),
    ).fetchall()
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('shoping-cart.html', items=items, total=total)


@app.route('/carrito/agregar/<int:product_id>', methods=['POST'])
@login_required
def agregarCarrito(product_id):
    try:
        quantity = max(1, int(request.form.get('num-product', 1)))
    except ValueError:
        quantity = 1
    db = database.get_db()
    existing = db.execute(
        'SELECT id, quantity FROM cart_item WHERE user_id = ? AND product_id = ?',
        (session['user_id'], product_id),
    ).fetchone()
    if existing:
        db.execute(
            'UPDATE cart_item SET quantity = ? WHERE id = ?',
            (existing['quantity'] + quantity, existing['id']),
        )
    else:
        db.execute(
            'INSERT INTO cart_item (user_id, product_id, quantity) VALUES (?, ?, ?)',
            (session['user_id'], product_id, quantity),
        )
    db.commit()
    flash('Producto añadido al carrito.')
    return redirect(url_for('carroCom'))


@app.route('/carrito/eliminar/<int:item_id>', methods=['POST'])
@login_required
def eliminarDelCarrito(item_id):
    db = database.get_db()
    db.execute('DELETE FROM cart_item WHERE id = ? AND user_id = ?', (item_id, session['user_id']))
    db.commit()
    flash('Producto eliminado del carrito.')
    return redirect(url_for('carroCom'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
