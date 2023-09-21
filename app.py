import os

from flask import Flask, Blueprint, render_template, redirect, url_for, request, flash, abort
from database import *
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
db=CreateDBApp(app)

#---------------------- All operational endpoints --------------#
main = Blueprint('main', __name__)


def search_by_(page):
    categories = Category.query.all()
    products = Product.query.all()
    try:
        Search_By = request.args.get('Search_by')
    except:
        Search_By = None
    return render_template(page, current_user=current_user, products=products, categories=categories, Search_By=Search_By)

def search(query, search_by, categories, products, page):
    try:
        if search_by == 'category':
            cats_cat = []
            prods_cat = []
            for i in range(len(categories)):
                if query.lower() in categories[i].name.lower():
                    cats_cat.append(categories[i])
            for cat in cats_cat:
                for product in products:
                    if product.category_id == cat.id:
                        prods_cat.append(product)
            return render_template(page, current_user=current_user, products=prods_cat, categories=cats_cat)
        elif search_by == 'product':
            prods_prod = []
            cats_prod = []
            for i in range(len(products)):
                if query.lower() in products[i].name.lower():
                    prods_prod.append(products[i])
                    cats_prod.append(products[i].category_id)
            return render_template(page, current_user=current_user, products=prods_prod, categories=cats_prod)
        elif search_by == 'rpu':
            prods_rpu = []
            cats_rpu = []
            query = float(query)
            for i in range(len(products)):
                if float(products[i].rpu) <= query:
                    prods_rpu.append(products[i])
                    cats_rpu.append(products[i].category_id)
            return render_template(page, user=current_user, products=prods_rpu, categories=cats_rpu)
        elif search_by == 'manufacture':
            prods_mfg = []
            cats_mfg = []
            query = datetime.strptime(query,"%Y-%m-%d")
            for i in range(len(products)):
                if query <= products[i].manufacture:
                    prods_mfg.append(products[i])
                    cats_mfg.append(products[i].category_id)
            return render_template(page, user=current_user, products=prods_mfg, categories=cats_mfg)
        elif search_by == 'expiry':
            prods_exp = []
            cats_exp = []
            query = datetime.strptime(query,"%Y-%m-%d")
            for i in range(len(products)):
                if query <= products[i].expiry:
                    prods_exp.append(products[i])
                    cats_exp.append(products[i].category_id)
            return render_template(page, user=current_user, products=prods_exp, categories=cats_exp)
    except Exception as e:
        print(e)
        return render_template(page, current_user=current_user, products=products, categories=categories)


@main.route('/')
def index():
    categories = Category.query.all()
    products = Product.query.all()
    query = request.args.get('query')
    search_by = request.args.get('Search_by')
    try:
        if current_user.role == 'admin':
            page = 'admin.html'
        else:
            page = 'user.html'
    except:
        page = 'user.html'
    if query:
        return search(query, search_by, categories, products, page=page)
    else:
        return search_by_(page=page)


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)


@main.route('/admin')
@login_required
def admin():
    query=request.args.get('query')
    categories = Category.query.all()
    products = Product.query.all()
    search_by = request.args.get('Search_by')
    if query:
        return search(query, search_by, categories, products, page='admin.html')
    else:
        return search_by_(page='admin.html')


@main.route('/checkout', methods=['POST'])
@login_required
def checkout():
    selectedproducts=request.form.get('selectedproducts')
    if selectedproducts:
        selectedproducts=list(map(int, selectedproducts.split(',')))
        products = Product.query.all()
        purchased=[]
        total=0
        over_selected = {}
        for product in products:
            item=[]
            if product.id in selectedproducts:
                if selectedproducts.count(product.id) > product.quantity:
                    over_selected[product.name] = selectedproducts.count(product.id)
                qty = min(selectedproducts.count(product.id), product.quantity)
                total += product.rpu * qty
                item.append(product)
                item.append(qty)
                item.append(product.rpu)
                item.append(product.rpu* qty)
                purchased.append(item)
        vals = ','.join([str(i) for i in list(over_selected.values())])
        keys = ','.join([str(i) for i in list(over_selected.keys())])
        if len(over_selected)>0:
            flash(f"You selected {vals} {keys}, while available stock is not enough\n You may proceed with max available quantity or update your cart.")
        return render_template('checkout.html', purchased=purchased, total=total)
    else:
        flash("Please Select at least one item")
        return redirect(url_for('main.user'))


@main.route('/pay', methods=['POST'])
@login_required
def pay():
    pids=request.form.getlist('pid')
    qnt=request.form.getlist('qnt')
    for i in range(len(qnt)):
        product=Product.query.filter_by(id=int(pids[i])).first()
        product.owner_id=current_user.id
        product.quantity-=int(qnt[i])
        db.session.commit()
    flash("purchased successfully")
    return redirect(url_for('main.user'))


@main.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    query=request.args.get('query')
    categories = Category.query.all()
    products = Product.query.all()
    search_by = request.args.get('Search_by')
    if query:
        return search(query, search_by, categories, products, page='user.html')
    else:
        return search_by_(page='user.html')


@main.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method=='GET':
        print("Existing Categories")
        return render_template('create.html', name=current_user.name)
    elif request.method=='POST':
        name=request.form.get('name')
        category=Category(name=name)
        db.session.add(category)
        db.session.commit()
        print("generating new category")
        return redirect(url_for('main.admin'))


@main.route('/update/<int:cat_id>', methods=['GET', 'POST'])
@login_required
def update(cat_id):
    if isinstance(cat_id, int):
        category=Category.query.filter_by(id=cat_id).first()
        if category and request.method=='GET':
            return render_template('update.html', category=category)
        elif request.method=='POST' and category:
            name=request.form.get('name')
            category.name=name
            db.session.commit()
            return redirect(url_for('main.admin'))
        else:
            abort(404)
    else:
        abort(404)


@main.route('/view/<int:cat_id>', methods=['GET', 'POST'])
@login_required
def view(cat_id):
    if isinstance(cat_id, int):
        category=Category.query.filter_by(id=cat_id).first()
        return render_template('catgory_view.html', category=category)
    else:
        abort(404)


@main.route('/delete/<int:cat_id>', methods=['GET', 'POST'])
@login_required
def delete(cat_id):
    if isinstance(cat_id, int):
        category=Category.query.filter_by(id=cat_id).first()
        if category and request.method=='GET':
            flash('Are you sure you want to delete')
            return render_template('delete.html', category=category)
        elif request.method=='POST' and category:
            for product in category.products:
                if product.owner_id==None:
                    db.session.delete(product)
                    db.session.commit()
                elif product.owner_id!=None: # so that user history has all the product access that he has purchased till now
                    product.category_id=None
                    db.session.commit()
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('main.admin'))
        else:
            abort(404)
    else:
        abort(404)


@main.route('/product', methods=['GET', 'POST'])
@login_required
def product():
    if request.method=='GET':
        categories=Category.query.all()
        # images=Image.query.all()
        images = os.listdir("static")
        images = [image for image in images if image.split(".")[1] == "avif"]
        units = ["l", "ml", "g", "kg", "m", "cm", "inch", "foot", "piece", "dozen"]
        return render_template('product.html', name=current_user.name, categories=categories, images=images, units=units)
    if request.method=='POST':
        category=request.form.get('category')
        name=request.form.get('name')
        image=request.form.get('image')
        manufacture=request.form.get('manufacture')
        rpu=request.form.get('rpu')
        unit=request.form.get('unit')
        quantity=request.form.get('quantity')
        expiry=request.form.get('expiry')
        expiry=datetime.strptime(expiry,"%Y-%m-%d")
        manufacture=datetime.strptime(manufacture,"%Y-%m-%d")
        product=Product(name=name, manufacture=manufacture, rpu=rpu, unit=unit, category_id=int(category), expiry=expiry, image=str(image), quantity=quantity)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('main.admin'))
    

@main.route('/product_update/<int:pro_id>', methods=['GET', 'POST'])
@login_required
def product_update(pro_id):
    if isinstance(pro_id, int):
        product=Product.query.filter_by(id=pro_id).first()
        units = ["l", "ml", "g", "kg", "m", "cm", "inch", "foot", "piece", "dozen"]
        if product and request.method=='GET':
            return render_template('product_update.html', name=current_user.name, product=product, units=units)
        elif request.method=='POST' and product:
            product.name=request.form.get('name')
            product.manufacture = datetime.strptime(request.form.get('manufacture'),"%Y-%m-%d")
            product.expiry = datetime.strptime(request.form.get('expiry'), "%Y-%m-%d")
            product.rpu=request.form.get('rpu')
            product.unit=request.form.get('unit')
            product.quantity=request.form.get('quantity')
            db.session.commit()
            return redirect(url_for('main.admin'))
        else:
            abort(404)
    else:
        abort(404)


@main.route('/product_delete/<int:pro_id>', methods=['GET', 'POST'])
@login_required
def product_delete(pro_id):
    if isinstance(pro_id, int):
        product=Product.query.filter_by(id=pro_id).first()
        if product and request.method=='GET':
            flash('Are you sure you want to delete')
            return render_template('product_delete.html', name=current_user.name, product=product)
        elif request.method=='POST' and product:
            db.session.delete(product)
            db.session.commit()
            return redirect(url_for('main.admin'))
        else:
            abort(404)
    else:
        abort(404)




#-------------------authentication and authorization-----------------#
auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/admin_login')
def admin_login():
    return render_template('adminlogin.html')

@auth.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    entryform= request.form.get('entryform')

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    if user.role=='admin':
        if entryform!='admin':
            flash('Please use admin login form')
            return redirect(url_for('auth.admin_login'))
        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect(url_for('main.admin'))
    else:
        if entryform!='user':
            flash('Please use user login form')
            return redirect(url_for('auth.login'))
        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect(url_for('main.user'))


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    role = request.form.get('role')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.

    new_user = User(email=email, name=name, role=role, password=generate_password_hash(password,method='scrypt'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    if role == 'user':
        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('auth.admin_login'))



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@app.errorhandler(404)
def page_not_found(e):
    flash("Something went wrong")
    return render_template('error.html')

app.register_blueprint(auth)
app.register_blueprint(main)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.filter_by(id=int(user_id)).first()



if __name__=='__main__':
    app.run()