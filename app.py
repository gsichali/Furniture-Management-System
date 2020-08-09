from flask import make_response, flash, redirect, url_for, session, request, logging, jsonify
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_wtf import Form,FlaskForm
from wtforms import DateField, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
# from extensions import csrf
from flask_wtf.csrf import CsrfProtect
from time import gmtime, strftime
from functools import wraps
import bcrypt
import pdfkit
import hashlib
from twilio.rest import Client
from datetime import date
import dbConnect
import mysql.connector as mysql
import os


app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = "secret key"
# csrf.init_app(app)
CsrfProtect(app)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'webapp'
# init MYSQL
mysql = MySQL(app)

@app.route("/")
def main():
   return redirect(url_for('login'))

# ------------------------------------------------------------------------Register Router------------------------------------------------------------------------------------#
class RdgisterForm(FlaskForm):
    firstname = StringField('firstname', [validators.Length(min=1, max=10)])
    lastname = StringField('lastname', [validators.Length(min=1, max=10)])
    email = StringField('email', [validators.Length(min=1, max=30)])
    password = StringField('password', [validators.Length(min=1, max=20)])
    confirmpass = TextAreaField('confirmpass', [validators.Length(min=1, max=20)])

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RdgisterForm(request.form)
    if request.method == 'GET':
        return render_template("register.html", form=form)
    else:
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = firstname + " "+ lastname
        email = request.form['email']
        password = request.form['password']
        temp_hash = hashlib.md5(password.encode())
        hash_password = temp_hash.hexdigest()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO webapp.login_details (username, password,email) VALUES (%s,%s,%s)",(username,hash_password,email))
        mysql.connection.commit()
        cur.close()
        flash('registered')

        return redirect(url_for('login'))
    return render_template("register.html", form=form)

# ------------------------------------------------------------------------User login------------------------------------------------------------------------------------#
class LoginForm(FlaskForm):
    email = StringField('email', [validators.Length(min=1, max=30)])
    password = StringField('password', [validators.Length(min=1, max=20)])

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = RdgisterForm(request.form)
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM login_details WHERE email = %s", [email])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data[1]
            email = data[0]

            temp_hash = hashlib.md5(password_candidate.encode())
            hash_password = temp_hash.hexdigest()
            # Compare Passwords
            if password == hash_password :
                # Passed
                session['logged_in'] = True
                session['email'] = email
                #session['username'] = username

                print("Success login", session['email'])
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                print("Failed login", error)
                return render_template('login.html', form=form,  error=error)
            # Close connection
            cur.close()
        else:
            error = 'User email not found'
            return render_template('login.html', form=form, error=error)

    return render_template('login.html', form=form)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def sign_out():
    session.pop('logged_in')
    session.pop('email')
    return redirect(url_for('login'))
# ------------------------------------------------------------------------Dashboard Router------------------------------------------------------------------------------------#
@app.route('/dashboard')
@is_logged_in
def dashboard():
   return render_template("dashboard.html")

@app.route('/dashboard/getsparkdata', methods=['GET', 'POST'])
@is_logged_in
def getSparkData():
    cur = mysql.connection.cursor()

    # Transaction In data by day
    cur.execute("SELECT SUM(amount), DATE FROM TRANSACTION WHERE transaction_type = 'in' GROUP BY transaction.date ORDER BY transaction.date DESC LIMIT 7")
    inTransactionData = cur.fetchall()

    cur.execute("SELECT SUM(amount), DATE FROM TRANSACTION WHERE transaction_type = 'out' GROUP BY transaction.date ORDER BY transaction.date DESC LIMIT 7")
    outTransactionData = cur.fetchall()

    cur.execute("SELECT SUM(quantity * cost) total FROM product")
    totalProduct = cur.fetchone()

    cur.execute("SELECT  transaction_type , SUM(amount) FROM TRANSACTION GROUP BY transaction_type ORDER BY transaction_type")
    totalInOut = cur.fetchall()

    cur.execute("SELECT product_name, quantity, (quantity * cost) AS total_cost FROM product")
    productInfo = cur.fetchall()

    cur.close()

    return jsonify({'status':'success', 'inTransactionData': inTransactionData, 'outTransactionData': outTransactionData, 'totalProduct':totalProduct, 'totalInOut':totalInOut, 'productInfo': productInfo})

# ------------------------------------------------------------------------Customer Router------------------------------------------------------------------------------------#
class CustomerForm(FlaskForm):
    firstname = StringField('firstname', [validators.Length(min=1, max=10)])
    lastname = StringField('lastname', [validators.Length(min=1, max=10)])
    email = StringField('email', [validators.Length(min=1, max=30)])
    contact = StringField('contact', [validators.Length(min=10, max=13)])
    address = TextAreaField('address', [validators.Length(min=1)])

@app.route('/customer/view', methods=['GET', 'POST'])
@is_logged_in
def viewCustomer():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM customer ORDER BY customer_id ASC")
    if result > 0:
        data = cur.fetchall()
    return render_template('viewCustomer.html', customers = data)

@app.route('/customer/add', methods=['GET', 'POST'])
@is_logged_in
def addCustomer():
    form = CustomerForm(request.form)
    if form.validate() :
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        contact = form.contact.data
        address= form.address.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO webapp.customer(firstname, lastname, email, contact, address) VALUES(%s, %s, %s, %s, %s)", (firstname, lastname, email, contact, address))

        mysql.connection.commit()
        cur.close()

        return render_template('addCustomer.html', form=form, success=True)

    else :
        print(form.errors)
        return render_template('addCustomer.html', form=form)

@app.route('/customer/edit/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def editCustomer(id):
    form = CustomerForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            firstname = form.firstname.data
            lastname = form.lastname.data
            email = form.email.data
            contact = form.contact.data
            address= form.address.data

            cur = mysql.connection.cursor()
            cur.execute("UPDATE customer SET firstname = %s, lastname = %s, email = %s, contact = %s, address = %s   WHERE customer_id = %s", [firstname, lastname, email, contact, address, id])

            mysql.connection.commit()

            result = cur.execute("SELECT * FROM customer WHERE customer_id = %s LIMIT 1" , [id])
            if result > 0:
                data = cur.fetchone()
                cur.close()
            return render_template('editCustomer.html', form=form, customer=data, success=True)

        else :
            return render_template('editCustomer.html', form=form)
    else:
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM customer WHERE customer_id = %s LIMIT 1" , [id])
        if result > 0:
            data = cur.fetchone()
        return render_template('editCustomer.html', form=form, customer=data)

@app.route('/customer/delete', methods=['GET', 'POST'])
@is_logged_in
def deleteCustomer():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customer WHERE customer_id = %s", [request.form['customer_id']])
    mysql.connection.commit()
    cur.close()

    return jsonify({'status':'success'})
# ------------------------------------------------------------------------Product Router------------------------------------------------------------------------------------#
class ProductForm(FlaskForm):
    productName = StringField('productName', [validators.Length(min=1, max=20)])
    location = StringField('location', [validators.Length(min=1, max=20)])
    quantity = StringField('quantity', [validators.Length(min=1, max=20)])
    cost = StringField('cost', [validators.Length(min=1)])

@app.route('/stock', methods=['GET', 'POST'])
@is_logged_in
def viewProduct():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM product ORDER BY product_id ASC")
    if result > 0:
        data = cur.fetchall()
    return render_template('viewProduct.html', products = data)

@app.route('/product/add', methods=['GET', 'POST'])
@is_logged_in
def addProduct():
    form = ProductForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            productName = form.productName.data
            location = form.location.data
            quantity = form.quantity.data
            cost = form.cost.data

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO product(product_name, location, quantity, cost) VALUES(%s, %s, %s, %s)", (productName, location, quantity, cost))

            mysql.connection.commit()
            cur.close()

            return render_template('addProduct.html', form=form, success=True)

        else :
            print(form.errors)
            return render_template('addProduct.html', form=form)
    else:
        return render_template('addProduct.html', form=form)

@app.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def editProduct(id):
    form = ProductForm(request.form)
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        if form.validate() :
            productName = form.productName.data
            location = form.location.data
            quantity = form.quantity.data
            cost = form.cost.data


            cur.execute("UPDATE product SET product_name = %s, location = %s, quantity = %s, cost = %s   WHERE product_id = %s", [productName, location, quantity, cost, id])

            mysql.connection.commit()
            success = True
        else :
            print(form.errors)
            success = False
    else:
        success = False

    result = cur.execute("SELECT * FROM product WHERE product_id = %s LIMIT 1" , [id])
    if result > 0:
        data = cur.fetchone()
        cur.close()
    return render_template('editProduct.html', form=form, product=data, success=success)

@app.route('/product/delete', methods=['GET', 'POST'])
@is_logged_in
def deleteProduct():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM product WHERE product_id = %s", [request.form['product_id']])
    mysql.connection.commit()
    cur.close()

    return jsonify({'status':'success'})
# ------------------------------------------------------------------------Supplier Router------------------------------------------------------------------------------------#
class SupplierForm(FlaskForm):
    supplierName = StringField('supplierName', [validators.Length(min=1, max=30)])
    email = StringField('email', [validators.Length(min=1, max=30)])
    phone = StringField('phone', [validators.Length(min=9, max=13)])
    address = TextAreaField('address', [validators.Length(min=1)])

@app.route('/supplier/view', methods=['GET', 'POST'])
@is_logged_in
def viewSupplier():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM supplier ORDER BY supplier_id ASC")
    if result > 0:
        data = cur.fetchall()
    return render_template('viewSupplier.html', suppliers = data)

@app.route('/supplier/add', methods=['GET', 'POST'])
@is_logged_in
def addSupplier():
    form = SupplierForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            supplierName = form.supplierName.data
            email = form.email.data
            phone = form.phone.data
            address = form.address.data

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO supplier(supplier_name, email, phone, address) VALUES(%s, %s, %s, %s)", (supplierName, email, phone, address))

            mysql.connection.commit()
            cur.close()

            return render_template('addSupplier.html', form=form, success=True)

        else :
            print(form.errors)
            return render_template('addSupplier.html', form=form)
    else:
        return render_template('addSupplier.html', form=form)


@app.route('/supplier/edit/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def editSupplier(id):
    form = SupplierForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            supplierName = form.supplierName.data
            email = form.email.data
            phone = form.phone.data
            address= form.address.data

            cur = mysql.connection.cursor()
            cur.execute("UPDATE supplier SET supplier_name = %s, email = %s, phone = %s, address = %s   WHERE supplier_id = %s", [supplierName, email, phone, address, id])

            mysql.connection.commit()

            result = cur.execute("SELECT * FROM supplier WHERE supplier_id = %s LIMIT 1" , [id])
            if result > 0:
                data = cur.fetchone()
                cur.close()
            return render_template('editSupplier.html', form=form, supplier=data, success=True)

        else :
            print(form.errors)
            cur = mysql.connection.cursor()
            result = cur.execute("SELECT * FROM supplier WHERE supplier_id = %s LIMIT 1" , [id])
            if result > 0:
                data = cur.fetchone()
                cur.close()
            return render_template('editSupplier.html', form=form, supplier=data)
    else:
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM supplier WHERE supplier_id = %s LIMIT 1" , [id])
        if result > 0:
            data = cur.fetchone()
            cur.close()
        return render_template('editSupplier.html', form=form, supplier=data)

@app.route('/supplier/delete', methods=['GET', 'POST'])
@is_logged_in
def deleteSupplier():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM supplier WHERE supplier_id = %s", [request.form['supplier_id']])
    mysql.connection.commit()
    cur.close()

    return jsonify({'status':'success'})

# -----------------------------------------------------------------------Transaction------------------------------------------------------------------------------------#
class InTransactionForm(FlaskForm):
    supplier = StringField('supplier', [validators.Length(min=1, max=30)])
    product = StringField('product', [validators.Length(min=1, max=20)])
    units = StringField('units', [validators.Length(min=1)])
    amount = StringField('amount', [validators.Length(min=1)])
    date = StringField('date', [validators.Length(min=1)])

class OutTransactionForm(FlaskForm):
    customer = StringField('customer', [validators.Length(min=1, max=30)])
    product = StringField('product', [validators.Length(min=1, max=20)])
    units = StringField('units', [validators.Length(min=1)])
    amount = StringField('amount', [validators.Length(min=1)])
    date = StringField('date', [validators.Length(min=1)])

@app.route('/transaction/in', methods=['GET', 'POST'])
@is_logged_in
def inTransaction():
    form = InTransactionForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            supplier = form.supplier.data
            product = form.product.data
            units = form.units.data
            amount = form.amount.data
            date = form.date.data
            transaction_type = "in"

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO transaction(transaction_type, from_to, product, units, amount, date) VALUES(%s, %s, %s, %s, %s, %s)", (transaction_type, supplier, product, units, amount, date))

            mysql.connection.commit()
            cur.close()

            success = True
        else :
            print(form.errors)
            success = False
    else:
        success = False

    cur = mysql.connection.cursor()

    supplierResult = cur.execute("SELECT * FROM supplier ORDER BY supplier_id ASC")
    if supplierResult > 0:
        supplierData = cur.fetchall()

    productResult = cur.execute("SELECT * FROM product ORDER BY product_id ASC")
    if productResult > 0:
        productData = cur.fetchall()
    return render_template('addInTransaction.html', form = form, suppliers = supplierData, products = productData, success = success)

@app.route('/transaction/out', methods=['GET', 'POST'])
@is_logged_in
def outTransaction():
    form = OutTransactionForm(request.form)
    if request.method == 'POST':
        if form.validate() :
            customer = form.customer.data
            product = form.product.data
            units = form.units.data
            amount = form.amount.data
            date = form.date.data
            transaction_type = "out"

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO transaction(transaction_type, from_to, product, units, amount, date) VALUES(%s, %s, %s, %s, %s, %s)", (transaction_type, customer, product, units, amount, date))

            mysql.connection.commit()
            cur.close()

            success = True
        else :
            print(form.errors)
            success = False
    else:
        success = False

    cur = mysql.connection.cursor()

    customerResult = cur.execute("SELECT * FROM customer ORDER BY customer_id ASC")
    if customerResult > 0:
        customerData = cur.fetchall()

    productResult = cur.execute("SELECT * FROM product ORDER BY product_id ASC")
    if productResult > 0:
        productData = cur.fetchall()
    return render_template('addOutTransaction.html', form = form, customers = customerData, products = productData, success = success)

@app.route('/transaction/getproduct/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def getProduct(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM product WHERE product_id = %s LIMIT 1" , [id])
    data = cur.fetchone()
    cur.close()

    return jsonify({'status':'success', 'data': data})
# -----------------------------------------------------------------------Reports Router------------------------------------------------------------------------------------#
class ReportForm(FlaskForm):
    transactionId = StringField('transactionId', [validators.Length(min=1, max=30)])
    transactionType = StringField('transactionType')

@app.route('/reports', methods=['GET', 'POST'])
@is_logged_in
def viewTransaction():
    form = ReportForm(request.form)
    cur = mysql.connection.cursor()
    if request.method == 'GET':
        return render_template('viewTransaction.html', form=form)
    else:
        transactionId = form.transactionId.data
        transactionType = form.transactionType.data
        if transactionId == '':
            if transactionType == 'in':
                result = cur.execute("SELECT tr.*, sp.supplier_name,  pr.product_name, date  FROM webapp.transaction AS tr LEFT JOIN supplier AS sp ON tr.`from_to` = sp.`supplier_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE transaction_type = %s ORDER BY tr.transaction_id ASC", [transactionType])
            else:
                result = cur.execute("SELECT tr.*, ct.firstname, pr.product_name, date FROM webapp.transaction AS tr LEFT JOIN customer AS ct ON tr.`from_to` = ct.`customer_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE transaction_type = %s ORDER BY tr.transaction_id ASC", [transactionType])

        else:
            if transactionType == 'in':
                result = cur.execute("SELECT tr.*, sp.supplier_name, pr.product_name, date FROM webapp.transaction AS tr LEFT JOIN supplier AS sp ON tr.`from_to` = sp.`supplier_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE transaction_type = %s AND transaction_id = %s ORDER BY tr.transaction_id ASC", [transactionType, transactionId])
            else:
                result = cur.execute("SELECT tr.*, ct.firstname, pr.product_name, date FROM webapp.transaction AS tr LEFT JOIN customer AS ct ON tr.`from_to` = ct.`customer_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE transaction_type = %s AND transaction_id = %s ORDER BY tr.transaction_id ASC", [transactionType, transactionId])

        if result > 0:
            data = cur.fetchall()
            return render_template('viewTransaction.html', transactions=data, trId=transactionId, trType=transactionType, form=form)
        else:
            return render_template('viewTransaction.html',trId=transactionId, trType=transactionType, form=form)

# -----------------------------------------------------------------------Monthly Reports Router------------------------------------------------------------------------------------#
class MonthlyReportForm(FlaskForm):
    fromDate = StringField('fromDate', [validators.Length(min=1, max=30)])
    toDate = StringField('toDate', [validators.Length(min=1, max=30)])

@app.route('/currentmonth', methods=['GET', 'POST'])
@is_logged_in
def viewMonthlyTransaction():
    form = MonthlyReportForm(request.form)
    cur = mysql.connection.cursor()
    if request.method == 'GET':

        fromDate = strftime("%Y-%m")+'-01'
        toDate = strftime("%Y-%m-%d", gmtime())
    else:
        fromDate = form.fromDate.data
        toDate = form.toDate.data

    inResult = cur.execute("SELECT tr.*,  sp.supplier_name, pr.product_name FROM webapp.transaction AS tr LEFT JOIN supplier AS sp ON tr.`from_to` = sp.`supplier_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE tr.date >=  %s And tr.date <= %s AND tr.transaction_type='in' ORDER BY tr.transaction_id ASC", [fromDate, toDate])
    inData = cur.fetchall()
    #inResult = cur.execute("SELECT tr.*,  pr.product_name FROM webapp.product AS tr LEFT JOIN supplier AS sp ON tr.`from_to` = sp.`supplier_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE tr.date >=  %s And tr.date <= %s AND tr.transaction_type='in' ORDER BY tr.transaction_id ASC", [fromDate, toDate])
    #inData = cur.fetchall()

    outResult = cur.execute("SELECT tr.*,  ct.firstname, pr.product_name FROM webapp.transaction AS tr LEFT JOIN customer AS ct ON tr.`from_to` = ct.`customer_id` LEFT JOIN product AS pr ON tr.product =  pr.product_id WHERE tr.date >=  %s And tr.date <= %s AND tr.transaction_type='out' ORDER BY tr.transaction_id ASC", [fromDate, toDate])
    outData = cur.fetchall()

    return render_template('viewMonthlyTransaction.html', inTransactions=inData, outTransactions=outData, form=form)

# -----------------------------------------------------------------------Update page------------------------------------------------------------------------------------#
@app.route('/update',methods=['POST','GET'])
@is_logged_in
def update():

    if request.method == 'POST':
        product_id = request.form['id']
        product_name = request.form['name']
        location = request.form['location']
        quantity = request.form['quantity']
        cost = request.form['cost']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
               UPDATE stock
               SET name=%s, location=%s, quantity=%s, cost=%s
               WHERE id=%s
            """, (product_name, location, quantity,cost,product_id))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return 'updated'
        #return redirect(url_for('Index'))
    return render_template('index.html',msg=msg)



if __name__ =='__main__':
    app.run(debug=True)
