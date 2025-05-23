from flask import Flask, render_template, request, jsonify, redirect, url_for,flash, session
import mysql.connector
from mysql.connector import Error
import os, random
from werkzeug.utils import secure_filename
import mysql.connector
import sqlite3  
from flask_mail import Mail, Message
from datetime import timedelta
import threading 
import time
import logging
import string
import sqlite3
from datetime import datetime
from flask import current_app as app
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://192.168.0.21:5000"])


app.secret_key = 'your_secret_key'  # Change this to a random secret key for session management

# Set the UPLOAD_FOLDER configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mediaverse888@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'tyyy vefg uvyl jhwf'  # The app password you generated
app.config['MAIL_DEFAULT_SENDER'] = 'mediaverse888@gmail.com'
mail = Mail(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Use appropriate password
        database="dashboardss"
    )

@app.route('/')
def index():
    return redirect(url_for('login_page'))  # Redirect to the login page



@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        return login()  # Handle login form submission
    return render_template('login.html')  # Render the login page

@app.route('/formsreg', methods=['GET', 'POST'])
def formsreg():
    if request.method == 'POST':
        return submit_form()  # Handle form submission
    return render_template('formsreg.html')  # Ensure you have this template



@app.route('/submit_form', methods=['POST'])
def submit_form():
    name = request.form.get('Name')
    email = request.form.get('Email')
    password = request.form.get('Password')
    gender = request.form.get('Gender')
    role = request.form.get('Role')
    phone_number = request.form.get('PhoneNumber')
    physical_address = request.form.get('PhysicalAddress')
    
    # Validate password
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."})
    
    # Get courier-specific fields if role is Courier
    vehicle_type = request.form.get('VehicleType') if role == 'Courier' else None
    license_plate = request.form.get('LicensePlate') if role == 'Courier' else None
    id_number = request.form.get('IDNumber') if role == 'Courier' else None
    service_area = request.form.get('ServiceArea') if role == 'Courier' else None
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        sql = "SELECT * FROM userinfo WHERE Email = %s"
        cursor.execute(sql, (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({"error": "User already exists. Please log in or use a different email."})
        
        # Insert new user
        if role == 'Courier':
            sql = """
            INSERT INTO userinfo (
                Name, Email, Password, Gender, Role, PhoneNumber, PhysicalAddress,
                VehicleType, LicensePlate, IDNumber, ServiceArea, Status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                name, email, password, gender, role, phone_number, physical_address,
                vehicle_type, license_plate, id_number, service_area, 'pending'
            )
        else:
            sql = """
            INSERT INTO userinfo (
                Name, Email, Password, Gender, Role, PhoneNumber, PhysicalAddress
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (name, email, password, gender, role, phone_number, physical_address)
        
        cursor.execute(sql, values)
        conn.commit()
        
        # Handle special roles
        if role == 'Seller':
            session['user'] = {'name': name, 'role': role, 'email': email}
            return redirect(url_for('seller_follow_up'))
        elif role == 'Courier':
            return jsonify({"message": "Courier registration successful! Your account is pending approval."})
        
        return jsonify({"message": "Registration successful, just wait for admin approval!"})
        
    except Error as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




import uuid

@app.route('/seller_follow_up', methods=['GET', 'POST'])
def seller_follow_up():
    if 'user' not in session or session['user']['role'] != 'Seller':
        return redirect(url_for('login_page'))  # Ensure only sellers can access this page

    if request.method == 'POST':
        business_name = request.form['BusinessName']
        email = session['user']['email']
        business_permit = request.files['BusinessPermit']
        dti_permit = request.files['DTI']
        bir_permit = request.files['BIR']

        upload_paths = {}

        # Handle file uploads
        for permit_name, permit_file in [('BusinessPermit', business_permit), ('DTI', dti_permit), ('BIR', bir_permit)]:
            if permit_file:
                unique_filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(permit_file.filename)[1])
                permit_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                permit_file.save(permit_path)
                upload_paths[permit_name] = permit_path

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the user already exists
            cursor.execute("SELECT * FROM userinfo WHERE Email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Update the database
                sql = """
                UPDATE userinfo
                SET Business_name = %s, BusinessPermit = %s, DTI_permit = %s, BIR_permit = %s
                WHERE Email = %s
                """
                values = (business_name, upload_paths.get('BusinessPermit'), upload_paths.get('DTI'), upload_paths.get('BIR'), email)
                cursor.execute(sql, values)
            else:
                sql = """
                INSERT INTO userinfo (Business_name, Email, BusinessPermit, DTI_permit, BIR_permit)
                VALUES (%s, %s, %s, %s, %s)
                """
                values = (business_name, email, upload_paths.get('BusinessPermit'), upload_paths.get('DTI'), upload_paths.get('BIR'))
                cursor.execute(sql, values)

            conn.commit()
            flash("Seller information saved successfully!", "success")

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('seller_follow_up'))

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login_page'))

    return render_template('seller_follow_up.html', user=session['user']['name'])



@app.route('/seller_profile')
def seller_profile():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Retrieve the user's session information
    userinfo = session.get('user')
    user_id = userinfo.get('id')  # Ensure safe access

    if not user_id:
        flash('Invalid user session. Please log in again.', 'danger')
        return redirect(url_for('login'))

    # Get the database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Query user data including business_name
        query = """
            SELECT Name, Email, PhoneNumber, PhysicalAddress, Gender, Business_name
            FROM userinfo WHERE ID = %s
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if user:
            # Update user info from database
            userinfo.update({
                'name': user[0],
                'email': user[1],
                'phone_number': user[2],
                'physical_address': user[3],
                'gender': user[4],
                'business_name': user[5]
            })
        else:
            flash('User profile could not be found.', 'danger')
            return redirect(url_for('sellerdash'))

    except Exception as e:
        # Log the exception securely
        print(f"Error fetching user profile: {e}")
        flash('An error occurred while loading your profile. Please try again later.', 'danger')
        return redirect(url_for('homepage'))

    finally:
        # Always close the cursor and connection
        cursor.close()
        conn.close()

    return render_template('seller_profile.html', userinfo=userinfo)

@app.route('/update_seller', methods=['POST'])
def update_seller():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Retrieve the user's session information
    userinfo = session['user']
    user_id = userinfo['id']  # Assuming 'id' is stored in session

    # Get updated info from form submission
    name = request.form.get('name')
    business_name = request.form.get('business_name')  # Corrected to match the form's input name
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    address = request.form.get('physical_address')  # Fixed key name to match the form
    gender = request.form.get('gender')  # Get the selected gender

    # Ensure all fields are provided
    if not all([name, business_name, email, phone_number, address, gender]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('seller_profile'))

    # Get the database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # SQL update query
        sql = """
            UPDATE userinfo
            SET Name = %s, Business_name = %s, Email = %s, PhoneNumber = %s, PhysicalAddress = %s, Gender = %s
            WHERE ID = %s
        """
        values = (name, business_name, email, phone_number, address, gender, user_id)

        # Execute the UPDATE query
        cursor.execute(sql, values)
        conn.commit()

        # Check if the update was successful
        if cursor.rowcount > 0:
            flash('Profile updated successfully!', 'success')
            # Update session data
            session['user']['name'] = name
            session['user']['business_name'] = business_name  # Update business name in session
            session['user']['email'] = email
            session['user']['phone_number'] = phone_number
            session['user']['physical_address'] = address
            session['user']['gender'] = gender  # Update gender in session
            session.modified = True  # Mark the session as modified
        else:
            flash('No changes were made to your profile.', 'info')

    except Exception as e:
        flash('An error occurred while updating your profile. Please try again later.', 'danger')
        print(f"Error executing query: {e}")
        conn.rollback()

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

    # Redirect back to the profile page
    return redirect(url_for('seller_profile'))



@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Get user data from session
    userinfo = session['user']

    # Render profile page with user data
    return render_template('profile.html', userinfo=userinfo)

@app.route('/prof')
def prof():
      # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Get user data from session
    userinfo = session['user']

    # Render profile page with user data
    return render_template('profile.html', userinfo=userinfo)

@app.route('/update_account', methods=['POST'])
def update_account():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Retrieve the user's session information
    userinfo = session['user']
    user_id = userinfo['id']  # Assuming 'id' is stored in session

    # Get updated info from form submission
    name = request.form.get('name')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    address = request.form.get('physical_address')  # Fixed key name to match the HTML
    gender = request.form.get('gender')  # Get the selected gender

    # Ensure all fields are provided
    if not all([name, email, phone_number, address, gender]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('profile'))

    # Get the database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # SQL update query
        sql = """
            UPDATE userinfo
            SET Name = %s, Email = %s, PhoneNumber = %s, PhysicalAddress = %s, Gender = %s
            WHERE ID = %s
        """
        values = (name, email, phone_number, address, gender, user_id)

        # Execute the UPDATE query
        cursor.execute(sql, values)
        conn.commit()

        # Check if the update was successful
        if cursor.rowcount > 0:
            flash('Profile updated successfully!', 'success')
            # Update session data
            session['user']['name'] = name
            session['user']['email'] = email
            session['user']['phone_number'] = phone_number
            session['user']['physical_address'] = address
            session['user']['gender'] = gender  # Update gender in session
            session.modified = True  # Mark the session as modified
        else:
            flash('No changes were made to your profile.', 'info')

    except Exception as e:
        flash('An error occurred while updating your profile. Please try again later.', 'danger')
        print(f"Error executing query: {e}")
        conn.rollback()

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

    # Redirect back to the profile page
    return redirect(url_for('profile'))


@app.route('/update_password_plain', methods=['POST'])
def update_password_plain():
    if 'user_id' not in session:  # Ensure user is logged in
        flash('You need to log in to change your password.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch the current password from the database
        cursor.execute("SELECT Password FROM userinfo WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        # Check if user exists
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('profile'))

        # Verify the current password directly (no hashing)
        if user['Password'] != current_password:
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('profile'))

        # Ensure the new password matches the confirmation
        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('profile'))

        # Update the password in the database without hashing
        cursor.execute("UPDATE userinfo SET Password = %s WHERE id = %s", (new_password, user_id))
        conn.commit()  # Ensure the changes are saved to the database

        flash('Password updated successfully (no hashing used).', 'success')
        return redirect(url_for('profile'))

    except mysql.connector.Error as e:
        print(f"Database Error: {e}")
        flash('A database error occurred. Please try again.', 'danger')
        return redirect(url_for('profile'))
    except Exception as e:
        print(f"Error updating password: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('profile'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



#Profile End


@app.route('/verify_otp', methods=['GET', 'POST'])
def send_mail():
    if request.method == 'POST':
        email = request.form['email']
        subject = "Your OTP Code"
        
        # Generate a random 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))  # 6-digit OTP
        
        message_body = f"Your OTP code is: {otp}"  # OTP message content

        msg = Message(subject, sender='togtogdausin@gmail.com', recipients=[email])
        msg.body = message_body  # Plain text message
        msg.html = f"<p>{message_body}</p>"  # HTML version of the message

        try:
            mail.send(msg)
            flash('OTP sent successfully!', 'success')
            # Store the OTP in the session to verify later
            session['otp_code'] = otp
            session['otp_email'] = email
        except Exception as e:
            flash(f'Failed to send OTP. Error: {str(e)}', 'danger')
            return redirect(url_for('send_mail'))

        return redirect(url_for('verify_otp_code'))  # Redirect to OTP verification page after sending OTP

    return render_template('verify_otp.html')

@app.route('/verify_otp_code', methods=['POST', 'GET'])
def verify_otp_code():
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        # Retrieve the OTP stored in session
        otp_code = session.get('otp_code')
        
        # Check if the OTP entered by the user matches the one in the session
        if otp == otp_code:
            flash("OTP verified successfully!", "success")
            # Redirect to the next URL after OTP verification
            next_url = session.pop('next_url', url_for('homepage'))
            return redirect(next_url)
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('verify_otp_code'))  # Redirect back to OTP form for re-entry

    return render_template('verify_otp_code.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You need to log in to change your password.'})

    user_id = session['user_id']
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New password and confirm password do not match.'})

    try:
        # Connect to the database to fetch user email
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT Email, Password FROM userinfo WHERE ID = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found.'})

        # Verify current password
        if user['Password'] != current_password:
            return jsonify({'success': False, 'message': 'Current password is incorrect.'})

        user_email = user['Email']
        otp = ''.join(random.choices(string.digits, k=6))  # Generate a 6-digit OTP

        # Save OTP and user-provided data in session
        session['otp_code'] = otp
        session['current_password'] = current_password
        session['new_password'] = new_password

        # Send OTP to the user's email
        msg = Message("Your OTP Code", sender='mediaverse888@gmail.com', recipients=[user_email])
        msg.body = f"Your OTP code is: {otp}"
        mail.send(msg)

        return jsonify({'success': True, 'message': 'OTP sent successfully to your email.'})
    
    except mysql.connector.Error as db_error:
        return jsonify({'success': False, 'message': f'Database error: {str(db_error)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




@app.route('/verify_otp_and_update_password', methods=['POST'])
def verify_otp_and_update_password():
    if 'user_id' not in session:
        flash('You need to log in to change your password.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    otp_input = request.form.get('otp')

    # Verify OTP
    if otp_input != session.get('otp_code'):
        flash('Invalid OTP. Please try again.', 'danger')
        return redirect(url_for('profile'))

    # Retrieve password data from session
    current_password = session.get('current_password')
    new_password = session.get('new_password')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify current password from database
        cursor.execute("SELECT Password FROM userinfo WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user or user['Password'] != current_password:
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('profile'))

        # Update password in the database
        cursor.execute("UPDATE userinfo SET Password = %s WHERE id = %s", (new_password, user_id))
        conn.commit()

        flash('Password updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('profile'))





#OTP End

#ADD PRODUCT START

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user' not in session or session['user']['role'] != 'Seller':
        return redirect(url_for('login_page'))

    # Ensure the user email exists in the session
    if 'email' not in session['user']:
        return jsonify({"error": "User email not found in session."}), 400

    # Retrieve the form data
    product_name = request.form.get('product_name')
    category = request.form.get('category')
    mini_description = request.form.get('mini_description')
    main_description = request.form.get('main_description')
    price = request.form.get('price')
    stock_quantity = request.form.get('stock_quantity')
    product_image = request.files.get('product_image')
    sub_image_1 = request.files.get('sub_image_1')
    sub_image_2 = request.files.get('sub_image_2')
    sub_image_3 = request.files.get('sub_image_3')
    business_name = request.form.get('business_name')
    seller_id = request.form.get('seller_id')

    # Check for missing fields
    if not all([product_name, category, mini_description, main_description, price, stock_quantity, product_image]):
        return jsonify({"error": "One or more fields are missing."}), 400

    # Ensure the images are properly saved
    image_directory = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(image_directory, exist_ok=True)

    image_filename = None
    if product_image and product_image.filename != '':
        # Create a unique filename and save the image
        image_filename = str(uuid.uuid4()) + os.path.splitext(product_image.filename)[1]
        image_path = os.path.join(image_directory, image_filename)
        product_image.save(image_path)

    # Handle sub-images (if provided)
    sub_image_filenames = []
    for sub_image in [sub_image_1, sub_image_2, sub_image_3]:
        sub_image_filename = None
        if sub_image and sub_image.filename != '':
            sub_image_filename = str(uuid.uuid4()) + os.path.splitext(sub_image.filename)[1]
            sub_image_path = os.path.join(image_directory, sub_image_filename)
            sub_image.save(sub_image_path)
        sub_image_filenames.append(sub_image_filename)

    # Insert into the database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO seller_add_product 
        (product_name, category, mini_description, main_description, price, stock_quantity, product_image, sub_image_1, sub_image_2, sub_image_3, seller_id, product_status, business_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            product_name, category, mini_description, main_description, price, stock_quantity,
            image_filename, sub_image_filenames[0], sub_image_filenames[1], sub_image_filenames[2],
            seller_id, 'listed', business_name
        )
        
        cursor.execute(sql, values)
        conn.commit()

        # Redirect to the seller dashboard
        return redirect(url_for('seller_dash'))
    except Error as e:
        print(f"Database error: {e}")  # Debugging output
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#ADD PRODUCT END

#Inventory Start

@app.route('/my_products', methods=['GET', 'POST'])
def my_products():
    seller_id = session.get('seller_id')

    if not seller_id:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '').lower()
    selected_category = request.args.get('selected_category', 'all').lower()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Construct base query for listed products
        query = "SELECT * FROM seller_add_product WHERE seller_id = %s AND product_status = 'listed'"
        params = [seller_id]

        # Add filtering by search query (if provided)
        if search_query:
            query += " AND LOWER(product_name) LIKE %s"
            params.append(f"%{search_query}%")
        
        # Add filtering by category (if provided and not 'all')
        if selected_category != 'all':
            query += " AND LOWER(category) = %s"
            params.append(selected_category)

        # Execute query for listed products
        cursor.execute(query, tuple(params))
        listed_products = cursor.fetchall()

        # Unlisted products (same filtering logic)
        query = "SELECT * FROM seller_unlisted_products WHERE seller_id = %s"
        params = [seller_id]
        
        if search_query:
            query += " AND LOWER(product_name) LIKE %s"
            params.append(f"%{search_query}%")
        
        if selected_category != 'all':
            query += " AND LOWER(category) = %s"
            params.append(selected_category)

        cursor.execute(query, tuple(params))
        unlisted_products = cursor.fetchall()

    except Exception as e:
        flash(f"An error occurred: {e}", 'error')
        listed_products = []
        unlisted_products = []
    finally:
        cursor.close()
        conn.close()

    return render_template('sellerdash.html',
                           listed_products=listed_products,
                           unlisted_products=unlisted_products,
                           search_query=search_query,
                           selected_category=selected_category,
                           active_tab='inventory')

# Route to unlist a product
@app.route('/unlist_product/<int:product_id>', methods=['POST'])
def unlist_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the product details from seller_add_product
        cursor.execute("SELECT * FROM seller_add_product WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if product:
            # Insert the product into seller_unlisted_products
            cursor.execute("""
                INSERT INTO seller_unlisted_products (
                    id, product_name, category, mini_description, main_description, price, stock_quantity, 
                    product_image, sub_image_1, sub_image_2, sub_image_3, seller_id, product_status, business_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product[0], product[1], product[2], product[3], product[4], product[5], product[6],
                product[7], product[8], product[9], product[10], session['seller_id'], 'unlisted', product[13]
            ))

            # Delete the product from seller_add_product
            cursor.execute("DELETE FROM seller_add_product WHERE id = %s", (product_id,))
            conn.commit()

            flash('Product unlisted successfully!', 'success')
        else:
            flash('Product not found!', 'error')
    except Exception as e:
        flash(f'Error unlisting product: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('my_products'))


@app.route('/move_back_to_listed/<int:product_id>', methods=['POST'])
def move_back_to_listed(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    seller_id = session.get('user_id')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, product_name, category, mini_description, main_description, price, stock_quantity, 
                   product_image, sub_image_1, sub_image_2, sub_image_3, seller_id, product_status, business_name 
            FROM seller_unlisted_products 
            WHERE id = %s AND seller_id = %s
        """, (product_id, seller_id))
        product = cursor.fetchone()

        if product:
            # Set product_status explicitly to 'listed'
            listed_product = list(product)
            listed_product[12] = 'listed'  # Assuming index 12 is `product_status`

            cursor.execute("""
                INSERT INTO seller_add_product 
                (id, product_name, category, mini_description, main_description, price, stock_quantity, 
                 product_image, sub_image_1, sub_image_2, sub_image_3, seller_id, product_status, business_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(listed_product))

            cursor.execute("DELETE FROM seller_unlisted_products WHERE id = %s AND seller_id = %s", (product_id, seller_id))
            conn.commit()

            flash('Product successfully moved back to listed products!', 'success')
        else:
            flash('Product not found in unlisted products', 'error')

    conn.close()
    return redirect(url_for('seller_homepage'))


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Delete the product or update the is_deleted flag as needed
        cursor.execute("DELETE FROM seller_unlisted_products WHERE id = %s", (product_id,))
        conn.commit()  # Commit the changes to the database
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash(f"An error occurred while deleting the product: {e}", 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('seller_homepage', active_tab='my-products'))  # Pass active tab here


#FILTERING WHAT YHE CATEGORY OF A PRODUCT
def fetch_products_from_database(category):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = "SELECT * FROM seller_add_product WHERE LOWER(category) = LOWER(%s)"
        print(f"Fetching products for category: {category}")  # Debugging line
        cursor.execute(sql, (category,))
        products = cursor.fetchall()
        print(f"Fetched products for {category}: {products}")  # Debugging line
        return products

    except mysql.connector.Error as err:
        print(f"Error fetching products: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

#Inventory End

#ORDERMANAGEMENT START


@app.route('/orders')
def orders():
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query the database for orders, including phone number and address
        cursor.execute("SELECT id, Name, PhoneNumber, PhysicalAddress, product_name, price, quantity_order, total, payment_method, created_at, status FROM orders")
        orders_data = cursor.fetchall()

        # Get the user's name from session and pass it to the template
        seller_name = session['user']['name'] if 'user' in session else 'Guest'

        # Close connection
        cursor.close()
        conn.close()

        # Pass data to the template and the seller's name
        return render_template('orders.html', orders=orders_data, seller_name=seller_name)

    except mysql.connector.Error as err:
        return f"Database error: {err}"



    
@app.route('/inventory', methods=['GET'])
def inventory():
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch products
        cursor.execute("SELECT id, product_name, category, price, stock_quantity FROM seller_add_product")
        products_data = cursor.fetchall()

        # Close connection
        cursor.close()
        conn.close()

        # Pass data to the template
        return render_template(
            'inventory.html',
            products=products_data,
            seller_name=session['user']['name'] if 'user' in session else 'Guest'
        )

    except mysql.connector.Error as err:
        return f"Database error: {err}"

@app.route('/sellerdash', methods=['GET'])
def seller_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Make sure you're passing the name
    return render_template('sellerdash.html', 
                        name=session['user'].get('name', 'Seller'))
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get seller ID from session
        seller_id = session['user']['id'] if 'user' in session else None
        if not seller_id:
            return redirect(url_for('login'))  # Redirect to login if not authorized

        # Get date range from request args
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Initialize values
        total_sales = 0
        total_income = 0

        # Debugging: Print seller_id and date filters
        print(f"Seller ID: {seller_id}")
        print(f"Start Date: {start_date}, End Date: {end_date}")

        # Query to calculate total sales and total income
        query = """
            SELECT 
                SUM(total) AS total_sales,
                SUM(price * quantity_order) AS total_income
            FROM orders
            WHERE seller_id = %s AND status IN ('Shipped Out', 'Completed')
        """
        params = (seller_id,)

        if start_date and end_date:
            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params += (start_date, end_date)

        # Debugging: Print final query and params
        print("Final Query:", query)
        print("Parameters:", params)

        # Execute the query
        cursor.execute(query, params)
        result = cursor.fetchone()

        # Handle results
        if result:
            total_sales = result['total_sales'] if result['total_sales'] else 0
            total_income = result['total_income'] if result['total_income'] else 0

        # Debugging: Print the results
        print(f"Total Sales: {total_sales}")
        print(f"Total Income: {total_income}")

        # Close connection
        cursor.close()
        conn.close()

        # Render the dashboard with the data
        return render_template(
            'sellerdash.html',
            total_sales=total_sales,
            total_income=total_income,
            start_date=start_date,
            end_date=end_date,
            seller_name=session['user']['name'] if 'user' in session else 'Guest'
        )

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return f"Database error: {err}"



    
@app.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    try:
        # Get the new quantity from the request
        new_quantity = request.json.get('quantity')

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the product quantity in the database
        cursor.execute("""
            UPDATE seller_add_product
            SET stock_quantity = %s
            WHERE id = %s
        """, (new_quantity, product_id))

        # Commit the transaction and close connection
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Quantity updated successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# eto yung pag naconfim yung order notification

@app.route('/notifications', methods=['GET'])
def notifications():
    """Render notifications page or return JSON notifications."""
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in

    user_id = session['user']['id']  # Get the logged-in user's ID from the session
    format_type = request.args.get('format', 'html')  # Check if 'format' query parameter is present

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch notifications for the logged-in user, joining with products and sellers
        query = """
            SELECT n.id, n.product_id, n.message, n.created_at, p.product_name, 
                   p.product_image, s.seller_name 
            FROM notifications n
            JOIN seller_add_product p ON n.product_id = p.id
            JOIN userinfo s ON p.role = s.id
            WHERE n.user_id = %s AND (n.message LIKE 'confirmed%' OR n.message LIKE 'to ship%' OR n.message LIKE 'canceled%')
            ORDER BY n.created_at DESC
        """
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()

        cursor.close()
        conn.close()

        # Ensure default product image if not present
        for notification in notifications:
            if not notification.get('product_image'):
                notification['product_image'] = '/static/default-product.png'

        # Return JSON response if format=json
        if format_type == 'json':
            return jsonify({"notifications": notifications}), 200

        # Otherwise, render the HTML template
        return render_template('notification.html', notifications=notifications)
    except Exception as e:
        print(f"Error fetching notifications: {e}")

        if format_type == 'json':
            return jsonify({"error": "Failed to retrieve notifications."}), 500

        # Render HTML with an empty notification list if an error occurs
        return render_template('notification.html', notifications=[])



def add_notification(user_id, product_name, message):
    """Helper function to add a notification to the database and send an email."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert notification into the database
        query = """
            INSERT INTO notifications (user_id, product_name, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(query, (user_id, product_name, message))
        conn.commit()

        # Fetch the user's email address
        user_query = "SELECT email FROM userinfo WHERE id = %s"
        cursor.execute(user_query, (user_id,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and user.get('email'):
            user_email = user['email']

            # Compose the email
            subject = f"Order Update: {message}"
            body = f"""
            Dear User,

            Your order for the product '{product_name}' has been updated with the following status:
            {message}

            Thank you for shopping with us.

            Best regards,
            Your Company
            """
            send_email(user_email, subject, body)

    except Exception as e:
        print(f"Error adding notification or sending email: {e}")


def send_email(to_email, subject, body):
    """Helper function to send an email."""
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
        msg.body = body
        mail.send(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


# Example route for seller dashboard
@app.route('/sellerdash')
def sellerdash():
    if 'user' not in session or session['user'].get('role') != 'Seller':
        return redirect(url_for('login'))  # Redirect to login page if not logged in or not a seller

    # Retrieve the seller's name and business name from the session
    seller_name = session['user'].get('name')
    business_name = session['user'].get('business_name')

    # Pass the seller's name and business name to the template
    return render_template('sellerdash.html', name=seller_name, business_name=business_name)
    
@app.route('/confirm_order/<int:order_id>', methods=['POST'])
def confirm_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Update order status
        cursor.execute("UPDATE orders SET status = 'Confirmed' WHERE id = %s", (order_id,))

        # Fetch user ID and email associated with the order
        cursor.execute("""
            SELECT o.user_id, u.Email AS email
            FROM orders o
            INNER JOIN userinfo u ON o.user_id = u.ID
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()

        # Debugging: Ensure data is fetched correctly
        print(f"Order Data: {order}")

        if not order:
            return jsonify({"error": "Order not found."}), 404

        # Send notification to the user via email
        user_email = order['email']
        message = f"Dear Customer,\n\nWe are pleased to inform you that your order #{order_id} has been confirmed. We will notify you once your order is shipped.\n\nThank you for choosing us.\n\nBest regards,\nMedia Verse Hub"

        
        # Check email before sending
        print(f"Sending email to: {user_email}")
        
        # Email sending logic
        try:
            msg = Message("Order Confirmation", sender='mediaverse888@gmail.com', recipients=[user_email])
            msg.body = message
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")
            return jsonify({"error": "Failed to send notification email."}), 500

        # Create a notification in the database
        cursor.execute("""
            INSERT INTO notifications (user_id, order_id, message)
            VALUES (%s, %s, %s)
        """, (order['user_id'], order_id, message))

        conn.commit()

        return jsonify({"message": "Order confirmed successfully, and notification sent!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to confirm the order: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Update order status to 'Cancelled'
        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))

        # Fetch user ID and email associated with the order
        cursor.execute("""
            SELECT o.user_id, u.Email AS email
            FROM orders o
            INNER JOIN userinfo u ON o.user_id = u.ID
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({"error": "Order not found."}), 404

        # Prepare and send cancellation notification email
        user_email = order['email']
        message = f"Dear Customer,\n\nWe regret to inform you that your order #{order_id} has been cancelled. If you have any questions or concerns, please feel free to contact us.\n\nThank you for your understanding.\n\nBest regards,\nMedia Verse Hub"


        try:
            msg = Message("Order Cancellation", sender='mediaverse888@gmail.com', recipients=[user_email])
            msg.body = message
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")
            return jsonify({"error": "Failed to send notification email."}), 500

        # Add notification in the database
        cursor.execute("""
            INSERT INTO notifications (user_id, order_id, message)
            VALUES (%s, %s, %s)
        """, (order['user_id'], order_id, message))

        conn.commit()

        return jsonify({"message": "Order cancelled successfully, and notification sent!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to cancel the order: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/ship_order/<int:order_id>', methods=['POST'])
def ship_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get the order details and verify stock
        cursor.execute("""
            SELECT o.id, o.user_id, o.product_id, o.quantity_order, o.status, 
                   p.stock_quantity, u.Email AS email, o.Name as buyer_name, 
                   o.PhysicalAddress as delivery_location, o.seller_id,
                   s.Name as seller_name, s.PhysicalAddress as pickup_location
            FROM orders o
            LEFT JOIN seller_add_product p ON o.product_id = p.id
            INNER JOIN userinfo u ON o.user_id = u.ID
            INNER JOIN userinfo s ON o.seller_id = s.ID
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({"error": "Order not found."}), 404

        # Check stock availability
        if order['quantity_order'] > order['stock_quantity']:
            return jsonify({"error": "Insufficient stock."}), 400

        # Deduct the stock and update the order status to 'Shipped Out'
        new_stock_quantity = order['stock_quantity'] - order['quantity_order']
        cursor.execute("UPDATE seller_add_product SET stock_quantity = %s WHERE id = %s", (new_stock_quantity, order['product_id']))
        cursor.execute("UPDATE orders SET status = 'Shipped Out' WHERE id = %s", (order_id,))

        # Add entry to delivery table
        cursor.execute("""
            INSERT INTO delivery 
            (order_id, seller_id, seller_name, buyer_id, buyer_name, 
             pickup_location, delivery_location, delivery_fee) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id,
            order['seller_id'],
            order['seller_name'],
            order['user_id'],
            order['buyer_name'],
            order['pickup_location'],
            order['delivery_location'],
            50.00  # Default delivery fee
        ))

        # Prepare and send shipping notification email
        user_email = order['email']
        message = f"Dear Customer,\n\nWe are pleased to inform you that your order #{order_id} has been successfully shipped out. Thank you for shopping with us.\n\nShould you have any further questions or require assistance, please do not hesitate to contact us.\n\nBest regards,\nMedia Verse Hub"

        try:
            msg = Message("Order Shipped", sender='mediaverse888@gmail.com', recipients=[user_email])
            msg.body = message
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")
            return jsonify({"error": "Failed to send notification email."}), 500

        # Add notification in the database
        cursor.execute("""
            INSERT INTO notifications (user_id, order_id, message)
            VALUES (%s, %s, %s)
        """, (order['user_id'], order_id, message))

        conn.commit()

        return jsonify({"message": "Order marked as shipped, and notification sent!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to ship the order: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/notifications', methods=['GET'])
def get_notification():
    if 'user_id' not in session:
        return jsonify({"error": "You need to log in to view notifications."}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch unread notifications for the user
        cursor.execute("""
            SELECT id, order_id, message, status, created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        notifications = cursor.fetchall()

        return jsonify({"notifications": notifications}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch notifications: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

    

@app.route('/request-cancel-order', methods=['POST'])
def request_cancel_order():
    data = request.get_json()
    order_id = data.get('order_id')
    cancel_reason = data.get('cancel_reason')

    if not order_id or not cancel_reason:
        return jsonify({"message": "Order ID and cancellation reason are required!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update order status and store the cancellation reason
        update_query = """
            UPDATE orders 
            SET status = 'Cancelled', cancel_reason = %s 
            WHERE id = %s
        """
        cursor.execute(update_query, (cancel_reason, order_id))
        conn.commit()

        # Fetch order details for the notification
        order_details_query = """
            SELECT user_id, seller_id, product_name, product_image 
            FROM orders 
            WHERE id = %s
        """
        cursor.execute(order_details_query, (order_id,))
        order_details = cursor.fetchone()

        if not order_details:
            return jsonify({"message": "Order not found."}), 404

        user_id, seller_id, product_name, product_image = order_details

        # Add a notification to the notifications table
        notification_query = """
            INSERT INTO notifications (user_id, seller_id, order_id, product_name, product_image, message, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        message = f"Your order {order_id} has been cancelled. Reason: {cancel_reason}"
        cursor.execute(
            notification_query, 
            (user_id, seller_id, order_id, product_name, product_image, message)
        )
        conn.commit()

        return jsonify({"message": "Order successfully cancelled!"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")  # Log the error for debugging
        return jsonify({"message": "Error cancelling the order. Please try again later."}), 500

    finally:
        cursor.close()
        conn.close()

#ORDERMANAGEMENT END

@app.route('/shop')
def shop():
    conn = None
    cursor = None
    category = request.args.get('category')  # Capture the category from the URL query string
    search_query = request.args.get('search')  # Capture the search query from the URL query string

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get distinct categories for the filter dropdown
        cursor.execute("SELECT DISTINCT category FROM seller_add_product")
        categories = cursor.fetchall()

        # Base SQL query for fetching products
        sql = "SELECT id, product_name, category, mini_description, main_description, price, product_image, sub_image_1, sub_image_2, sub_image_3, business_name FROM seller_add_product"
        params = []

        # Modify query to filter products by category and/or search term
        conditions = []
        if category:
            print(f"Filtering by category: {category}")  # Debugging output
            conditions.append("category = %s")
            params.append(category)
        if search_query:
            print(f"Filtering by search term: {search_query}")  # Debugging output
            conditions.append("product_name LIKE %s")
            params.append(f"%{search_query}%")
        
        # Add conditions to SQL if there are any
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        print(f"SQL query: {sql} with params: {params}")  # Debugging output
        cursor.execute(sql, tuple(params))
        products = cursor.fetchall()

        print(f"Products found: {products}")  # Debugging output

        # Pass products, categories, selected category, and search query to the template
        return render_template(
            'shopping.html',
            products=products,
            categories=categories,
            selected_category=category,
            search_query=search_query
        )

    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Updated query to include stock_quantity
        sql = """
        SELECT id, product_name, category, mini_description, main_description, 
               price, product_image, sub_image_1, sub_image_2, sub_image_3, 
               stock_quantity, business_name
        FROM seller_add_product 
        WHERE id = %s
        """
        cursor.execute(sql, (product_id,))
        product = cursor.fetchone()

        if product:
            # Pass the product details to the template
            return render_template('product_detail.html', product=product)
        else:
            return "Product not found", 404

    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/delete_cart_item', methods=['POST'])
def delete_cart_item():
    item_id = request.json.get('item_id')  # Get item ID from request
    user_id = session.get('user', {}).get('id')  # Get the user ID from session

    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Delete the item from the cart
        cursor.execute("DELETE FROM carts WHERE id = %s AND user_id = %s", (item_id, user_id))
        connection.commit()  # Commit the transaction
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting cart item: {e}")
        return jsonify({"error": "Failed to delete item"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        return jsonify({"error": "User must be logged in to add items to the cart."}), 401

    user_id = session['user']['id']
    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({"error": "Product ID is required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch product details including seller_id from the database
        cursor.execute(
            "SELECT id, product_name, price, product_image, business_name, seller_id FROM seller_add_product WHERE id = %s",
            (product_id,)
        )
        product_details = cursor.fetchone()
        
        if not product_details:
            return jsonify({"error": "Product not found."}), 404

        product_id, product_name, price, image_path, business_name, seller_id = product_details

        # Check if the product already exists in the user's cart
        cursor.execute(
            "SELECT quantity FROM carts WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        result = cursor.fetchone()

        if result:
            # If the product already exists, update the quantity
            new_quantity = result[0] + 1
            cursor.execute(
                """
                UPDATE carts 
                SET quantity = %s 
                WHERE user_id = %s AND product_id = %s
                """,
                (new_quantity, user_id, product_id)
            )
        else:
            # If the product doesn't exist, insert it into the cart
            cursor.execute(
                """
                INSERT INTO carts (user_id, seller_id, product_id, product_name, price, image_path, business_name, quantity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, seller_id, product_id, product_name, price, image_path, business_name, 1)
            )

        # Commit the transaction
        conn.commit()

        # Now, retrieve the updated cart and save it to the session
        cursor.execute(
            "SELECT product_id, product_name, price, quantity, seller_id FROM carts WHERE user_id = %s",
            (user_id,)
        )
        cart_items = cursor.fetchall()

        # Store the updated cart in the session
        session['cart'] = [{
            'product_id': item[0],
            'product_name': item[1],
            'price': item[2],
            'quantity': item[3],
            'total': item[2] * item[3],
            'seller_id': item[4]
        } for item in cart_items]

        return jsonify({"success": True, "message": "Product added to cart successfully!"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to add product to cart."}), 500

    finally:
        cursor.close()
        conn.close()




@app.route('/cart')
def cart():
    # Debugging: Check if user_id is in session
    if 'user_id' not in session:
        print("User not logged in, redirecting to login page.")
        return redirect(url_for('login'))

    # Check and print user_id from session
    user_id = session['user_id']
    print(f"User ID in session: {user_id}")

    # Connect to database and fetch cart items
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Fetch cart items for the user - now including seller_id
        # Original query that might be causing problems
        # cursor.execute("""
        # SELECT c.id, s.product_name, s.price, c.quantity, s.product_image, s.business_name, s.seller_id
        # FROM carts c
        # JOIN seller_add_product s ON c.product_id = s.id
        # WHERE c.user_id = %s
        # """, (user_id,))
        
        # Let's use the original query structure to avoid compatibility issues
        cursor.execute("""
        SELECT c.id, s.product_name, s.price, c.quantity, s.product_image, s.business_name
        FROM carts c
        JOIN seller_add_product s ON c.product_id = s.id
        WHERE c.user_id = %s
        """, (user_id,))

        # Retrieve results
        cart_items = cursor.fetchall()
        print("Cart items:", cart_items)  # Debug output to confirm data fetched

        # Check if cart_items is empty
        if not cart_items:
            print("No items found in cart.")
        
        # Now get seller_id separately for each product to avoid schema issues
        updated_cart_items = []
        for item in cart_items:
            # Get the product ID from the cart
            cursor.execute("""
            SELECT product_id FROM carts WHERE id = %s
            """, (item[0],))
            product_id_result = cursor.fetchone()
            
            if product_id_result:
                product_id = product_id_result[0]
                
                # Get the seller_id for this product
                cursor.execute("""
                SELECT seller_id FROM seller_add_product WHERE id = %s
                """, (product_id,))
                seller_id_result = cursor.fetchone()
                seller_id = seller_id_result[0] if seller_id_result else None
                
                # Store all the item info including seller_id
                updated_cart_items.append({
                    'id': item[0],
                    'product_name': item[1],
                    'price': item[2],
                    'quantity': item[3],
                    'product_image': item[4],
                    'business_name': item[5],
                    'seller_id': seller_id
                })
        
        # Ensure the session cart is updated with seller_ids
        session_cart = []
        for item in updated_cart_items:
            session_cart.append({
                'product_id': product_id,  # Use the product_id we retrieved
                'product_name': item['product_name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'total': float(item['price']) * int(item['quantity']),
                'seller_id': item['seller_id']
            })
            
        session['cart'] = session_cart
        
        # Render the cart page with items (use the original format for compatibility)
        return render_template('cart.html', cart_items=cart_items)

    except Exception as e:
        # Log the error in more detail
        import traceback
        print(f"Error fetching cart items: {e}")
        print(traceback.format_exc())
        return "An error occurred while loading your cart."

    finally:
        # Always close cursor and connection to avoid leaks
        cursor.close()
        connection.close()




@app.route('/cart/count')
def cart_count():
    user_id = session.get('user_id')

    if user_id is not None:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to count the number of different products in the cart for the user
        cursor.execute('SELECT COUNT(DISTINCT product_id) FROM carts WHERE user_id = %s', (user_id,))
        count_result = cursor.fetchone()

        conn.close()

        total_products_in_cart = count_result[0] if count_result else 0

        return jsonify(count=total_products_in_cart)
    
    return jsonify(count=0)


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form['product_id']  # Get product ID from the form
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        conn.commit()
        return redirect(url_for('cart'))

    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        conn.close()

@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    data = request.get_json()
    item_id = data.get('item_id')  # ID ng item sa cart
    new_quantity = data.get('quantity')  # Bagong quantity na nais i-set

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Hanapin ang product ID at ang stock quantity
        cursor.execute("""
            SELECT s.stock_quantity 
            FROM seller_add_product s
            INNER JOIN carts c ON s.id = c.product_id
            WHERE c.id = %s
        """, (item_id,))
        stock = cursor.fetchone()

        # Kung walang nakuhang stock
        if not stock:
            return jsonify({'success': False, 'message': 'Product not found in the database.'})

        available_stock = stock[0]  # Stock quantity sa database

        # I-validate kung ang bagong quantity ay higit sa available stock
        if new_quantity > available_stock:
            return jsonify({'success': False, 'message': f'Maximum available stock is {available_stock}.'})

        # Kung valid, i-update ang quantity sa cart
        cursor.execute("""
            UPDATE carts
            SET quantity = %s
            WHERE id = %s
        """, (new_quantity, item_id))
        connection.commit()

        return jsonify({'success': True, 'message': 'Quantity updated successfully.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the cart.'})
    finally:
        cursor.close()
        connection.close()

#BUYERS CHECK OUT, PLACE ORDER, ORDERS.


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_info = {}
    if 'user_id' in session:  # Check if the user is logged in
        user_id = session['user_id']
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Fetch user details
                query = """
                SELECT Name, PhoneNumber, PhysicalAddress 
                FROM userinfo 
                WHERE ID = %s
                """
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
                if result:
                    user_info = {
                        'name': result[0],  # Name
                        'phone': result[1],  # PhoneNumber
                        'address': result[2]  # PhysicalAddress
                    }
        except Exception as e:
            print(f"Error fetching user info: {e}")
        finally:
            conn.close()

    else:
        print("User is not logged in.")
        return redirect('/login')  # Redirect to login if user not logged in

    if request.method == 'GET':
        # Handle "Buy Now" or default cart-based checkout
        product_id = request.args.get('product_id')
        product_name = request.args.get('product_name')
        price = request.args.get('price')
        quantity = request.args.get('quantity', 1)
        seller_id = request.args.get('seller_id')  # Added seller_id parameter

        if product_id and product_name and price:
            # If seller_id wasn't provided, try to fetch it from the database
            if not seller_id:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        query = "SELECT seller_id FROM seller_add_product WHERE id = %s"
                        cursor.execute(query, (product_id,))
                        result = cursor.fetchone()
                        if result:
                            seller_id = result[0]
                    conn.close()
                except Exception as e:
                    print(f"Error fetching seller_id: {e}")

            # Temporary cart for "Buy Now" scenario
            temp_cart = [{
                'product_id': product_id,
                'product_name': product_name,
                'price': float(price),
                'quantity': int(quantity),
                'total': float(price) * int(quantity),
                'seller_id': seller_id  # Add seller_id to temp_cart
            }]
            session['temp_cart'] = temp_cart

            subtotal = sum(item['total'] for item in temp_cart)
            shipping_fee = 50.0  # Example shipping fee
            total = subtotal + shipping_fee

            return render_template(
                'checkout.html',
                cart_items=temp_cart,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total=total,
                user_info=user_info  # Pass user info to the template
            )

        # Default behavior for cart checkout
        cart_items = session.get('cart', [])
        if not cart_items:
            return jsonify({"error": "Cart is empty."}), 400

        # Calculate totals
        subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
        shipping_fee = 50.0
        total = subtotal + shipping_fee

        # Ensure seller_id is present in all cart items
        for item in cart_items:
            if 'seller_id' not in item or not item['seller_id']:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        query = "SELECT seller_id FROM seller_add_product WHERE id = %s"
                        cursor.execute(query, (item['product_id'],))
                        result = cursor.fetchone()
                        if result:
                            item['seller_id'] = result[0]
                    conn.close()
                except Exception as e:
                    print(f"Error fetching seller_id: {e}")

        return render_template(
            'checkout.html',
            cart_items=cart_items,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total=total,
            user_info=user_info
        )

    # Handle POST for other operations
    if request.method == 'POST':
        selected_items = request.json.get('selected_items', [])
        if selected_items:
            # Ensure selected_items have seller_id
            for item in selected_items:
                if 'seller_id' not in item or not item['seller_id']:
                    try:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            query = "SELECT seller_id FROM seller_add_product WHERE id = %s"
                            cursor.execute(query, (item['product_id'],))
                            result = cursor.fetchone()
                            if result:
                                item['seller_id'] = result[0]
                        conn.close()
                    except Exception as e:
                        print(f"Error fetching seller_id: {e}")
            
            session['cart'] = selected_items

        cart_items = session.get('cart', [])
        if not cart_items:
            return jsonify({"error": "Cart is empty."}), 400

        subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
        shipping_fee = 50.0
        total = subtotal + shipping_fee

        return render_template(
            'checkout.html',
            cart_items=cart_items,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total=total,
            user_info=user_info
        )



@app.route('/place-order', methods=['POST'])
def place_order():
    try:
        # Start with basic debugging
        print("==== STARTING PLACE ORDER FUNCTION ====")
        
        user_id = session.get('user_id')
        print(f"User ID from session: {user_id}")
        
        if not user_id:
            print("No user ID found in session, redirecting to login")
            return redirect(url_for('login'))

        # Get payment method from form data
        payment_method = request.form.get('payment_method')
        print(f"Payment method received: {payment_method}")
        
        # Get cart items (either from temp_cart or regular cart)
        cart_items = session.pop('temp_cart', None)
        if not cart_items:
            cart_items = session.get('cart', [])
        
        print(f"Number of items in cart: {len(cart_items)}")
        # Print first item for debugging (if exists)
        if cart_items and len(cart_items) > 0:
            print(f"First cart item: {cart_items[0]}")
        
        if not cart_items:
            print("No items in cart")
            return jsonify({"error": "No items to place an order."}), 400

        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user shipping details
        print("Fetching user shipping details...")
        name = None
        phone_number = None
        physical_address = None
        
        try:
            cursor.execute(
                "SELECT Name, PhoneNumber, PhysicalAddress FROM userinfo WHERE ID = %s",
                (user_id,)
            )
            user_result = cursor.fetchone()
            
            if user_result:
                name = user_result[0]
                phone_number = user_result[1]
                physical_address = user_result[2]
                print(f"Found user details: {name}, {phone_number}")
            else:
                print(f"No user details found for user_id {user_id}")
                return jsonify({"error": "User details not found"}), 400
                
        except Exception as e:
            print(f"Error fetching user details: {e}")
            return jsonify({"error": "Error fetching user details"}), 500
        
        # Process each cart item
        orders_inserted = 0
        
        for item in cart_items:
            print(f"\n--- Processing cart item ---")
            print(f"Cart item: {item}")
            
            # Extract product_id safely
            try:
                product_id = item.get('product_id')
                if not product_id:
                    print("Missing product_id in cart item, skipping")
                    continue
                    
                print(f"Processing product_id: {product_id}")
            except Exception as e:
                print(f"Error getting product_id: {e}")
                continue
            
            # --- SELLER ID LOOKUP ---
            # Always get seller_id from database for reliability
            seller_id = None
            try:
                print(f"Fetching seller_id for product {product_id}")
                cursor.execute(
                    "SELECT seller_id FROM seller_add_product WHERE id = %s",
                    (product_id,)
                )
                seller_result = cursor.fetchone()
                
                if seller_result and seller_result[0] is not None:
                    seller_id = int(seller_result[0])
                    print(f"Found seller_id in database: {seller_id}")
                else:
                    # If still not found, use a default (but log a warning)
                    seller_id = 81
                    print(f"WARNING: No seller_id found for product {product_id}, using default 81")
            except Exception as e:
                print(f"Error fetching seller_id: {e}")
                seller_id = 81  # Default if error
            
            # --- PRODUCT DATA GATHERING ---
            # Get other required data
            try:
                product_name = item.get('product_name', 'Unknown Product')
                # Safely convert price and quantity
                price = float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                total = float(item.get('total', price * quantity))
                
                print(f"Product data: {product_name}, ${price}, qty:{quantity}, total:${total}")
            except Exception as e:
                print(f"Error processing product data: {e}")
                price = 0
                quantity = 1
                total = 0
                product_name = "Unknown Product"
            
            # --- DATABASE INSERTION ---
            try:
                print("Preparing to insert order into database...")
                print(f"Seller ID being inserted: {seller_id}")
                
                # Simpler SQL query to minimize issues
                sql = """
                INSERT INTO orders (
                    user_id, product_id, Name, PhoneNumber, PhysicalAddress,
                    product_name, price, quantity_order, total, payment_method, status, seller_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    user_id,
                    product_id,
                    name,
                    phone_number,
                    physical_address,
                    product_name,
                    price,
                    quantity,
                    total,
                    payment_method,
                    'Pending',
                    seller_id
                )
                
                print(f"SQL values: {values}")
                cursor.execute(sql, values)
                print("Order inserted successfully!")
                orders_inserted += 1
                
            except Exception as e:
                import traceback
                print(f"Error inserting order into database: {e}")
                print(traceback.format_exc())
                continue  # Try next item
        
        # Check if any orders were inserted successfully
        if orders_inserted > 0:
            print(f"Committing {orders_inserted} orders to database")
            conn.commit()
            session.pop('cart', None)  # Clear cart
            print("Cart cleared, redirecting to homepage")
            return redirect(url_for('homepage'))
        else:
            print("No orders were inserted successfully")
            return jsonify({"error": "Failed to place any orders."}), 500
            
    except Exception as e:
        import traceback
        print(f"Critical error in place_order: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        
    finally:
        # Make sure connections are always closed
        try:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
            print("Database connections closed")
        except Exception as e:
            print(f"Error closing database connections: {e}")


@app.route('/purchases')
def purchases():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Get user_id from session (assuming user is logged in)

    # Fetch orders from the database for the logged-in user
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE user_id = %s", (user_id,))
    orders = cursor.fetchall()  # Retrieve all orders for the user
    conn.close()

    # Pass orders to the HTML template
    return render_template('purchase.html', orders=orders)

def get_userinfo(user_id):
    # Assuming you have a function to connect to the database (like get_db_connection)
    try:
        conn = get_db_connection()  # Replace with actual DB connection function
        cursor = conn.cursor()
        cursor.execute("SELECT Name, PhoneNumber, PhysicalAddress, Business_name FROM userinfo WHERE id = %s", (user_id,))
        userinfo = cursor.fetchone()  # Fetch the first matching record
        conn.close()
        return userinfo
    except Exception as e:
        print("Database connection error:", e)
        return None  # Return None if there is an error



@app.route('/my_purchases', methods=['GET'])
def my_purchases():
    user_id = session.get('user_id')

    if not user_id:
        flash("You need to be logged in to view your purchases", "danger")
        return redirect(url_for('login'))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch orders for the logged-in user
        sql = "SELECT product_name, description, total, status, quantity_order, payment_method FROM orders WHERE user_id = %s"
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()

        # Convert rows to a list of dictionaries for easy rendering
        orders = []
        for row in rows:
            orders.append({
                "product_name": row[0],
                "description": row[1],
                "total": row[2],
                "status": row[3],
                "quantity_order": row[4],
                "payment_method": row[5]
            })

        return render_template('purchase.html', orders=orders)

    except Exception as e:
    
        return redirect(url_for('homepage'))  # Redirect to homepage or a safe page

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

import logging

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        logging.error(f"No status provided for order {order_id}")
        return jsonify({"error": "Status is required"}), 400

    try:
        logging.info(f"Updating order {order_id} to status: {new_status}")
        
        # Update the order status in the database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE orders
            SET status = %s
            WHERE id = %s
        """, (new_status, order_id))

        conn.commit()

        # Close connection
        cursor.close()
        conn.close()

        logging.info(f"Order {order_id} updated successfully.")
        return jsonify({"message": "Status updated successfully!"}), 200

    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {str(err)}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

#FEEDBACK START


# Route to submit feedback
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    
    order_id = data.get('order_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not order_id or not rating:
        return jsonify({"error": "Order ID and rating are required."}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch Name and Email from userinfo table based on the order ID
        cursor.execute("""
            SELECT u.Name, u.Email
            FROM orders o
            INNER JOIN userinfo u ON o.user_id = u.ID
            WHERE o.id = %s
        """, (order_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            return jsonify({"error": "User information not found for this order."}), 404
        
        # Insert feedback into product_feedback table
        cursor.execute("""
            INSERT INTO product_feedback (order_id, Name, Email, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, user_info['Name'], user_info['Email'], rating, comment))
        
        conn.commit()
        
        return jsonify({"message": "Feedback submitted successfully!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while submitting feedback."}), 500
    finally:
        cursor.close()
        conn.close()

# Route to fetch all feedback
@app.route('/get_feedback', methods=['GET'])
def get_feedback():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Fetch rows as dictionaries
        
        cursor.execute("""
            SELECT order_id, Name, Email, rating, comment, created_at
            FROM product_feedback
            ORDER BY created_at DESC
        """)
        
        feedback_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Return JSON response
        return jsonify({"feedback": feedback_data})
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        return jsonify({"error": "An error occurred while fetching feedback."}), 500

# NEW ROUTE: Get average rating for a specific product
@app.route('/get_product_rating/<int:product_id>', methods=['GET'])
def get_product_rating(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get average rating and count for this product
        cursor.execute("""
            SELECT 
                AVG(pf.rating) as average_rating,
                COUNT(pf.id) as review_count
            FROM 
                product_feedback pf
            JOIN 
                orders o ON pf.order_id = o.id
            WHERE 
                o.product_id = %s
        """, (product_id,))
        
        result = cursor.fetchone()
        
        if result and result['average_rating'] is not None:
            rating_data = {
                'rating': float(result['average_rating']),
                'count': result['review_count']
            }
        else:
            rating_data = {
                'rating': 0.0,
                'count': 0
            }
        
        cursor.close()
        conn.close()
        
        return jsonify(rating_data)
    except Exception as e:
        print(f"Error getting product rating: {e}")
        return jsonify({'rating': 0.0, 'count': 0}), 500

# NEW ROUTE: Get recent reviews for a specific product
@app.route('/get_product_reviews/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get the most recent reviews for this product
        cursor.execute("""
            SELECT 
                pf.Name, 
                pf.rating, 
                pf.comment, 
                pf.created_at
            FROM 
                product_feedback pf
            JOIN 
                orders o ON pf.order_id = o.id
            WHERE 
                o.product_id = %s
            ORDER BY 
                pf.created_at DESC
            LIMIT 10
        """, (product_id,))
        
        reviews = cursor.fetchall()
        
        # Format the dates to a readable format
        for review in reviews:
            if 'created_at' in review and review['created_at']:
                review['created_at'] = review['created_at'].strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.close()
        conn.close()
        
        return jsonify({"reviews": reviews})
    except Exception as e:
        print(f"Error getting product reviews: {e}")
        return jsonify({"error": "Failed to fetch reviews"}), 500



#FEEDBACK END


@app.route('/login', methods=['POST'])
def login():
    conn = None
    cursor = None

    try:
        is_mobile = request.is_json  # detect if it's from Flutter
        if is_mobile:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('Email')
            password = request.form.get('Password')

        if not email or not password:
            if is_mobile:
                return jsonify({"status": "error", "message": "Email and password are required"}), 400
            else:
                flash("Email and password are required", "danger")
                return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM userinfo WHERE Email = %s AND Password = %s"
        cursor.execute(sql, (email, password))
        user = cursor.fetchone()

        if user:
            status = user[12]  # <-- Check the correct index of 'Status' column in your DB

            if status != "approved":
                if is_mobile:
                    return jsonify({
                        "status": "error",
                        "message": "Your account is still pending approval."
                    }), 403
                else:
                    flash("Your account is still pending approval.", "warning")
                    return redirect(url_for('login'))

            user_data = {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'role': user[6],
                'business_name': user[7],
                'phone_number': user[8],
                'physical_address': user[9]
            }

            if is_mobile:
                return jsonify({"status": "success", "user": user_data}), 200
            else:
                session['user'] = user_data
                session['user_id'] = user[0]
                session['next_url'] = (
                    url_for('dashboard') if user[6] == 'admin' else
                    url_for('seller_dash') if user[6] == 'Seller' else
                    url_for('courier') if user[6] == 'Courier' else
                    url_for('homepage')
                )
                return redirect(url_for('send_mail'))
        else:
            if is_mobile:
                return jsonify({"status": "error", "message": "Invalid email or password"}), 401
            else:
                flash("Invalid email or password", "danger")
                return redirect(url_for('login'))

    except Exception as e:
        if is_mobile:
            return jsonify({"status": "error", "message": str(e)}), 500
        else:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('login'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




@app.route('/courierdash')
def courier():
    if 'user' in session and session['user']['role'] == 'Courier':
        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Fetch the courier's status from the database
            sql = "SELECT Status, Name, Email, PhoneNumber, PhysicalAddress FROM userinfo WHERE Email = %s"
            cursor.execute(sql, (session['user']['email'],))
            courier_info = cursor.fetchone()
            
            if not courier_info:
                flash('Courier account not found', 'danger')
                return redirect(url_for('login_page'))

            # Check if the courier's status is pending or rejected
            if courier_info['Status'] == 'pending':
                return render_template('pending.html', message="Your account is still pending approval.")
            elif courier_info['Status'] == 'rejected':
                return render_template('rejected.html', message="Your courier application has been rejected.")
                
            # Fetch available orders (Only get orders with status "Confirmed")
            cursor.execute("""
                SELECT o.id, o.Name as customer_name, o.PhoneNumber, o.PhysicalAddress as delivery_location, 
                       u.PhysicalAddress as pickup_location, o.product_name, o.quantity_order as items,
                       ROUND((RAND() * 3) + 2, 1) as distance, 
                       ROUND((RAND() * 100) + 100) as pay_rate
                FROM orders o
                JOIN userinfo u ON o.seller_id = u.ID
                WHERE o.status = 'Confirmed'
                AND o.id NOT IN (SELECT order_id FROM deliveries WHERE order_id IS NOT NULL)
                ORDER BY o.created_at DESC
            """)
            available_orders = cursor.fetchall()
            
            # Count available orders directly from database for accuracy
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM orders o
                WHERE o.status = 'Confirmed'
                AND o.id NOT IN (SELECT order_id FROM deliveries WHERE order_id IS NOT NULL)
            """)
            available_count_result = cursor.fetchone()
            available_count = available_count_result['count'] if available_count_result else 0
            
            # Get courier ID
            cursor.execute("SELECT ID FROM userinfo WHERE Email = %s", (session['user']['email'],))
            courier_id_result = cursor.fetchone()
            courier_id = courier_id_result['ID'] if courier_id_result else None
            
            # Fetch current deliveries for this courier
            if courier_id:
                cursor.execute("""
                    SELECT d.id as delivery_id, d.order_id, o.Name as customer_name, o.PhoneNumber, 
                           o.PhysicalAddress as delivery_location,
                           s.PhysicalAddress as pickup_location, o.product_name, o.quantity_order as items,
                           d.status, d.pickup_time, d.estimated_delivery, d.completed_at, d.payment
                    FROM deliveries d
                    JOIN orders o ON d.order_id = o.id
                    JOIN userinfo s ON o.seller_id = s.ID
                    WHERE d.courier_id = %s
                    ORDER BY d.created_at DESC
                """, (courier_id,))
                
                all_deliveries = cursor.fetchall()
                
                # Separate deliveries by status
                current_deliveries = [d for d in all_deliveries if d['status'] in ('Pending Pickup', 'In Transit')]
                completed_deliveries = [d for d in all_deliveries if d['status'] == 'Delivered']
                
                # Count in-progress deliveries directly from database for accuracy
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM deliveries
                    WHERE courier_id = %s AND status IN ('Pending Pickup', 'In Transit')
                """, (courier_id,))
                in_progress_count_result = cursor.fetchone()
                in_progress_count = in_progress_count_result['count'] if in_progress_count_result else 0
                
                # Count completed deliveries today directly from database
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM deliveries
                    WHERE courier_id = %s 
                    AND status = 'Delivered'
                    AND DATE(completed_at) = %s
                """, (courier_id, today))
                completed_today_result = cursor.fetchone()
                completed_today_count = completed_today_result['count'] if completed_today_result else 0
            else:
                current_deliveries = []
                completed_deliveries = []
                in_progress_count = 0
                completed_today_count = 0
            
            # Get delivery statistics
            total_deliveries = len(completed_deliveries)
            rating = 4.8  # Sample rating - in a real app, this would come from reviews
            on_time_rate = 97  # Sample rate - in a real app, this would be calculated
            total_earnings = sum(d['payment'] for d in completed_deliveries) if completed_deliveries else 0

            # Pass courier information and data to the template
            return render_template(
                'courierdash.html', 
                courier_info=courier_info,
                available_orders=available_orders,
                current_deliveries=current_deliveries,
                completed_deliveries=completed_deliveries,
                available_count=available_count,
                in_progress_count=in_progress_count,
                completed_today_count=completed_today_count,
                total_deliveries=total_deliveries,
                rating=rating,
                on_time_rate=on_time_rate,
                total_earnings=total_earnings
            )
        except Error as e:
            flash(f"Database error: {str(e)}", 'danger')
            return redirect(url_for('login_page'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Redirect to login if not logged in or not a courier
    flash('Please log in as a courier to access this page', 'warning')
    return redirect(url_for('login_page'))

@app.route('/get_confirmed_orders')
def get_confirmed_orders():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Add print statement for debugging
        print("Attempting to fetch confirmed orders")
        
        # Query to fetch all orders with status 'Confirmed'
        # Modified to handle case where userinfo table might not have the expected structure
        cursor.execute("""
            SELECT o.*
            FROM orders o
            WHERE o.status = 'Confirmed'
        """)
        
        orders = cursor.fetchall()
        print(f"Found {len(orders)} confirmed orders")
        
        # Convert decimal values to string for JSON serialization
        for order in orders:
            if 'price' in order and order['price'] is not None:
                order['price'] = str(order['price'])
            if 'total' in order and order['total'] is not None:
                order['total'] = str(order['total'])
        
        return jsonify({"orders": orders}), 200
    
    except Exception as e:
        print(f"Error fetching confirmed orders: {str(e)}")
        return jsonify({"error": f"Failed to fetch orders: {str(e)}"}), 500
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
        
@app.route('/accept_order', methods=['POST'])
def accept_order():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        courier_id = data.get('courier_id')
        
        if not order_id or not courier_id:
            return jsonify({"error": "Order ID and Courier ID are required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if the order exists and is in 'Confirmed' status
        cursor.execute("""
            SELECT o.*, u.Email AS user_email, u.ID AS user_id 
            FROM orders o
            INNER JOIN userinfo u ON o.user_id = u.ID
            WHERE o.id = %s AND o.status = 'Confirmed'
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return jsonify({"error": "Order not found or already assigned"}), 404
        
        # Update order status to 'Shipped Out' - removed the courier_id field
        cursor.execute("""
            UPDATE orders 
            SET status = 'Shipped Out'
            WHERE id = %s AND status = 'Confirmed'
        """, (order_id,))
        
        # Create delivery record
        cursor.execute("""
            INSERT INTO deliveries (order_id, courier_id, status, created_at, payment)
            VALUES (%s, %s, 'Shipped Out', NOW(), 0.00)
        """, (order_id, courier_id))
        
        delivery_id = cursor.lastrowid
        
        # Send email notification to customer
        try:
            user_email = order['user_email']
            message = f"""Dear Customer,

Your order #{order_id} has been shipped and is on its way to you! Your order has been assigned to one of our delivery personnel and will arrive shortly.

Thank you for shopping with Media Verse Hub.

Best regards,
Media Verse Hub"""
            
            msg = Message("Order Shipped", sender='mediaverse888@gmail.com', recipients=[user_email])
            msg.body = message
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        # Create a notification in the database
        cursor.execute("""
            INSERT INTO notifications (user_id, order_id, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (order['user_id'], order_id, "Your order has been shipped and is on its way!"))
        
        conn.commit()
        
        return jsonify({
            "message": "Order accepted successfully! The customer has been notified.",
            "delivery_id": delivery_id
        }), 200
        
    except mysql.connector.Error as db_error:
        print(f"Database error: {db_error}")
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
        
    except Exception as e:
        print(f"General error: {e}")
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"Failed to accept order: {str(e)}"}), 500
        
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

        
@app.route('/get_courier_deliveries/<int:courier_id>')
def get_courier_deliveries(courier_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch all deliveries assigned to this courier
        cursor.execute("""
            SELECT d.id, d.order_id, d.status, d.pickup_time, d.estimated_delivery, d.completed_at,
                   o.product_name, o.Name, o.PhoneNumber, o.PhysicalAddress, o.price, 
                   o.quantity_order, o.total, o.payment_method
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            WHERE d.courier_id = %s AND d.status IN ('Shipped Out', 'In Transit', 'Delivered')
            ORDER BY FIELD(d.status, 'Shipped Out', 'In Transit', 'Delivered'), d.created_at DESC
        """, (courier_id,))

        deliveries = cursor.fetchall()

        # Convert decimal values to string for JSON serialization
        for delivery in deliveries:
            if 'price' in delivery and delivery['price'] is not None:
                delivery['price'] = str(delivery['price'])
            if 'total' in delivery and delivery['total'] is not None:
                delivery['total'] = str(delivery['total'])

        return jsonify({"deliveries": deliveries}), 200

    except Exception as e:
        print(f"Error fetching courier deliveries: {str(e)}")
        return jsonify({"error": f"Failed to fetch deliveries: {str(e)}"}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route('/mark_delivered', methods=['POST'])
def mark_delivered():
    try:
        data = request.get_json()
        delivery_id = data.get('delivery_id')

        if not delivery_id:
            return jsonify({"error": "Delivery ID is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # First, get the order_id and check current status
        cursor.execute("""
            SELECT d.order_id, d.status, o.user_id 
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            WHERE d.id = %s
        """, (delivery_id,))
        
        delivery_info = cursor.fetchone()
        
        if not delivery_info:
            return jsonify({"error": "Delivery not found"}), 404
            
        if delivery_info['status'] == 'Delivered':
            return jsonify({"message": "Delivery is already marked as delivered"}), 200

        # Update delivery status to 'Delivered' and set completed_at timestamp
        cursor.execute("""
            UPDATE deliveries 
            SET status = 'Delivered', completed_at = NOW()
            WHERE id = %s
        """, (delivery_id,))

        # Update order status to 'Completed'
        cursor.execute("""
            UPDATE orders 
            SET status = 'Completed'
            WHERE id = %s
        """, (delivery_info['order_id'],))

        # Get user email for notification
        cursor.execute("""
            SELECT u.Email
            FROM userinfo u
            WHERE u.ID = %s
        """, (delivery_info['user_id'],))
        
        user = cursor.fetchone()
        
        # Send email notification to customer
        if user and 'Email' in user and user['Email']:
            try:
                message = f"""Dear Customer,

Your order #{delivery_info['order_id']} has been delivered! Thank you for shopping with Media Verse Hub.

We hope you enjoy your purchase. Please let us know if you have any questions or concerns.

Best regards,
Media Verse Hub"""

                msg = Message("Order Delivered", sender='mediaverse888@gmail.com', recipients=[user['Email']])
                msg.body = message
                mail.send(msg)
            except Exception as e:
                print(f"Email sending failed: {e}")

        # Create a notification in the database
        cursor.execute("""
            INSERT INTO notifications (user_id, order_id, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (delivery_info['user_id'], delivery_info['order_id'], "Your order has been delivered! Enjoy your purchase."))

        conn.commit()

        return jsonify({
            "message": "Order marked as delivered successfully! The customer has been notified."
        }), 200

    except mysql.connector.Error as db_error:
        print(f"Database error: {db_error}")
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500

    except Exception as e:
        print(f"General error: {e}")
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"Failed to mark as delivered: {str(e)}"}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route('/get_courier_completed_deliveries/<int:courier_id>')
def get_courier_completed_deliveries(courier_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch all completed deliveries for this courier
        cursor.execute("""
            SELECT d.id, d.order_id, d.status, d.pickup_time, d.estimated_delivery, d.completed_at, d.payment,
                   o.product_name, o.Name, o.PhoneNumber, o.PhysicalAddress, o.price, 
                   o.quantity_order, o.total, o.payment_method
            FROM deliveries d
            JOIN orders o ON d.order_id = o.id
            WHERE d.courier_id = %s AND d.status = 'Delivered'
            ORDER BY d.completed_at DESC
        """, (courier_id,))

        deliveries = cursor.fetchall()

        # Count the number of completed deliveries
        completed_count = len(deliveries)

        # Calculate total earnings (₱15 per delivery)
        earning_per_delivery = 15.00
        total_earnings = completed_count * earning_per_delivery

        # Convert decimal values to string for JSON serialization
        for delivery in deliveries:
            if 'price' in delivery and delivery['price'] is not None:
                delivery['price'] = str(delivery['price'])
            if 'total' in delivery and delivery['total'] is not None:
                delivery['total'] = str(delivery['total'])
            if 'payment' in delivery and delivery['payment'] is not None:
                delivery['payment'] = str(delivery['payment'])

        return jsonify({
            "deliveries": deliveries,
            "completed_count": completed_count,
            "total_earnings": str(total_earnings)
        }), 200

    except Exception as e:
        print(f"Error fetching courier completed deliveries: {str(e)}")
        return jsonify({"error": f"Failed to fetch completed deliveries: {str(e)}"}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


@app.route('/seller_dash')
def seller_dash():
    if 'user' in session and session['user']['role'] == 'Seller':
        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch the seller's status from the database
            sql = "SELECT Status FROM userinfo WHERE Email = %s"
            cursor.execute(sql, (session['user']['email'],))
            status = cursor.fetchone()[0]

            # Check if the seller's status is pending
            if status == 'pending':
                return render_template('pending.html', message="Your account is still pending approval.")  # Create a 'pending.html' template

            # Pass seller information and status to the template if approved
            return render_template(
                'sellerdash.html', 
                name=session['user']['name'], 
                email=session['user']['email'],
                business_name=session['user'].get('business_name'),
                phone_number=session['user'].get('phone_number'),
                physical_address=session['user'].get('physical_address'),
                status=status  # Pass status to template
            )
        except Error as e:
            return jsonify({"error": str(e)})
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return redirect(url_for('login_page'))  # Redirect to login if not logged in or not a seller




# ADMIN START

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' in session:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Initialize variables
            total_sales = 0
            commission = 0
            start_date = request.args.get('start_date')  # Get start_date from request args
            end_date = request.args.get('end_date')  # Get end_date from request args

            # Get total users and admins
            cursor.execute("SELECT COUNT(*) FROM userinfo WHERE Role = 'user'")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM userinfo WHERE Role = 'admin'")
            total_admins = cursor.fetchone()[0]

            # Get pending users and sellers
            cursor.execute("SELECT COUNT(*) FROM userinfo WHERE Role = 'user' AND Status = 'pending'")
            pending_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM userinfo WHERE Role = 'Seller' AND Status = 'pending'")
            pending_sellers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM userinfo WHERE Role = 'Courier' AND Status = 'pending'")
            pending_courier = cursor.fetchone()[0]  # Fixed variable name from pending_sellers to pending_courier

            # Query total sales filtered by date range if provided
            if start_date and end_date:
                cursor.execute("""
                    SELECT SUM(total) FROM orders 
                    WHERE status IN ('Confirmed', 'Completed') 
                    AND DATE(created_at) BETWEEN %s AND %s
                """, (start_date, end_date))
            else:
                cursor.execute("""
                    SELECT SUM(total) FROM orders 
                    WHERE status IN ('Confirmed', 'Completed')
                """)

            total_sales = cursor.fetchone()[0]
            total_sales = total_sales if total_sales else 0  # Default to 0 if no sales

            # Calculate 5% commission
            commission = float(total_sales) * 0.05

            # Fetch pending users and sellers list
            cursor.execute("SELECT ID, Name, Email, Role, PhoneNumber, Status FROM userinfo WHERE Role = 'user' AND Status = 'pending'")
            pending_users_list = cursor.fetchall()

            pending_users_data = [
                {"id": user[0], "name": user[1], "email": user[2], "role": user[3], "PhoneNumber": user[4], "Status": user[5]}
                for user in pending_users_list
            ]

            cursor.execute("SELECT ID, Name, Email, Role, PhoneNumber, Status FROM userinfo WHERE Role = 'Seller' AND Status = 'pending'")
            pending_sellers_list = cursor.fetchall()

            pending_sellers_data = [
                {"id": seller[0], "name": seller[1], "email": seller[2], "role": seller[3], "PhoneNumber": seller[4], "Status": seller[5]}
                for seller in pending_sellers_list
            ]

            cursor.execute("SELECT ID, Name, Email, Role, PhoneNumber, Status FROM userinfo WHERE Role = 'Courier' AND Status = 'pending'")
            pending_courier_list = cursor.fetchall()

            pending_courier_data = [
                {"id": courier[0], "name": courier[1], "email": courier[2], "role": courier[3], "PhoneNumber": courier[4], "Status": courier[5]}
                for courier in pending_courier_list
            ]

            # Pass data to template
            return render_template(
                'dashboard.html',
                user=session['user']['name'],
                total_users=total_users,
                total_admins=total_admins,
                total_sales=total_sales,
                commission=round(commission, 2),  # Round to 2 decimal places
                pending_users=pending_users,
                pending_sellers=pending_sellers,
                pending_courier=pending_courier,  # Added this missing variable
                start_date=start_date,  # Pass start_date for filtering
                end_date=end_date,  # Pass end_date for filtering
                pending_users_list=pending_users_data,
                pending_sellers_list=pending_sellers_data,  # Fixed missing comma
                pending_courier_list=pending_courier_data  # Added courier list data
            )
        except Error as e:
            return jsonify({"error": str(e)})
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return redirect(url_for('login_page'))



@app.route('/user_management', methods=['GET'])
def user_management():
    if 'user' in session:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Fetch all approved users
            cursor.execute("SELECT * FROM userinfo WHERE Status != 'rejected'")
            users = cursor.fetchall()

            # Fetch banned users
            cursor.execute("SELECT * FROM banned_users")
            banned_users = cursor.fetchall()

            return render_template('user_management.html', users=users, banned_users=banned_users)
        except Error as e:
            return jsonify({"error": str(e)})
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return redirect(url_for('login_page'))


@app.route('/user_details/<int:seller_id>', methods=['GET'])
def user_details(seller_id):
    if 'user' in session:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Query to fetch user details by ID
            query = "SELECT * FROM userinfo WHERE id = %s"
            cursor.execute(query, (seller_id,))
            user = cursor.fetchone()
            if user:
                return render_template('user_details.html', user=user)
            else:
                return "User not found", 404
        except Error as e:
            return jsonify({"error": str(e)})
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return redirect(url_for('login_page'))


@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    name = request.form['Name']
    email = request.form['Email']
    password = request.form['Password']  # Get the password from the form
    gender = request.form['Gender']
    country = request.form['Country']
    role = request.form['Role']

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if password is provided
        if password:
            # Update all fields, including the password
            sql = """
            UPDATE userinfo
            SET Name = %s, Email = %s, Password = %s, Gender = %s, Country = %s, Role = %s
            WHERE ID = %s
            """
            values = (name, email, password, gender, country, role, user_id)
        else:
            # Update all fields except the password
            sql = """
            UPDATE userinfo
            SET Name = %s, Email = %s, Gender = %s, Country = %s, Role = %s
            WHERE ID = %s
            """
            values = (name, email, gender, country, role, user_id)

        cursor.execute(sql, values)
        conn.commit()

        return redirect(url_for('user_management'))  # Redirect to user management after updating
    except Error as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Delete user
        sql = "DELETE FROM userinfo WHERE ID = %s"
        cursor.execute(sql, (user_id,))
        conn.commit()
        return redirect(url_for('user_management'))  # Redirect to user management after deleting
    except Error as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

from flask_mail import Message

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the user's email and role
        cursor.execute("SELECT Email, Role FROM userinfo WHERE ID = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        email, role = user

        # Approve the user
        sql = "UPDATE userinfo SET Status = 'approved' WHERE ID = %s"
        cursor.execute(sql, (user_id,))
        conn.commit()

        # Send approval email
        subject = f"{role} Application Approved"
        body = f"Congratulations! Your {role.lower()} application has been approved. You can now use our platform."

        msg = Message(subject, sender='togtogdausin@gmail.com', recipients=[email])
        msg.body = body
        mail.send(msg)

        return redirect(url_for('dashboard'))
    except Error as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/reject_user/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the user's email and role
        cursor.execute("SELECT Email, Role FROM userinfo WHERE ID = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        email, role = user

        # Reject the user
        sql = "UPDATE userinfo SET Status = 'rejected' WHERE ID = %s"
        cursor.execute(sql, (user_id,))
        conn.commit()

        # Send rejection email
        subject = f"{role} Application Rejected"
        body = (
            f"We regret to inform you that your {role.lower()} application has been rejected. "
            "Please contact our support team for further assistance."
        )

        msg = Message(subject, sender='togtogdausin@gmail.com', recipients=[email])
        msg.body = body
        mail.send(msg)

        return redirect(url_for('dashboard'))
    except Error as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@app.route('/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user details
        cursor.execute("SELECT ID, Name, Email, Role FROM userinfo WHERE ID = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id, name, email, role = user
        reason = request.form.get('reason')
        banned_by = 'vandawg'  # Replace with actual admin username if available

        # Update user status to banned
        cursor.execute("UPDATE userinfo SET Status = 'banned' WHERE ID = %s", (user_id,))

        # Insert into banned_users table
        cursor.execute(
            "INSERT INTO banned_users (user_id, name, email, role, reason, banned_by) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, name, email, role, reason, banned_by)
        )
        conn.commit()

        # Send email notification
        subject = "Your Account Has Been Banned"
        body = f"Dear {name},\n\nYour account has been banned for the following reason:\n\n{reason}\n\nContact support for further details."
        msg = Message(subject, sender='togtogdausin@gmail.com', recipients=[email])
        msg.body = body
        mail.send(msg)

        return redirect(url_for('user_management'))
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the banned user's details from banned_users table
        cursor.execute("SELECT * FROM banned_users WHERE user_id = %s", (user_id,))
        banned_user = cursor.fetchone()

        if not banned_user:
            return jsonify({"error": "User not found in banned list"}), 404

        # Remove from banned_users table
        cursor.execute("DELETE FROM banned_users WHERE user_id = %s", (user_id,))

        # Update user status to 'approved' in userinfo table
        cursor.execute("UPDATE userinfo SET Status = 'approved' WHERE ID = %s", (user_id,))

        # Commit the changes
        conn.commit()

        # Send email notification
        subject = "Your Account Has Been Unbanned"
        body = f"Dear {banned_user[2]},\n\nYour account has been unbanned and is now active again.\n\nThank you."
        msg = Message(subject, sender='togtogdausin@gmail.com', recipients=[banned_user[3]])
        msg.body = body
        mail.send(msg)

        # Redirect to the user management page to refresh the user list
        return redirect(url_for('user_management'))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ADMIN END

#API Start

@app.route('/api/login', methods=['POST'])
def mobile_login():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"status": "error", "message": "Email and password are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM userinfo WHERE Email = %s AND Password = %s"
        cursor.execute(sql, (email, password))
        user = cursor.fetchone()
        
        if user:
            status = user[12]  # Adjust index if needed
            if status != "approved":
                return jsonify({"status": "error", "message": "Your account is still pending approval."}), 403
                
            # Create session data
            user_id = user[0]
            session['user_id'] = user_id
            session['email'] = email
            session['role'] = user[6]
            session.permanent = True  # Make session persist longer
            
            # Debug print to verify session was created
            print(f"Created session for user_id: {user_id}, session data: {session}")
            
            user_data = {
                'id': user_id,
                'name': user[1],
                'email': user[2],
                'role': user[6],
                'business_name': user[7],
                'phone_number': user[8],
                'physical_address': user[9]
            }
            
            # Return success with user data
            return jsonify({"status": "success", "user": user_data}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        # Get user_id from request - you should use your authentication system
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch notifications for specific user
        cursor.execute("""
            SELECT id, order_id, message, status, created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        
        notifications = cursor.fetchall()
        
        # Count unread notifications
        cursor.execute("""
            SELECT COUNT(*) as unread_count
            FROM notifications
            WHERE user_id = %s AND status = 'unread'
        """, (user_id,))
        
        unread_count = cursor.fetchone()['unread_count']
        
        return jsonify({
            "notifications": notifications,
            "unread_count": unread_count
        }), 200
        
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        return jsonify({"error": f"Failed to fetch notifications: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notification_read():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        user_id = data.get('user_id')
        
        if not notification_id or not user_id:
            return jsonify({"error": "Notification ID and User ID are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mark specific notification as read
        cursor.execute("""
            UPDATE notifications
            SET status = 'read'
            WHERE id = %s AND user_id = %s
        """, (notification_id, user_id))
        
        conn.commit()
        
        return jsonify({"success": True, "message": "Notification marked as read"}), 200
        
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return jsonify({"error": f"Failed to mark notification as read: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mark all notifications as read for this user
        cursor.execute("""
            UPDATE notifications
            SET status = 'read'
            WHERE user_id = %s AND status = 'unread'
        """, (user_id,))
        
        conn.commit()
        
        return jsonify({"success": True, "message": "All notifications marked as read"}), 200
        
    except Exception as e:
        print(f"Error marking all notifications as read: {str(e)}")
        return jsonify({"error": f"Failed to mark all notifications as read: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart_api():
    try:
        data = request.json
        print(f"Received add to cart request with data: {data}")
        
        # Extract required fields
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        # Validate required fields
        if not user_id or not product_id:
            print("Missing required fields: user_id or product_id")
            return jsonify({"error": "User ID and Product ID are required"}), 400
        
        conn = get_db_connection()
        if not conn:
            print("Database connection failed")
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # First, get the product details from seller_add_product table
        cursor.execute("""
        SELECT id, seller_id, product_name, business_name, price, product_image, stock_quantity
        FROM seller_add_product
        WHERE id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            return jsonify({"error": "Product not found"}), 404
        
        # Debug output for product details
        print(f"Product details: {product}")
        
        # Extract proper seller_id from the product
        seller_id = product['seller_id']
        business_name = product['business_name']
        product_name = product['product_name']
        price = product['price']
        image_path = product['product_image']
        
        # Check if item already exists in the cart
        check_query = """
        SELECT id, quantity FROM carts 
        WHERE user_id = %s AND product_id = %s
        """
        cursor.execute(check_query, (user_id, product_id))
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity of existing item
            new_quantity = existing_item['quantity'] + quantity
            update_query = "UPDATE carts SET quantity = %s WHERE id = %s"
            cursor.execute(update_query, (new_quantity, existing_item['id']))
            conn.commit()
            item_id = existing_item['id']
            message = "Item quantity updated in cart"
        else:
            # Insert new item with correct seller_id from the product
            insert_query = """
            INSERT INTO carts (user_id, seller_id, product_id, Business_name, 
                              product_name, image_path, price, quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id, seller_id, product_id, business_name,
                product_name, image_path, price, quantity
            ))
            conn.commit()
            item_id = cursor.lastrowid
            message = "Item added to cart"
            
        # Get the updated cart item
        get_item_query = "SELECT * FROM carts WHERE id = %s"
        cursor.execute(get_item_query, (item_id,))
        added_item = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"Cart operation successful: {message}")
        print(f"Added item with seller_id: {seller_id}")
        
        return jsonify({
            "success": True,
            "message": message,
            "item": added_item
        })
        
    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        return jsonify({"error": str(e)}), 500




@app.route('/api/cart', methods=['GET'])
def get_cart_api():
    try:
        # First check if user is logged in via session
        session_user_id = session.get('user_id')
        # Get user_id from query parameters as fallback
        query_user_id = request.args.get('user_id')
        
        # Prioritize session user_id, then fallback to query parameter
        user_id = session_user_id or query_user_id
        
        if not user_id:
            print("No user ID found in session or query parameters")
            return jsonify({"success": False, "message": "User ID is required"}), 400
            
        print(f"Fetching cart items for user ID: {user_id}")
        
        conn = get_db_connection()
        if not conn:
            print("Database connection failed")
            return jsonify({"success": False, "message": "Database connection failed"}), 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Updated query with JOIN to fetch seller_id and other product details
            cursor.execute("""
            SELECT c.id, c.user_id, c.product_id, c.quantity, 
                   s.seller_id, s.product_name, s.price, s.product_image AS image_path, 
                   s.business_name AS seller_name
            FROM carts c
            JOIN seller_add_product s ON c.product_id = s.id
            WHERE c.user_id = %s
            """, (user_id,))
            
            cart_items = cursor.fetchall()
            
            # Calculate total price for each item
            total_price = 0
            for item in cart_items:
                # Ensure price is a float
                price = float(item['price']) if item['price'] else 0
                item['price'] = price
                
                # Calculate item total
                item_total = price * item['quantity']
                item['total'] = item_total
                total_price += item_total
                
                # Format image path if needed
                if item['image_path'] and not item['image_path'].startswith('http'):
                    # Keep the relative path - our Flutter app will construct the full URL
                    pass
                    
                # Debug output
                print(f"Item: {item['product_name']}, Seller ID: {item['seller_id']}, Price: {price}, Qty: {item['quantity']}")
            
            # Return structured response with success flag, cart items, and total
            response = {
                "success": True,
                "cart_items": cart_items,
                "total_items": len(cart_items),
                "total_price": total_price,
                "user_id": user_id
            }
            
            return jsonify(response)
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
    except Exception as e:
        print(f"Error in get_cart_api: {str(e)}")
        return jsonify({"success": False, "message": f"Error retrieving cart items: {str(e)}"}), 500



@app.route('/api/cart/clear', methods=['POST'])
def clear_cart_items():
    try:
        # Get data from request
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({"success": False, "message": "User ID is required"}), 400
            
        user_id = data.get('user_id')
        cart_item_ids = data.get('cart_item_ids', [])
        
        # Log received data
        print(f"Clearing cart items for user {user_id}, item IDs: {cart_item_ids}")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
            
        try:
            cursor = conn.cursor()
            
            if cart_item_ids and len(cart_item_ids) > 0:
                # Delete specific cart items using IN clause
                placeholders = ', '.join(['%s'] * len(cart_item_ids))
                query = f"DELETE FROM carts WHERE user_id = %s AND id IN ({placeholders})"
                params = [user_id] + cart_item_ids
                cursor.execute(query, params)
            else:
                # If no specific item IDs provided, delete all cart items for the user
                cursor.execute("DELETE FROM carts WHERE user_id = %s", (user_id,))
                
            conn.commit()
            rows_affected = cursor.rowcount
            print(f"Successfully cleared {rows_affected} cart items for user {user_id}")
            
            return jsonify({
                "success": True, 
                "message": f"Successfully cleared {rows_affected} cart items",
                "rows_deleted": rows_affected
            })
            
        except Exception as e:
            print(f"Database error in clear_cart_items: {str(e)}")
            conn.rollback()
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    except Exception as e:
        print(f"Error in clear_cart_items: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


    
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details_api(product_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Fetch product with seller information explicitly joined
        query = """
        SELECT p.*, p.seller_id, p.business_name
        FROM seller_add_product p
        WHERE p.id = %s
        """
        
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Debug output to verify seller_id is included
        print(f"Product details for ID {product_id}:")
        print(f"Product name: {product.get('product_name')}")
        print(f"Seller ID: {product.get('seller_id')}")
        print(f"Business name: {product.get('business_name')}")
        
        return jsonify(product)
            
    except Exception as e:
        print(f"Error getting product details: {e}")
        return jsonify({"error": str(e)}), 500

# Additional endpoint to update cart quantity
@app.route('/api/cart/update', methods=['POST'])
def update_cart_item():
    try:
        data = request.json
        item_id = data.get('id')
        quantity = data.get('quantity')
        
        if not item_id or quantity is None:
            return jsonify({"error": "Item ID and quantity are required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Update the quantity
        query = "UPDATE carts SET quantity = %s WHERE id = %s"
        cursor.execute(query, (quantity, item_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Cart updated successfully"})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint to remove item from cart
@app.route('/api/cart/remove', methods=['POST'])
def remove_cart_item():
    try:
        data = request.json
        item_id = data.get('id')
        
        if not item_id:
            return jsonify({"error": "Item ID is required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Delete the cart item
        query = "DELETE FROM carts WHERE id = %s"
        cursor.execute(query, (item_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Item removed from cart"})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    # Debug session data
    print(f"Session data in checkout: {session}")
    print(f"Cookie header: {request.headers.get('Cookie')}")
    
    if 'user_id' not in session:
        print(f"User not logged in, no user_id in session")
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    user_id = session['user_id']
    print(f"User ID from session: {user_id}")
    
    # Initialize with empty values
    user_info = {
        'name': '',
        'phone': '',
        'address': ''
    }
    
    try:
        conn = get_db_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Check the structure of userinfo table first
            cursor.execute("DESCRIBE userinfo")
            columns = cursor.fetchall()
            print(f"UserInfo table columns: {columns}")
            
            # Fetch user details - adjust column names if needed based on your actual table structure
            query = """
            SELECT Name, PhoneNumber, PhysicalAddress 
            FROM userinfo 
            WHERE ID = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                # Print raw result for debugging
                print(f"Raw database result: {result}")
                
                # Map database fields - handle different column name possibilities
                user_info = {
                    'name': result[0] if result[0] else '',
                    'phone': result[1] if result[1] else '',
                    'address': result[2] if result[2] else ''
                }
                
                # Make sure to print the exact values for debugging
                print(f"User info extracted:")
                print(f"  Name: '{user_info['name']}'")
                print(f"  Phone: '{user_info['phone']}'")
                print(f"  Address: '{user_info['address']}'")
            else:
                print(f"No user record found for user_id: {user_id}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

    # Process cart items
    data = request.get_json()
    cart_items = data.get('cart_items', [])
    print(f"Cart items received: {cart_items}")

    if not cart_items:
        return jsonify({'success': False, 'message': 'No cart items provided'}), 400

    subtotal = 0.0
    formatted_cart = []

    for item in cart_items:
        try:
            pid = item['product_id']
            pname = item.get('product_name', 'Unknown Product')
            price = float(item['price'])
            qty = int(item['quantity'])
            total = price * qty
            subtotal += total

            formatted_cart.append({
                'product_id': pid,
                'product_name': pname,
                'price': price,
                'quantity': qty,
                'total': total,
                'image_path': item.get('image_path', '')
            })
        except (KeyError, ValueError) as e:
            print(f"Error processing cart item: {e}")
            continue

    shipping_fee = 50.0
    grand_total = subtotal + shipping_fee

    # Print final response JSON for debugging
    response_data = {
        'success': True,
        'user_info': user_info,
        'cart': formatted_cart,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': grand_total
    }
    print(f"Sending response: {json.dumps(response_data)}")

    # Return the response with user info matching Flutter app expectations
    return jsonify(response_data), 200

# Add this route for testing session
@app.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'message': 'User is logged in',
            'user_id': session['user_id']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'User is not logged in'
        }), 401

@app.route('/api/place-order', methods=['POST'])
def api_place_order():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        payment_method = data.get('payment_method')
        cart_items = data.get('cart_items')  # Should be sent from mobile as a list of items

        if not user_id or not payment_method or not cart_items:
            return jsonify({"error": "Missing required fields"}), 400

        # Fetch user shipping details
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Name, PhoneNumber, PhysicalAddress
            FROM userinfo
            WHERE ID = %s
        """, (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Shipping details not found. Please update your details."}), 400

        name, phone_number, physical_address = result

        # Insert each item as an order
        for item in cart_items:
            cursor.execute("""
                INSERT INTO orders (
                    user_id, product_id, Name, PhoneNumber, PhysicalAddress,
                    product_name, price, quantity_order, total, payment_method, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                item['product_id'],
                name,
                phone_number,
                physical_address,
                item['product_name'],
                item['price'],
                item['quantity'],
                item['total'],
                payment_method,
                'Pending'
            ))

        conn.commit()
        return jsonify({"message": "Order placed successfully."}), 200

    except Exception as e:
        print(f"Error placing order (API): {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()




@app.route('/api/shop')
def api_shop():
    conn = None
    cursor = None
    category = request.args.get('category')
    search_query = request.args.get('search')
    
    print(f"[DEBUG] category={category}, search_query={search_query}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT 
                id,
                product_name,
                category,
                mini_description,
                main_description,
                price,
                stock_quantity,  -- Make sure this field exists in your seller_add_product table
                CONCAT('http://192.168.0.21:5000/static/uploads/', product_image) AS product_image,
                CONCAT('http://192.168.0.21:5000/static/uploads/', sub_image_1) AS sub_image_1,
                CONCAT('http://192.168.0.21:5000/static/uploads/', sub_image_2) AS sub_image_2,
                CONCAT('http://192.168.0.21:5000/static/uploads/', sub_image_3) AS sub_image_3,
                business_name,
                seller_id
            FROM seller_add_product
        """
        
        params = []
        conditions = []
        
        if category and category.lower() != 'all':
            conditions.append("LOWER(category) = LOWER(%s)")
            params.append(category)
        
        if search_query:
            conditions.append("LOWER(product_name) LIKE LOWER(%s)")
            params.append(f"%{search_query}%")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        print(f"[DEBUG] Final SQL: {sql} | Params: {params}")
        cursor.execute(sql, tuple(params))
        products = cursor.fetchall()
        
        print(f"[DEBUG] Found {len(products)} products.")
        return jsonify(products)
    
    except Error as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)})
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Add this new route to update stock quantity when an order is confirmed
@app.route('/api/orders/confirm', methods=['POST'])
def api_confirm_order():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.json
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({"error": "Missing order_id parameter"}), 400
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # First, get the order items to know which products to update
        cursor.execute("""
            SELECT 
                oi.product_id, 
                oi.quantity
            FROM 
                order_items oi
            JOIN 
                orders o ON oi.order_id = o.id
            WHERE 
                o.id = %s
        """, (order_id,))
        
        order_items = cursor.fetchall()
        
        if not order_items:
            return jsonify({"error": "Order not found or has no items"}), 404
        
        # Update the order status to confirmed
        cursor.execute("""
            UPDATE orders
            SET status = 'confirmed'
            WHERE id = %s
        """, (order_id,))
        
        # Update product stock quantities
        for item in order_items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Update the stock quantity in the product table
            cursor.execute("""
                UPDATE seller_add_product
                SET stock_quantity = GREATEST(0, stock_quantity - %s)
                WHERE id = %s
            """, (quantity, product_id))
            
            # Log the stock update
            print(f"[INFO] Updated stock for product ID {product_id}: reduced by {quantity}")
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Order confirmed and stock quantities updated",
            "order_id": order_id
        })
        
    except Error as e:
        if conn:
            conn.rollback()
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

otp_store = {}

@app.route('/api/send-otp', methods=['POST'])
def api_send_otp():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({
            'status': 'error',
            'message': 'Email is required'
        }), 400
    
    try:
        # Generate a random 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in both session and backup dictionary with expiration time
        expiry_time = time.time() + 600  # 10 minutes expiry
        
        # Store in session
        session['otp'] = otp
        session['otp_email'] = email
        session['otp_expiry'] = expiry_time
        
        # Store in backup dictionary (keyed by email)
        otp_store[email] = {
            'otp': otp,
            'expiry': expiry_time
        }
        
        # Debug logs
        print(f"Generated OTP for {email}: {otp}")
        print(f"Session data: {dict(session)}")
        print(f"OTP store: {otp_store}")
        
        # Send email with OTP
        subject = "Your OTP Code"
        message_body = f"Your OTP code is: {otp}"
        
        msg = Message(subject, sender='mediaverse888@gmail.com', recipients=[email])
        msg.body = message_body
        msg.html = f"<p>{message_body}</p>"
        
        mail.send(msg)
        
        # Set a cookie in the response to help maintain session
        response = jsonify({
            'status': 'success',
            'message': 'OTP sent successfully'
        })
        
        return response
        
    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to send OTP: {str(e)}'
        }), 500

@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.json
    user_otp = data.get('otp')
    email = data.get('email')
    
    # Debug logs
    print(f"Verifying OTP for {email}: {user_otp}")
    print(f"Session data: {dict(session)}")
    print(f"OTP store: {otp_store}")
    print(f"Request cookies: {request.cookies}")
    
    if not user_otp or not email:
        return jsonify({
            'status': 'error',
            'message': 'OTP and email are required'
        }), 400
    
    # First check session
    stored_otp = session.get('otp')
    stored_email = session.get('otp_email')
    expiry_time = session.get('otp_expiry')
    
    # If not in session, check backup dictionary
    if not stored_otp or not stored_email:
        print("OTP not found in session, checking backup store")
        if email in otp_store:
            stored_otp = otp_store[email]['otp']
            expiry_time = otp_store[email]['expiry']
            stored_email = email
        else:
            return jsonify({
                'status': 'error',
                'message': 'No OTP found. Please request a new OTP.'
            }), 400
    
    current_time = time.time()
    
    # Check expiry
    if current_time > expiry_time:
        # Clear expired OTP
        if email in otp_store:
            del otp_store[email]
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('otp_expiry', None)
        
        return jsonify({
            'status': 'error',
            'message': 'OTP has expired. Please request a new one.'
        }), 400
    
    # Check if OTP matches
    if user_otp == stored_otp:
        # Clear OTP after successful verification
        if email in otp_store:
            del otp_store[email]
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('otp_expiry', None)
        
        # Mark user as verified in session
        session['verified'] = True
        session['verified_email'] = email
        
        print(f"OTP verified successfully for {email}")
        print(f"Updated session: {dict(session)}")
        
        # Return success response and set session cookie
        response = jsonify({
            'status': 'success',
            'message': 'OTP verified successfully'
        })
        
        return response
    else:
        print(f"Invalid OTP. Expected {stored_otp}, got {user_otp}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid OTP. Please check and try again.'
        }), 400


def generate_otp():
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

@app.route('/api/forgot', methods=['POST'])
def forgot_password():
    """Handle forgot password requests - verify email exists"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if the email exists in the database
        cursor.execute("SELECT * FROM userinfo WHERE Email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Email not found'}), 404
            
        # Return success - let the frontend navigate to the reset password page
        return jsonify({
            'status': 'success',
            'message': 'Email verified successfully. Please continue with the reset process.'
        })
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/request-password-reset', methods=['POST'])
def request_password_reset():
    """Alias for forgot_password to maintain compatibility with frontend"""
    return forgot_password()

@app.route('/api/reset-password-init', methods=['POST'])
def reset_password_init():
    """Initialize password reset process and send OTP"""
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    
    if not email or not new_password:
        return jsonify({'status': 'error', 'message': 'Email and new password are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if the email exists in the database
        cursor.execute("SELECT * FROM userinfo WHERE Email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Email not found'}), 404
            
        # Generate a random 6-digit OTP
        otp = generate_otp()
        
        # Store OTP in both session and backup dictionary with expiration time
        expiry_time = time.time() + 600  # 10 minutes expiry
        
        # Store in session
        session['reset_otp'] = otp
        session['reset_email'] = email
        session['reset_password'] = new_password
        session['reset_expiry'] = expiry_time
        
        # Store in backup dictionary (keyed by email)
        otp_store[email] = {
            'otp': otp,
            'new_password': new_password,
            'expiry': expiry_time
        }
        
        # Debug logs
        print(f"Generated OTP for password reset - {email}: {otp}")
        print(f"Session data: {dict(session)}")
        print(f"OTP store: {otp_store}")
        
        # Send email with OTP
        subject = "Your Password Reset Code"
        message_body = f"Your password reset code is: {otp}"
        
        try:
            msg = Message(subject, sender='mediaverse888@gmail.com', recipients=[email])
            msg.body = message_body
            msg.html = f"""
            <html>
            <body>
              <h2>Password Reset Verification</h2>
              <p>You requested to reset your password for your MediaVerse account.</p>
              <p>Your verification code is: <strong>{otp}</strong></p>
              <p>This code will expire in 10 minutes.</p>
              <p>If you didn't request this, please ignore this email or contact support.</p>
            </body>
            </html>
            """
            
            mail.send(msg)
            
            # Include debug OTP in response (remove in production)
            response = {
                'status': 'success',
                'message': 'OTP sent successfully',
                'debug_otp': otp  # Remove this in production!
            }
            
            return jsonify(response)
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to send email: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Error sending reset OTP: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to send OTP: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/verify-reset-otp', methods=['POST'])
def api_verify_reset_otp():
    data = request.json
    user_otp = data.get('otp')
    email = data.get('email')
    new_password = data.get('new_password')
    
    # Debug logs
    print(f"Verifying password reset OTP for {email}: {user_otp}")
    print(f"Session data: {dict(session)}")
    print(f"OTP store: {otp_store}")
    
    if not user_otp or not email or not new_password:
        return jsonify({
            'status': 'error',
            'message': 'OTP, email, and new password are required'
        }), 400
    
    # First check session
    stored_otp = session.get('reset_otp')
    stored_email = session.get('reset_email')
    stored_password = session.get('reset_password')
    expiry_time = session.get('reset_expiry')
    
    # If not in session, check backup dictionary
    if not stored_otp or not stored_email:
        print("Reset OTP not found in session, checking backup store")
        if email in otp_store:
            stored_otp = otp_store[email]['otp']
            stored_password = otp_store[email]['new_password']
            expiry_time = otp_store[email]['expiry']
            stored_email = email
        else:
            return jsonify({
                'status': 'error',
                'message': 'No OTP found. Please request a new OTP.'
            }), 400
    
    current_time = time.time()
    
    # Check expiry
    if current_time > expiry_time:
        # Clear expired OTP
        if email in otp_store:
            del otp_store[email]
        session.pop('reset_otp', None)
        session.pop('reset_email', None)
        session.pop('reset_password', None)
        session.pop('reset_expiry', None)
        
        return jsonify({
            'status': 'error',
            'message': 'OTP has expired. Please request a new one.'
        }), 400
    
    # Check if OTP matches and new_password matches stored password
    if user_otp == stored_otp and new_password == stored_password:
        # Update the user's password in the database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Print the query params for debugging
            print(f"Attempting to update password for email: {email}")
            
            # Hash the new password before storing it
            # Check if your app is using a specific hashing method
            hashed_password = new_password  # Try without hashing first
            
            # Update the password in the database - check your column name case sensitivity
            cursor.execute(
                "UPDATE userinfo SET Password = %s WHERE Email = %s",
                (hashed_password, email)
            )
            
            # Check if any rows were affected
            rows_affected = cursor.rowcount
            print(f"Rows affected by update: {rows_affected}")
            
            # If no rows were updated, it could be a column name issue
            if rows_affected == 0:
                print("No rows updated - trying alternative column names")
                # Try alternative column names (databases can be case-sensitive)
                try:
                    cursor.execute(
                        "UPDATE userinfo SET password = %s WHERE email = %s",
                        (hashed_password, email)
                    )
                    print(f"Alternative query affected rows: {cursor.rowcount}")
                except Exception as column_err:
                    print(f"Alternative column attempt error: {column_err}")
            conn.commit()
            
            # Clear OTP after successful verification
            if email in otp_store:
                del otp_store[email]
            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('reset_password', None)
            session.pop('reset_expiry', None)
            
            print(f"Password reset successful for {email}")
            
            return jsonify({
                'status': 'success',
                'message': 'Password has been reset successfully'
            })
            
        except Exception as e:
            print(f"Database error during password reset: {e}")
            return jsonify({
                'status': 'error',
                'message': 'An error occurred while resetting your password'
            }), 500
        finally:
            cursor.close()
            conn.close()
    else:
        print(f"Invalid OTP for password reset. Expected {stored_otp}, got {user_otp}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid OTP. Please check and try again.'
        }), 400

# Modified change password endpoint
@app.route('/api/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    
    if not data or 'email' not in data or 'old_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Email, old password, and new password are required"}), 400
    
    email = data['email']
    old_password = data['old_password']
    new_password = data['new_password']
    
    # Connect to the database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the email exists and the old password is correct
        cursor.execute("SELECT * FROM userinfo WHERE Email = %s AND Password = %s", (email, old_password))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Update the user's password
        cursor.execute("UPDATE userinfo SET Password = %s WHERE Email = %s", (new_password, email))
        conn.commit()
        
        conn.close()
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred. Please try again later."}), 500

# New endpoint for resetting password (when user comes from the reset link)
@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    if not data or 'email' not in data or 'new_password' not in data or 'token' not in data:
        return jsonify({"error": "Email, new password, and token are required"}), 400
    
    email = data['email']
    new_password = data['new_password']
    token = data['token']
    
    # In a real application, you'd verify the token here
    # For now, we'll just update the password
    
    # Connect to the database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the email exists
        cursor.execute("SELECT * FROM userinfo WHERE Email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "Email not found"}), 404
        
        # Update the user's password
        cursor.execute("UPDATE userinfo SET Password = %s WHERE Email = %s", (new_password, email))
        conn.commit()
        
        conn.close()
        
        return jsonify({"message": "Password reset successfully"}), 200
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred. Please try again later."}), 500
    

@app.route('/get_orders', methods=['GET'])
def get_orders():
    """Fetch all orders from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, user_id, product_name, price, quantity_order, 
                   total, payment_method, created_at, status 
            FROM orders
            ORDER BY created_at DESC
        """)
        
        orders = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for order in orders:
            if 'created_at' in order and order['created_at']:
                order['created_at'] = order['created_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(orders), 200
    
    except Exception as e:
        logging.error(f"Error fetching orders: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_products', methods=['GET'])
def get_products():
    """Fetch all products from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.id, p.name AS product_name, p.description, p.price, 
                   p.stock_quantity, p.image_url, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock_quantity > 0
            ORDER BY p.id DESC
        """)
        
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(products), 200
    
    except Exception as e:
        logging.error(f"Error fetching products: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_status/<int:order_id>', methods=['POST'])
def update_status_api(order_id):
    """Update the status of an order"""
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        logging.error(f"No status provided for order {order_id}")
        return jsonify({"error": "Status is required"}), 400
    
    try:
        logging.info(f"Updating order {order_id} to status: {new_status}")
        
        # Update the order status in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE orders
            SET status = %s
            WHERE id = %s
        """, (new_status, order_id))
        
        conn.commit()
        
        # Close connection
        cursor.close()
        conn.close()
        
        logging.info(f"Order {order_id} updated successfully.")
        return jsonify({"message": "Status updated successfully!"}), 200
    
    except mysql.connector.Error as err:
        logging.error(f"MySQL error: {str(err)}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500


#api End

#MESSAGE START

@app.route('/contact-seller')
def contact_seller():
    # Extract query parameters with defaults if not provided
    seller_id = request.args.get('seller_id', None)
    seller_name = request.args.get('seller_name', "Unknown Seller")
    order_id = request.args.get('order_id', None)
    product_name = request.args.get('product_name', "Unnamed Product")
    product_image = request.args.get('image_path', "default_image.jpg")
    product_price = request.args.get('price', "0.00")

    # Debugging: Log extracted parameters
    print(f"seller_id: {seller_id}, seller_name: {seller_name}, order_id: {order_id}, "
          f"product_name: {product_name}, product_image: {product_image}, product_price: {product_price}")

    # Handle missing `seller_id` gracefully
    if not seller_id:
        return render_template('error.html', message="Seller information is required to proceed"), 400

    # Fetch order details from the database if `order_id` is provided
    order_details = None
    if order_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order_details = cursor.fetchone()
        cursor.close()
        conn.close()

    # Render the template with order, product, and seller details
    return render_template(
        'messages.html',
        seller_id=seller_id,
        seller_name=seller_name,
        order_id=order_id,
        product_name=product_name,
        product_image=product_image,
        product_price=product_price,
        order_details=order_details
    )


from mysql.connector import Error

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        # Get the data from the request
        data = request.get_json()

        print(f"Received data: {data}")  # Debugging line to see the incoming data

        # Extract data
        message = data.get('message')
        seller_id = data.get('seller_id')
        order_id = data.get('order_id')  # Optional field, can be None
        business_name = data.get('business_name')
        sender_type = data.get('sender_type')

        # Get user info from session
        user_id = session.get('user_id')  # Assuming the user ID is stored in the session
        name = session.get('name')  # Assuming the username is stored in the session

        # Validate required fields and identify missing ones
        missing_fields = []
        if not message:
            missing_fields.append('message')
        if not seller_id:
            missing_fields.append('seller_id')
        if not business_name:
            missing_fields.append('business_name')
        if not user_id:
            missing_fields.append('user_id (from session)')
        if not name:
            missing_fields.append('name (from session)')

        # If any required fields are missing, return an error
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the message into the database
        query = """
        INSERT INTO messages (user_id, seller_id, order_id, business_name, message, sender_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, seller_id, order_id, business_name, message, sender_type))

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return success response
        return jsonify({'success': True, 'message': 'Message sent successfully'}), 200

    except Error as e:
        # Handle database errors
        print(f"Database Error: {e}")
        return jsonify({'success': False, 'message': f"Database Error: {e}"}), 500

    except Exception as e:
        # Handle any other errors
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500



@app.route('/get-sellers', methods=['GET'])
def get_sellers():
    user_id = session.get('user_id')  # Get the logged-in user ID from session
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Query to get distinct sellers for the logged-in user
        cursor.execute("""
            SELECT DISTINCT seller_id, business_name 
            FROM messages 
            WHERE user_id = %s
        """, (user_id,))

        Sellers = cursor.fetchall()  # Fetch all distinct sellers

        if not Sellers:
            return jsonify({'success': False, 'message': 'No sellers found'}), 404

        return jsonify({'success': True, 'Sellers': Sellers})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error: {err}'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_sales_analytics')
def get_sales_analytics():
    date_range = request.args.get('range', 'week')
    
    # Calculate dates based on range
    end_date = datetime.now()
    if date_range == 'week':
        start_date = end_date - timedelta(days=7)
    elif date_range == 'month':
        start_date = end_date - timedelta(days=30)
    elif date_range == 'quarter':
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    # Query your database for the analytics data
    # This is just a placeholder - you'll need to implement actual queries
    
    # Example data structure - replace with actual data from your database
    data = {
        "ordersByStatus": [
            {"name": "Completed", "value": 7},
            {"name": "Pending", "value": 8},
            {"name": "Confirmed", "value": 5},
            {"name": "Shipped Out", "value": 3},
            {"name": "Cancelled", "value": 3}
        ],
        "salesByMonth": [
            {"name": "Dec 2024", "sales": 1280},
            {"name": "Jan 2025", "sales": 2390},
            {"name": "Feb 2025", "sales": 3490},
            {"name": "Mar 2025", "sales": 3000},
            {"name": "Apr 2025", "sales": 2800},
            {"name": "May 2025", "sales": 3300}
        ],
        "productPerformance": [
            {"name": "Phonics", "sales": 720, "orders": 6},
            {"name": "The Contenders", "sales": 477, "orders": 3},
            {"name": "Tekken", "sales": 1295, "orders": 5},
            {"name": "Final Fantasy XVI", "sales": 1740, "orders": 3},
            {"name": "Time Magazine", "sales": 2998, "orders": 3}
        ],
        "recentOrders": [
            {"id": 160, "product": "Tomes Jones Vinyls CD", "amount": 235, "status": "Shipped Out", "date": "2025-05-18"},
            {"id": 159, "product": "The Contenders", "amount": 159, "status": "Shipped Out", "date": "2025-05-18"},
            {"id": 157, "product": "PS5 Final Fantasy XVI (R3)", "amount": 580, "status": "Confirmed", "date": "2025-05-18"},
            {"id": 154, "product": "Tekken", "amount": 259, "status": "Completed", "date": "2025-05-18"}
        ],
        "summary": {
            "totalSales": 11580,
            "totalOrders": 25,
            "averageOrderValue": 463.20,
            "completionRate": 68
        }
    }
    
    return jsonify(data)




    
@app.route('/get-messages', methods=['GET', 'POST'])
def messages():
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User is not logged in'}), 401

    # Get the logged-in user's id from the session
    user_id = session['user_id']
    print(f"Logged-in user ID: {user_id}")  # Debugging step

    # If the request method is GET, fetch messages
    if request.method == 'GET':
        seller_id = request.args.get('seller_id')
        print(f"seller_id: {seller_id}")  # Debugging step

        if not seller_id:
            return jsonify({'success': False, 'message': 'Missing seller_id'}), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Query the database to get messages for the user and seller
            cursor.execute("""
                SELECT user_id, seller_id, message, sender_type, created_at 
                FROM messages 
                WHERE (user_id = %s AND seller_id = %s) OR (user_id = %s AND seller_id = %s)
            """, (user_id, seller_id, seller_id, user_id))  # Fetch messages where the user or seller is involved
            messages = cursor.fetchall()

            if not messages:
                return jsonify({'success': False, 'message': 'No messages found'}), 404

            # Return the messages as a response
            return jsonify({
                'success': True,
                'messages': messages  # Return messages as a list of dictionaries
            })

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")  # Debugging step
            return jsonify({'success': False, 'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

    # If the request method is POST, send a message
    elif request.method == 'POST':
        # Get the data from the request
        data = request.get_json()
        print(f"Received data: {data}")  # Debugging line to see the incoming data

        # Extract data
        message = data.get('message')
        seller_id = data.get('seller_id')
        sender_type = data.get('sender_type')

        if not message or not seller_id or not sender_type:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: message, seller_id, or sender_type'
            }), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insert the message into the database
            query = """
            INSERT INTO messages (user_id, seller_id, message, sender_type)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, seller_id, message, sender_type))

            # Commit the transaction
            conn.commit()

            return jsonify({'success': True, 'message': 'Message sent successfully'}), 200

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")  # Debugging step
            return jsonify({'success': False, 'message': f'Error: {err}'}), 500

        finally:
            cursor.close()
            conn.close()

#MESSAGE END

@app.route('/homepage')
def homepage():
    if 'user' in session:
        return render_template('homepage.html', user=session['user']['name'])  # Pass user name to template
    return redirect(url_for('login_page'))  # Redirect if not logged in

@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user from session
    return redirect(url_for('login_page'))  # Redirect to login page after logout

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/logout', methods=['POST'])
def logout():
    # Clear the user session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('login'))

