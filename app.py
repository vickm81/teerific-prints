from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SECRET_KEY'] = 'ilovecode' 
app.config['CACHE_TYPE'] = 'SimpleCache'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
cache = Cache(app)


# Set the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
db = SQLAlchemy(app)

# database models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(30), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_name = db.Column(db.String(30), nullable=False)
    rate = db.Column(db.Float)
    quantity = db.Column(db.Float)
    size = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(10),nullable=False)
    image_filename = db.Column(db.String(200), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Float)
    order_items = db.relationship('OrderItems', backref='order_items', lazy=True)



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    images = db.relationship('ProductImage', backref='product', cascade="all, delete-orphan", lazy=True)


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_filename = db.Column(db.String(200), nullable=False)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    
    return render_template('product.html', product=product)
    

@app.route('/admin')
@login_required

def admin():
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        new_product = Product(
            name=name,
            description=description,
            price=price
        )
        db.session.add(new_product)
        db.session.commit()

        images = request.files.getlist('images')
        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                new_image = ProductImage(
                    product_id=new_product.id,
                    image_filename=filename
                )
                db.session.add(new_image)

        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('add_product.html')


@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.image_url = request.form['image_url']
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

 # Delete the product (and the associated images due to the cascade delete)
    db.session.delete(product)
    db.session.commit()
    flash('Product and associated images deleted successfully.', 'success')

    return redirect(url_for('admin'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])

    # Calculate the total cost of the cart
    total_cost = 0
    for item in cart:
        total_cost+=item['total_price']

    return render_template('cart.html', cart=cart, total_cost=total_cost)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    size = request.form.get('size')
    quantity = int(request.form.get('quantity'))
    color = request.form.get('color')

    if size == '':
        size = request.form.get('size_kids')   

    # Retrieve the product from the database
    product = Product.query.get_or_404(product_id)
    images = product.images
    for image in images:
        if color.lower() in image.image_filename:
            image_name=image.image_filename


    # Create the cart item as a dictionary
    cart_item = {
        'product_id': product.id,
        'image': image_name,
        'name': product.name,
        'price': product.price,
        'size': size,
        'quantity': quantity,
        'color': color,
        'total_price': product.price * quantity,
    }

    # Ensure the session has a 'cart' key, and that it's a list
    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    # Ensure that cart is a list before appending items
    if isinstance(cart, list):
        item_exists = False

        # Iterate over the cart items to check if the item already exists
        for item in cart:
            if item['product_id'] == product_id and item['size'] == size and item['color'] == color:
                # If the item exists, update its quantity and total price
                item['quantity'] += quantity
                item['total_price'] = item['price'] * item['quantity']
                item_exists = True
                break

        # If the item does not exist in the cart, add it as a new entry
        if not item_exists:
            cart.append(cart_item)

        # Save the updated cart back to the session
        session['cart'] = cart
        session.modified = True

    else:
        # If 'cart' is not a list, reinitialize it as an empty list
        session['cart'] = [cart_item]
        session.modified = True
    

    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', [])

    # create order
    total_cost = 0
    for item in cart:
        total_cost+=item['total_price']

    new_order = Order(
            total = total_cost
        )
    db.session.add(new_order)
    db.session.commit()

    #order items
    for item in cart:
        order_items = OrderItems(
            order_id = new_order.id,
            product_name = item['name'],
            rate = item['price'],
            quantity = item['quantity'],
            size = item['size'],
            color = item['color'],
            image_filename = item['image']   
        )

        db.session.add(order_items)
        db.session.commit()
    
    session['cart']=[]
    return redirect(url_for('submit'))

@app.route('/submit')
def submit():
    order = Order.query.all()

    id = 0
    for item in order:
        id+=1
    message = "Here is my order "
    link = message+"http%3A%2F%2F127.0.0.1:5000/admin/order/"+str(id)
    return redirect('https://wa.me/254768297762?text={}'.format(link))



@app.route('/admin/order/<int:order_id>', methods=['GET'])
def orders(order_id):

    order = Order.query.get_or_404(order_id)
    order_items = OrderItems.query.filter_by(order_id=order_id).all()

    return render_template('orders.html', order=order, order_items=order_items )


@app.route('/cart/remove/<int:product_id>/<string:size>/<string:color>', methods=['POST'])
def remove_from_cart(product_id, size, color):
    cart = session.get('cart', [])

    # Filter out the item with the matching product_id and size
    updated_cart = [item for item in cart if not (item['product_id'] == product_id and item['size'] == size and item['color'])]

    # Update the session cart
    session['cart'] = updated_cart
    session.modified = True

    return redirect(url_for('cart'))


if __name__ == '__main__':
    app.run(debug=True)
    
