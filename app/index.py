from flask import render_template, request, session, jsonify, redirect
from flask_login import login_user, logout_user

from app import app, dao, login
from app.decorators import annonymous
from app.models import RoomDetail


@app.route('/')
def index():
    id = request.args.get('id') #important '?'
    # categories = dao.get_categories() #categories=categories
    kw = request.args.get('keyword')
    rooms = dao.get_rooms(id=id, kw=kw)
    return render_template('index.html', rooms=rooms) #for html


@app.route('/room/<id>')
def detail(id):
    r = dao.get_room_id(id)
    return render_template('detail.html', room=r) #for html


@login.user_loader
def get_user(id):
    return dao.get_user_id(id)


@app.route('/admin/login', methods=['post']) #action
def admin_login(): #init
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    return redirect('/admin')


@app.route('/login', methods=['get', 'post'])
@annonymous
def user_login():
    if request.method.__eq__('POST'):
        username = request.form['username']
        password = request.form['password']
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)
            n = request.args.get("next")
            return redirect(n if n else '/')

    return render_template('login.html')


@app.route('/register', methods=['get', 'post'])
def register():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form['password']
        confirm = request.form['confirm']
        if password.__eq__(confirm):
            try:
                dao.register(name=request.form['name'], username=request.form['username'], password=password)
                return redirect('/login')
            except:
                err_msg = 'Hệ thống đang có lỗi! Vui lòng quay lại sau!'
        else:
            err_msg = 'Mật khẩu ko khớp!'

    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.context_processor
def common():
    return {
        'categories': dao.get_categories(),
        'customers': dao.get_customers(),
        'cart': count_cart(session.get('cart'))
    }


@app.route('/cart')
def cart(): #hàm khi trỏ /cart chuyển đến trang cart.html
    max_value = RoomDetail.query.first().max if RoomDetail.query.first() else 0
    return render_template('cart.html', max_value=max_value)


def count_cart(cart): #utils
    total_quantity, total_amount = 0, 0
    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']

    return {
        "total_quantity": total_quantity,
        "total_amount": total_amount
    }


@app.route('/api/cart', methods=['post'])
def add_cart():
    cart = session.get('cart')
    if cart is None:
        cart = {}

    data = request.json
    print(data)
    id = str(data.get("id"))
    if id in cart: #co trong gio
        cart[id]["quantity"] = cart[id]["quantity"] + 1
    else: #chua co trong gio
        cart[id] = {
            "id": id,
            "name": data.get("name"),
            "price": data.get("price"),
            "quantity": 1
        }

    session['cart'] = cart
    return jsonify(count_cart(cart))


@app.route("/api/cart/<room_id>", methods=['put'])
def update_cart(room_id):
    cart = session.get('cart')
    if cart and room_id in cart:
        cart[room_id]['quantity'] = int(request.json.get('quantity'))

    session['cart'] = cart
    return jsonify(count_cart(cart))


@app.route("/api/cart/<room_id>", methods=['delete'])
def delete_cart(room_id):
    cart = session.get('cart')
    if cart and room_id in cart:
        del cart[room_id] #xóa

    session['cart'] = cart
    return jsonify(count_cart(cart))


@app.route('/api/pay', methods=['post'])
def pay():
    key = app.config['CART_KEY']
    cart = session.get(key)
    if cart:
        try:
            customer_data = request.json.get('customers')
            check_in = customer_data[0].get('check_in')
            check_out = customer_data[0].get('check_out')
            dao.save_receipt(cart=cart, check_in=check_in, check_out=check_out)
            dao.save_receipt_detail(cart=cart)
            for cd in customer_data:
                customer_name = cd.get('customer_name')
                type_id = cd.get('type_id')
                identification = cd.get('identification')
                address = cd.get('address')
                dao.save_receipt_information(cart=cart, customer_name=customer_name, type_id=type_id, identification=identification, address=address)
        except Exception as ex:
            print(str(ex))
            return jsonify({"status": 500})
        else:
            del session[key]

    return jsonify({"status": 200})


if __name__ == '__main__':
    from app import admin
    app.run(debug=True)