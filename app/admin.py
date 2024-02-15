import os
from datetime import datetime

from flask import redirect, request, current_app, flash
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_url
from flask_admin.model import InlineFormAdmin
from flask_login import current_user, logout_user
from werkzeug.utils import secure_filename
from wtforms import FileField

from app import app, db, dao
from app.models import Category, Room, UserRole, Customer, User, Receipt, ReceiptDetail, RoomDetail, ReceiptInformation, Status


class AuthenticatedUser(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class AuthenticatedAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class CategoryView(AuthenticatedAdmin):
    column_list = ['name', 'rooms'] #khóa ngoại
    column_searchable_list = ['name']


class RoomView(AuthenticatedAdmin):
    column_display_pk = True #khóa chính
    column_list = ['name', 'price']
    column_searchable_list = ['name']
    form_extra_fields = {
        'image': FileField('Ảnh minh họa')
    }

    def on_model_change(self, form, model, is_created):
        image_file = form.image.data

        if image_file:
            static_folder = current_app.config.get('STATIC_FOLDER', 'static') #check
            img_folder = os.path.join(static_folder, 'img')

            if not os.path.exists(img_folder):
                os.makedirs(img_folder)

            filename = secure_filename(image_file.filename) #tên
            image_path = os.path.join(img_folder, filename) #lưu
            image_file.save(image_path)
            model.image = os.path.join(filename)

    def get_image_url(self, model):
        return get_url('static', filename=model.image) if model.image else None


class DetailView(AuthenticatedAdmin):
    can_create = False
    can_delete = False


class CustomerView(AuthenticatedAdmin):
    column_display_pk = True
    column_list = ['type', 'multiplier']


class ReceiptDetailInlineForm(InlineFormAdmin):
    form_columns = ('quantity', 'price', 'room_id', 'id')

    def on_model_change(self, form, model, is_created):
        room_id = form.room_id.data
        room = db.session.query(Room).filter(Room.id == room_id).first()

        if room:
            model.price = room.price


class ReceiptInformationInlineForm(InlineFormAdmin):
    form_columns = ('customer_name', 'identification', 'address', 'type_id', 'id')


class ReceiptView(AuthenticatedAdmin):
    column_display_pk = True
    column_default_sort = ('id', True)
    column_list = ['created_date', 'check_in', 'check_out', 'status', 'total', 'user_id', 'id', 'details', 'information']
    inline_models = (ReceiptDetailInlineForm(ReceiptDetail), ReceiptInformationInlineForm(ReceiptInformation))
    column_searchable_list = ['information.customer_name']
    can_view_details = True

    @action('status', 'Status')
    def change_status(self, ids):
        for receipt_id in ids:
            receipt = Receipt.query.get(receipt_id)

            if receipt:
                if receipt.status == Status.BOOK:
                    receipt.status = Status.STAY

        db.session.commit()

    @action('total', 'Total')
    def total(self, ids):
        for receipt_id in ids:
            total = 0
            receipt = Receipt.query.get(receipt_id)

            if receipt:
                receipt_detail = ReceiptDetail.query.filter_by(receipt_id=receipt_id).all()

                for rd in receipt_detail:
                    total += rd.price * rd.quantity

                receipt_info = ReceiptInformation.query.filter_by(receipt_id=receipt_id).first()

                if receipt_info and receipt_info.type_id:
                    count = ReceiptInformation.query.filter_by(receipt_id=receipt_id).count()

                    if count >= 3:
                        room_detail = RoomDetail.query.first()

                        if room_detail:
                            total *= (1 + room_detail.surcharge)

                    customer = Customer.query.get(receipt_info.type_id)

                    if customer and customer.multiplier:
                        total *= customer.multiplier

                if receipt.check_out and receipt.check_in:
                    stay = (receipt.check_out - receipt.check_in).days
                    total *= stay

                receipt.total = total

                if receipt.status == Status.STAY:
                    receipt.status = Status.PAID

        db.session.commit()

    def is_action_allowed(self, name): #xác thực
        if name == 'total':
            return True
        return super(ReceiptView, self).is_action_allowed(name)

    def user_name_formatter(view, context, model, name):
        user = User.query.get(model.user_id)

        if user:
            return user.name
        return None

    def details_formatter(view, context, model, name):
        receipt_detail = ReceiptDetail.query.filter_by(receipt_id=model.id).all()
        room_name = []

        for detail in receipt_detail:
            room = Room.query.get(detail.room_id)
            if room:
                room_name.append(room.name)

        if room_name:
            return ', '.join(room_name)

        return None

    def information_formatter(view, context, model, name):
        receipt_info = ReceiptInformation.query.filter_by(receipt_id=model.id).all()

        if receipt_info:
            info_list = [f"{info.customer_name} ({info.identification})" for info in receipt_info]
            return ', '.join(info_list)

        return None

    column_formatters = {
        'user_id': user_name_formatter,
        'details': details_formatter,
        'information': information_formatter
    }


class StatsView(AuthenticatedUser):
    @expose('/')
    def index(self):
        month = request.args.get("month")
        year = request.args.get("year")
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        stats = dao.stats(kw=request.args.get('kw'),
                          from_date=request.args.get('from_date'),
                          to_date=request.args.get('to_date')) #name
        export = dao.export_sale()
        report = dao.report(month=month, year=year)
        return self.render('admin/stats.html', stats=stats, export=export, report=report)


class AdminView(AdminIndexView):
    @expose('/')
    def index(self):
        count = dao.count()
        return self.render('admin/index.html', count=count)


class LogoutView(AuthenticatedUser):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/admin')


admin = Admin(app=app, name='Quản Lý Khách Sạn', template_mode='bootstrap4', index_view=AdminView()) #admin/index.html
admin.add_view(CategoryView(Category, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(DetailView(RoomDetail, db.session))
admin.add_view(CustomerView(Customer, db.session))
admin.add_view(ReceiptView(Receipt, db.session))
admin.add_view(StatsView(name='Stats'))
admin.add_view(LogoutView(name='Logout'))

