import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@indetex.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

SEED_PRODUCTS = [
    ('REF-01', 'Esprit Ruffle Shirt', 16.64, 25, 'product-01.jpg', 'women'),
    ('REF-02', 'Herschel supply', 35.31, 25, 'product-02.jpg', 'women'),
    ('REF-03', 'Only Check Trouser', 25.50, 25, 'product-03.jpg', 'men'),
    ('REF-04', 'Classic Trench Coat', 75.00, 25, 'product-04.jpg', 'women'),
    ('REF-05', 'Front Pocket Jumper', 34.75, 25, 'product-05.jpg', 'women'),
    ('REF-06', 'Vintage Inspired Classic', 93.20, 25, 'product-06.jpg', 'watches'),
    ('REF-07', 'Shirt in Stretch Cotton', 52.66, 25, 'product-07.jpg', 'women'),
    ('REF-08', 'Pieces Metallic Printed', 18.96, 25, 'product-08.jpg', 'women'),
    ('REF-09', 'Converse All Star Hi Plimsolls', 75.00, 25, 'product-09.jpg', 'shoes'),
    ('REF-10', 'Femme T-Shirt In Stripe', 25.85, 25, 'product-10.jpg', 'women'),
    ('REF-11', 'Herschel supply', 63.16, 25, 'product-11.jpg', 'men'),
    ('REF-12', 'Herschel supply', 63.15, 25, 'product-12.jpg', 'men'),
    ('REF-13', 'T-Shirt with Sleeve', 18.49, 25, 'product-13.jpg', 'women'),
    ('REF-14', 'Pretty Little Thing', 54.79, 25, 'product-14.jpg', 'women'),
    ('REF-15', 'Mini Silver Mesh Watch', 86.85, 25, 'product-15.jpg', 'watches'),
    ('REF-16', 'Square Neck Back', 29.64, 25, 'product-16.jpg', 'women'),
]


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def seed_db():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM product').fetchone()[0] == 0:
        db.executemany(
            'INSERT INTO product (ref, name, price, stock, image, category, description) '
            "VALUES (?, ?, ?, ?, ?, ?, 'Prenda en algodón fabricada por Indetex.')",
            SEED_PRODUCTS,
        )
        db.commit()

    if db.execute('SELECT COUNT(*) FROM user WHERE is_admin = 1').fetchone()[0] == 0:
        db.execute(
            'INSERT INTO user (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)',
            ('Admin', ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD)),
        )
        db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        seed_db()
