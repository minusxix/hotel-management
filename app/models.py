from datetime import datetime
from enum import Enum as UserEnum, Enum as StatusEnum

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from app import db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    USER = 1
    ADMIN = 2


class User(db.Model, UserMixin): #cmnd, sdt, d/c
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER) #import
    receipts = relationship('Receipt', backref='user', lazy=True)

    def __str__(self):
        return self.name


class Category(db.Model):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    rooms = relationship('Room', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Room(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    image = Column(String(100))
    price = Column(Float, default=0)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    receipt_details = relationship('ReceiptDetail', backref='room', lazy=True)

    def __str__(self):
        return self.name


class RoomDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    max = Column(Integer, default=3)
    surcharge = Column(Float, default=0.25)


class Customer(BaseModel):
    type = Column(String(50))
    multiplier = Column(Float, default=1)
    receipt_information = relationship('ReceiptInformation', backref='customer', lazy=True)


class Status(StatusEnum):
    STAY = 1
    BOOK = 2
    PAID = 3

    def __str__(self):
        if self is Status.STAY:
            return "Đã thuê phòng"
        elif self is Status.BOOK:
            return "Chưa thuê phòng"
        else:
            return "Thanh toán"


class Receipt(BaseModel): #id: khóa chính
    created_date = Column(DateTime, default=datetime.now())
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    status = Column(Enum(Status), default=Status.BOOK)
    total = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('ReceiptDetail', backref='receipt', lazy=True)
    information = relationship('ReceiptInformation', backref='receipt', lazy=True)


class ReceiptDetail(BaseModel):
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)


class ReceiptInformation(BaseModel):
    customer_name = Column(String(50), nullable=False)
    identification = Column(Integer, nullable=False)
    address = Column(String(100), nullable=False)
    type_id = Column(Integer, ForeignKey(Customer.id), nullable=False)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)


if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.create_all() #tạo bảng

        # db.drop_all()

        import hashlib

        password = str(hashlib.md5('123'.encode('utf-8')).hexdigest())
        u = User(name='Admin',
                 username='ad',
                 password=password,
                 user_role=UserRole.ADMIN)

        db.session.add(u)
        db.session.commit()

        c1 = Category(name='Basic')
        c2 = Category(name='View')
        c3 = Category(name='VIP')

        db.session.add(c1)
        db.session.add(c2)
        db.session.add(c3)
        db.session.commit()

        r1 = Room(name='1', image='1.jpg', price=100000, category_id=1)
        r2 = Room(name='2', image='1.jpg', price=200000, category_id=2)
        r3 = Room(name='3', image='1.jpg', price=300000, category_id=3)

        db.session.add_all([r1, r2, r3])
        db.session.commit()

        rd = RoomDetail(max='3', surcharge='0.25')

        db.session.add(rd)
        db.session.commit()

        customer1 = Customer(type='Nội địa', multiplier='1')
        customer2 = Customer(type='Nước ngoài', multiplier='1.5')

        db.session.add_all([customer1, customer2])
        db.session.commit()

