import hashlib

from flask_login import current_user
from sqlalchemy import func, extract, and_

from app import db
from app.models import Category, Room, User, Receipt, ReceiptDetail, Customer, ReceiptInformation, Status


def get_categories():
    return Category.query.all()


def get_rooms(id=None, kw=None):
    query = Room.query
    if id:
        query = query.filter(Room.category_id.__eq__(id))

    if kw:
        query = query.filter(Room.name.contains(kw))

    return query.all()


def get_room_id(id):
    return Room.query.get(id)


def get_customers():
    return Customer.query.all()


def get_user_id(id):
    return User.query.get(id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def register(name, username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name, username=username.strip(), password=password)
    db.session.add(u)
    db.session.commit()


def save_receipt(cart, check_in, check_out): #models.py
    if cart:
        r = Receipt(user=current_user, check_in=check_in, check_out=check_out) #lấy id
        db.session.add(r)
        db.session.commit()


def save_receipt_detail(cart):
    if cart:
        r = Receipt.query.order_by(Receipt.id.desc()).first()
        for c in cart.values():
            rd = ReceiptDetail(quantity=c['quantity'], price=c['price'],
                               room_id=c['id'], receipt=r) #id?
            db.session.add(rd)

        db.session.commit()


def save_receipt_information(cart, customer_name, type_id, identification, address):
    if cart:
        r = Receipt.query.order_by(Receipt.id.desc()).first()
        ri = ReceiptInformation(customer_name=customer_name, type_id=type_id,
                                identification=identification, address=address, receipt=r)
        db.session.add(ri)

        db.session.commit()


def count():
    return db.session.query(Category.id, Category.name, func.count(Room.id))\
             .join(Room, Room.category_id.__eq__(Category.id), isouter=True)\
             .group_by(Category.id).all()


# def stats(): #hỗ trợ
#     query = db.session.query(Category.id, Category.name,
#                              func.sum(ReceiptDetail.price * ReceiptDetail.quantity * func.datediff(Receipt.check_out, Receipt.check_in)),
#                              func.count(Room.id))\
#               .join(Room, Room.category_id.__eq__(Category.id)) \
#               .join(ReceiptDetail, ReceiptDetail.room_id.__eq__(Room.id)) \
#               .join(Receipt, ReceiptDetail.receipt_id.__eq__(Receipt.id))
#     return query.group_by(Category.id).order_by(Category.id).all()


def stats(kw=None, from_date=None, to_date=None):
    subquery = db.session.query(Category.id, func.count(Room.id).label('room_count'))\
                 .join(Room, Room.category_id == Category.id)\
                 .join(ReceiptDetail, ReceiptDetail.room_id == Room.id)\
                 .join(Receipt, and_(ReceiptDetail.receipt_id == Receipt.id, Receipt.status == Status.PAID))\
                 .group_by(Category.id).subquery() #số lượng
    query = db.session.query(Category.id, Category.name,
                             func.sum(ReceiptDetail.price * ReceiptDetail.quantity * func.datediff(Receipt.check_out, Receipt.check_in)).label('total_amount'),
                             subquery.c.room_count,
                             func.cast(subquery.c.room_count * 100.0 / func.sum(subquery.c.room_count).over(), db.Float))\
              .join(Room, Room.category_id == Category.id)\
              .join(ReceiptDetail, ReceiptDetail.room_id == Room.id)\
              .join(Receipt, and_(ReceiptDetail.receipt_id == Receipt.id, Receipt.status == Status.PAID))\
              .join(subquery, subquery.c.id == Category.id) #room_count
    if kw:
        query = query.filter(Category.name.contains(kw))

    if from_date:
        query = query.filter(Receipt.created_date.__ge__(from_date))

    if to_date:
        query = query.filter(Receipt.created_date.__le__(to_date))

    return query.group_by(Category.id, Category.name, subquery.c.room_count).order_by(Category.id).all()


def export_sale():
    sale_data = stats()
    total_sale = sum(row.total_amount for row in sale_data)
    return total_sale


def report(month, year): #kw
    query = db.session.query(func.sum(func.datediff(Receipt.check_out, Receipt.check_in)))\
              .filter(Receipt.status == Status.PAID).scalar() #trả về giá trị đầu tiên
    report = (db.session.query(Room.id, Room.name,
                               func.sum(func.datediff(Receipt.check_out, Receipt.check_in)),
                               func.cast(func.sum(func.datediff(Receipt.check_out, Receipt.check_in)) * 100.0 / query, db.Float))\
                .filter(Receipt.status == Status.PAID)\
                .filter(extract('month', Receipt.created_date) == month)\
                .filter(extract('year', Receipt.created_date) == year)\
                .group_by(Room.name).all())
    return report