import datetime
from tkinter import INSERT

from flask import Flask, render_template, request, redirect, session
from flask import jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = "smartwaste"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_waste",

    autocommit=True,

    connection_timeout=1000
)

cursor = db.cursor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        

        sql = """
        INSERT INTO users(name, email, password, phone)
        VALUES(%s, %s, %s, %s)
        """

        values = (name, email, password, phone)

        db.reconnect()
        
        try:

            cursor.execute(sql, values)

            db.commit()

            return redirect('/login')

        except:

            return """

            <h3 style='text-align:center;
            color:red;
            margin-top:50px;'>

            Email Already Registered

            </h3>

            """

    return render_template('register.html')

#to delete
#@app.route('/login')
#def login():
    #return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"

        values = (email, password)

        db.reconnect()
        
        cursor.execute(sql, values)

        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]

            session['user_name'] = user[1]
            
            session['admin'] = False

            if user[5] is None:

                return redirect('/complete_profile')

            return redirect('/dashboard')

        else:
            return """

            <h3 style='text-align:center;
            color:red;
            margin-top:50px;'>

            Invalid Email or Password

            </h3>

            """

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
# I will delete thses 2 lines if i want 
# (used forpreventing users from opening pages without logging in.)

    if 'user_id' not in session:

        return redirect('/login')

    return render_template('dashboard.html')

@app.route('/schedules')
def schedules():

    db.reconnect()

    cursor.execute("""

    SELECT

    schedules.schedule_id,
    schedules.zone,
    areas.area_name,
    schedules.collection_day,
    schedules.collection_date,
    schedules.time_slot

    FROM schedules

    JOIN areas

    ON schedules.area_id = areas.area_id

    ORDER BY schedules.schedule_id

    """)

    data = cursor.fetchall()

    return render_template(

        'schedules.html',

        schedules=data

    )

@app.route('/pickup', methods=['GET', 'POST'])
def pickup():

    # I will delete thses 2 lines if i want 
    #(used forpreventing users from opening pages without logging in.)

    if 'user_id' not in session:

        return redirect('/login')

    if request.method == 'POST':

        user_id = session['user_id']

        user_name = request.form['user_name']

        phone = request.form['phone']

        address = request.form['address']

        landmark = request.form['landmark']

        area_id = request.form['area_id']

        waste_weight = request.form['waste_weight']

        additional_notes = request.form['additional_notes']

        # FETCH AREA NAME

        sql_area = """

        SELECT area_name, zone

        FROM areas

        WHERE area_id=%s

        """

        values_area = (area_id,)

        db.reconnect()

        cursor.execute(sql_area, values_area)

        area_data = cursor.fetchone()

        area_name = area_data[0]

        zone = area_data[1]

        # FETCH SCHEDULE

        sql_schedule = """

        SELECT collection_day, collection_date, time_slot

        FROM schedules

        WHERE area_id=%s

        ORDER BY schedule_id DESC

        LIMIT 1

        """

        values_schedule = (area_id,)

        db.reconnect()

        cursor.execute(sql_schedule, values_schedule)

        schedule = cursor.fetchone()

        if schedule:

            pickup_day = schedule[0]

            pickup_date = schedule[1]

            pickup_slot = schedule[2]

        else:

            pickup_day = "Not Assigned"

            pickup_date = None

            pickup_slot = "Not Assigned"

        # INSERT PICKUP REQUEST

        sql = """

        INSERT INTO pickup_requests(

        user_id,
        user_name,
        phone,
        address,
        landmark,
        area_id,
        area,
        zone,
        pickup_day,
        pickup_date,
        pickup_slot,
        waste_weight,
        additional_notes,
        status

        )

        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

        """

        values = (

        user_id,
        user_name,
        phone,
        address,
        landmark,
        area_id,
        area_name,
        zone,
        pickup_day,
        pickup_date,
        pickup_slot,
        waste_weight,
        additional_notes,
        'Pending'

        )

        db.reconnect()

        cursor.execute(sql, values)

        db.commit()

        return redirect('/reports')

    # LOAD AREAS

    #db.reconnect()

    #cursor.execute("""

    #SELECT area_id, area_name

    #FROM areas

    #""")

    #areas = cursor.fetchall()

    # FETCH USER DETAILS

    user_id = session['user_id']

    db.reconnect()

    cursor.execute("""

    SELECT

    name,
    phone,
    house_no,
    address,
    landmark,
    area_id,
    zone

    FROM users

    WHERE user_id=%s

    """, (user_id,))

    user_data = cursor.fetchone()

    # FETCH AREA NAME

    db.reconnect()

    cursor.execute("""

    SELECT area_name, zone

    FROM areas

    WHERE area_id=%s

    """, (user_data[5],))

    area_data = cursor.fetchone()

    return render_template(

        'pickup.html',

        user=user_data,

        area_name=area_data[0]

    )

#@app.route('/get_schedule/<int:area_id>')
#def get_schedule(area_id):


    db.reconnect()

    sql = """

    SELECT collection_day, time_slot

    FROM schedules

    WHERE area_id=%s

    """

    values = (area_id,)

    cursor.execute(sql, values)

    schedule = cursor.fetchone()


    from datetime import datetime, timedelta

    today = datetime.today()

    pickup_date = today + timedelta(days=2)

    formatted_date = pickup_date.strftime('%d-%m-%Y')


    return jsonify({

        "collection_day": schedule[0],

        "pickup_date": formatted_date,

        "time_slot": schedule[1]

    })

@app.route('/get_schedule/<int:area_id>')
def get_schedule(area_id):

    db.reconnect()

    cursor.execute("""

    SELECT

    collection_day,
    collection_date,
    time_slot

    FROM schedules

    WHERE area_id=%s

    """, (area_id,))

    schedule = cursor.fetchone()

    return {

        "collection_day": schedule[0],

        "collection_date": schedule[1].strftime('%d-%m-%Y'),

        "time_slot": schedule[2]

    }

@app.route('/reports')
def reports():
# I will delete thses 2 lines if i want 
# (used forpreventing users from opening pages without logging in.)

    if 'user_id' not in session:    

        return redirect('/login')
    
    user_id = session['user_id']

    db.reconnect()

    cursor.execute("""

    SELECT

    request_id,
    area,
    zone,
    collection_day,
    collection_date,
    time_slot,
    waste_weight,
    status

    FROM pickup_requests

    WHERE user_id=%s

    ORDER BY request_id DESC

    """, (user_id,))

    data = cursor.fetchall()

    return render_template(

        'reports.html',

        reports=data

    )

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        sql = """
        SELECT * FROM admin
        WHERE username=%s AND password=%s
        """

        values = (username, password)

        db.reconnect()

        cursor.execute(sql, values)

        admin = cursor.fetchone()

        if admin:

            session['admin'] = True
            
            return redirect('/admin_dashboard')

        else:
            return "Invalid Admin Login"
        
    return render_template('admin_login.html')    

@app.route('/admin_dashboard')
def admin_dashboard():

    if not session.get('admin'):

        return redirect('/')
    
    db.reconnect()

    # TOTAL USERS

    cursor.execute("""

    SELECT COUNT(*)

    FROM users

    """)

    total_users = cursor.fetchone()[0]


    # TOTAL REQUESTS

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    """)

    total_requests = cursor.fetchone()[0]


    # PENDING

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE status='Pending'

    """)

    pending_requests = cursor.fetchone()[0]


    # APPROVED

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE status='Approved'

    """)

    approved_requests = cursor.fetchone()[0]


    # COMPLETED

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE status='Completed'

    """)

    completed_requests = cursor.fetchone()[0]


    # MISSED

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE status='Missed'

    """)

    missed_requests = cursor.fetchone()[0]


    # REJECTED

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE status='Rejected'

    """)

    rejected_requests = cursor.fetchone()[0]


    return render_template(

        'admin_dashboard.html',

        total_users=total_users,
        total_requests=total_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        completed_requests=completed_requests,
        missed_requests=missed_requests,
        rejected_requests=rejected_requests

    )

#TO DELETE
# @app.route('/view_users')
#def view_users():

 #   cursor.execute("""
  #  SELECT * FROM users
   # """)

    #users = cursor.fetchall()

    #return render_template(
   #     'view_users.html',
    #    users=users
   # )

# @app.route('/view_requests')
# def view_requests():

#     if not session.get('admin'):

#         return redirect('/')

#     status = request.args.get('status')

#     db.reconnect()

#     if status:

#         sql = """

#         SELECT

#         request_id,
#         user_name,
#         area,
#         zone,
#         pickup_day,
#         pickup_date,
#         pickup_slot,
#         waste_weight,
#         status

#         FROM pickup_requests

#         WHERE status=%s

#         ORDER BY request_id DESC

#         """

#         values = (status,)

#         cursor.execute(sql, values)

#     else:

#         cursor.execute("""

#         SELECT

#         request_id,
#         user_name,
#         area,
#         zone,
#         pickup_day,
#         pickup_date,
#         pickup_slot,
#         waste_weight,
#         status

#         FROM pickup_requests

#         ORDER BY request_id DESC

#         """)

#     requests = cursor.fetchall()

#     return render_template(

#         'view_requests.html',

#         requests=requests

#     )


@app.route('/view_requests')
def view_requests():

    if not session.get('admin'):

        return redirect('/')

    status = request.args.get('status')

    db.reconnect()

    if status:

        sql = """

        SELECT

        request_id,
        user_name,
        area,
        zone,

        COALESCE(collection_day, pickup_day),

        COALESCE(collection_date, pickup_date),

        COALESCE(time_slot, pickup_slot),

        waste_weight,

        status

        FROM pickup_requests

        WHERE status=%s

        ORDER BY request_id DESC

        """

        values = (status,)

        cursor.execute(sql, values)

    else:

        cursor.execute("""

        SELECT

        request_id,
        user_name,
        area,
        zone,

        COALESCE(collection_day, pickup_day),

        COALESCE(collection_date, pickup_date),

        COALESCE(time_slot, pickup_slot),

        waste_weight,

        status

        FROM pickup_requests

        ORDER BY request_id DESC

        """)

    requests = cursor.fetchall()

    return render_template(

        'view_requests.html',

        requests=requests

    )

@app.route('/manage_schedules', methods=['GET', 'POST'])
def manage_schedules():

    if not session.get('admin'):

        return redirect('/')
    
    if request.method == 'POST':

        zone = request.form['zone']

        area_id = request.form['area_id']

        collection_day = request.form['collection_day']

        collection_date = request.form['collection_date']

        time_slot = request.form['time_slot']


        sql = """

        INSERT INTO schedules(

        area_id,
        collection_day,
        collection_date,
        time_slot,
        zone

        )

        VALUES(%s,%s,%s,%s,%s)

        """

        values = (

            area_id,
            collection_day,
            collection_date,
            time_slot,
            zone

        )

        db.reconnect()

        cursor.execute(sql, values)

        db.commit()


    # LOAD AREAS

    db.reconnect()

    cursor.execute("""

    SELECT

    area_id,
    area_name,
    zone

    FROM areas

    ORDER BY zone, area_name

    """)

    areas = cursor.fetchall()


    # LOAD SCHEDULES

    db.reconnect()

    cursor.execute("""

    SELECT

    schedules.schedule_id,
    areas.zone,
    areas.area_name,
    schedules.collection_day,
    schedules.collection_date,
    schedules.time_slot

    FROM schedules

   JOIN areas
   ON schedules.area_id = areas.area_id

   ORDER BY schedules.schedule_id ASC
                   
   """)
    
    schedules = cursor.fetchall()


    return render_template(

        'manage_schedules.html',

        areas=areas,

        schedules=schedules

    )

@app.route('/delete_schedule/<int:id>')
def delete_schedule(id):

    sql = """
    DELETE FROM schedules
    WHERE schedule_id=%s
    """

    values = (id,)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/manage_schedules')

@app.route('/edit_schedule/<int:id>',
methods=['GET', 'POST'])
def edit_schedule(id):

    if request.method == 'POST':

        collection_day = request.form['collection_day']
        time_slot = request.form['time_slot']

        sql = """
        UPDATE schedules

        SET collection_day=%s,
        time_slot=%s

        WHERE schedule_id=%s
        """

        values = (
            collection_day,
            time_slot,
            id
        )

        cursor.execute(sql, values)

        db.commit()

        return redirect('/manage_schedules')

    cursor.execute("""
    SELECT * FROM schedules
    WHERE schedule_id=%s
    """, (id,))

    schedule = cursor.fetchone()

    return render_template(
        'edit_schedule.html',
        schedule=schedule
    )

@app.route('/manage_areas', methods=['GET', 'POST'])
def manage_areas():

    if not session.get('admin'):

        return redirect('/')

    if request.method == 'POST':

        area_name = request.form['area_name']

        zone = request.form['zone']


        sql = """

        INSERT INTO areas(

        area_name,
        zone

        )

        VALUES(%s,%s)

        """

        values = (

            area_name,
            zone

        )

        db.reconnect()

        cursor.execute(sql, values)

        db.commit()


    db.reconnect()

    cursor.execute("""

    SELECT *

    FROM areas

    ORDER BY area_id

    """)

    areas = cursor.fetchall()


    return render_template(

        'manage_areas.html',

        areas=areas

    )

@app.route('/delete_area/<int:id>')
def delete_area(id):

    sql = """
    DELETE FROM areas
    WHERE area_id=%s
    """

    values = (id,)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/manage_areas')

@app.route('/update_request_status/<int:id>/<status>')
def update_request_status(id, status):

    if not session.get('admin'):

        return redirect('/')
    
    sql = """
    UPDATE pickup_requests

    SET status=%s

    WHERE request_id=%s
    """

    values = (status, id)

    db.reconnect()
    
    cursor.execute(sql, values)

    db.commit()

    return redirect('/view_requests')

@app.route('/analytics')
def analytics():

    if not session.get('admin'):

        return redirect('/')
    
    db.reconnect()

    # AREA-WISE ANALYTICS

    cursor.execute("""

    SELECT

    area,
    COUNT(*) as total_requests

    FROM pickup_requests

    GROUP BY area

    ORDER BY total_requests DESC

    """)

    area_analytics = cursor.fetchall()


    # ZONE-WISE ANALYTICS

    cursor.execute("""

    SELECT

    zone,
    COUNT(*) as total_requests

    FROM pickup_requests

    GROUP BY zone

    ORDER BY total_requests DESC

    """)

    zone_analytics = cursor.fetchall()


    # STATUS-WISE ANALYTICS

    cursor.execute("""

    SELECT

    status,
    COUNT(*) as total_status

    FROM pickup_requests

    GROUP BY status

    """)

    status_analytics = cursor.fetchall()


    return render_template(

        'analytics.html',

        area_analytics=area_analytics,
        zone_analytics=zone_analytics,
        status_analytics=status_analytics

    )

@app.route('/view_users')
def view_users():

    search = request.args.get('search')

    if search:

        sql = """

        SELECT

        users.user_id,
        users.name,
        users.email,
        users.phone,
        users.address,
        users.zone,

        COUNT(

        CASE

        WHEN pickup_requests.status='Completed'

        THEN 1

        END

        ) as participation_score

        FROM users

        LEFT JOIN pickup_requests

        ON users.user_id = pickup_requests.user_id

        WHERE

        users.name LIKE %s

        OR users.email LIKE %s

        OR users.phone LIKE %s

        OR users.zone LIKE %s

        GROUP BY users.user_id

        """

        values = (

            '%' + search + '%',
            '%' + search + '%',
            '%' + search + '%',
            '%' + search + '%'

        )

        cursor.execute(sql, values)

    else:

        cursor.execute("""

        SELECT

        users.user_id,
        users.name,
        users.email,
        users.phone,
        users.address,
        users.zone,

        COUNT(

        CASE

        WHEN pickup_requests.status='Completed'

        THEN 1

        END

        ) as participation_score

        FROM users

        LEFT JOIN pickup_requests

        ON users.user_id = pickup_requests.user_id

        GROUP BY users.user_id

        ORDER BY users.user_id

        """)

    users = cursor.fetchall()

    return render_template(

        'view_users.html',

        users=users

    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():

    if 'user_id' not in session:

        return redirect('/login')


    if request.method == 'POST':

        house_no = request.form['house_no']

        address = request.form['address']

        landmark = request.form['landmark']

        area_id = request.form['area_id']


        # FETCH AREA + ZONE

        sql_area = """

        SELECT area_name, zone

        FROM areas

        WHERE area_id=%s

        """

        values_area = (area_id,)

        db.reconnect()

        cursor.execute(sql_area, values_area)

        area_data = cursor.fetchone()


        zone = area_data[1]


        # UPDATE USER PROFILE

        sql = """

        UPDATE users

        SET

        house_no=%s,
        address=%s,
        landmark=%s,
        area_id=%s,
        zone=%s

        WHERE user_id=%s

        """

        values = (

            house_no,
            address,
            landmark,
            area_id,
            zone,
            session['user_id']

        )

        db.reconnect()

        cursor.execute(sql, values)

        db.commit()


        return redirect('/dashboard')


    # LOAD AREAS

    db.reconnect()

    cursor.execute("""

    SELECT area_id, area_name

    FROM areas

    """)

    areas = cursor.fetchall()


    return render_template(

        'complete_profile.html',

        areas=areas

    )

@app.route('/special_pickup', methods=['GET', 'POST'])
def special_pickup():
# I will delete thses 2 lines if i want 
# (used forpreventing users from opening pages without logging in.)

    if 'user_id' not in session:

        return redirect('/login')
    
    user_id = session['user_id']

    db.reconnect()

    cursor.execute("""

    SELECT

    name,
    phone,
    area_id,
    zone

    FROM users

    WHERE user_id=%s

    """, (user_id,))

    user = cursor.fetchone()


    # FETCH AREA NAME

    db.reconnect()

    cursor.execute("""

    SELECT area_name

    FROM areas

    WHERE area_id=%s

    """, (user[2],))

    area_data = cursor.fetchone()

    area_name = area_data[0]


    # PARTICIPATION SCORE

    db.reconnect()

    cursor.execute("""

    SELECT COUNT(*)

    FROM pickup_requests

    WHERE

    user_id=%s

    AND status='Completed'

    """, (user_id,))

    completed_pickups = cursor.fetchone()[0]

    # PRE-CHECK ELIGIBILITY

    if completed_pickups >= 5:

        eligibility_status = "Eligible"

    else:

        eligibility_status = "Not Eligible"
        
    if request.method == 'POST':


        pickup_reason = request.form['pickup_reason']

        priority_level = request.form['priority_level']

        preferred_date = request.form['preferred_date']

        preferred_time = request.form['preferred_time']

        waste_segregated = request.form['waste_segregated']

        from datetime import datetime

        date_object = datetime.strptime(

        preferred_date,

        '%Y-%m-%d'

        )

        preferred_day = date_object.strftime('%A')



        # ELIGIBILITY CHECK

        if completed_pickups >= 5 and waste_segregated == "Yes":

            eligibility = "Eligible"

        else:

            eligibility = "Not Eligible"


        if eligibility == "Eligible":

            sql = """

            INSERT INTO special_pickup_requests(

            user_id,
            user_name,
            phone,
            area,
            zone,
            pickup_reason,
            priority_level,
            preferred_date,
            preferred_day,
            preferred_time,
            waste_segregated,
            participation_score,
            request_status

            )

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)


            """

            values = (

                user_id,
                user[0],
                user[1],
                area_name,
                user[3],
                pickup_reason,
                priority_level,
                preferred_date,
                preferred_day,
                preferred_time,
                waste_segregated,
                completed_pickups,
                'Pending'

            )

            db.reconnect()

            cursor.execute(sql, values)

            db.commit()

            return """

            <h3 style='text-align:center';
            color:green;
            margin-top:50px;'>

            Special Pickup Request Submitted Successfully

            </h3>

         """

        else:

            return """

            <h3 style='text-align:center;
            color:red;
            margin-top:50px;'>

            You are not eligible for Special Pickup Service.

            <br><br>

            Complete 5 pickups and practice waste segregation.

            </h3>

            """


    return render_template(

        'special_pickup.html',

        user=user,

        area_name=area_name,

        participation_score=completed_pickups,

        eligibility_status=eligibility_status

     )

@app.route('/special_reports')
def special_reports():
# I will delete thses 2 lines if i want 
# (used forpreventing users from opening pages without logging in.)

    if 'user_id' not in session:

        return redirect('/login')
    
    user_id = session['user_id']

    db.reconnect()

    cursor.execute("""

    SELECT

    special_request_id,
    area,
    zone,
    pickup_reason,
    priority_level,
    preferred_day,
    preferred_date,
    preferred_time,
    waste_segregated,
    participation_score,
    request_status,
    request_date


    FROM special_pickup_requests

    WHERE user_id=%s

    ORDER BY special_request_id DESC

    """, (user_id,))

    reports = cursor.fetchall()

    return render_template(

        'special_reports.html',

        reports=reports

    )

@app.route('/view_special_requests')
def view_special_requests():

    if not session.get('admin'):

        return redirect('/')
    
    db.reconnect()

    cursor.execute("""

    SELECT

    special_request_id,
    user_name,
    phone,
    area,
    zone,
    pickup_reason,
    priority_level,
    preferred_day,
    preferred_date,
    preferred_time,
    participation_score,
    waste_segregated,
    request_status,
    request_date


    FROM special_pickup_requests

    ORDER BY special_request_id DESC

    """)

    requests = cursor.fetchall()

    return render_template(

        'view_special_requests.html',

        requests=requests

    )

@app.route('/update_special_request/<int:id>/<status>')
def update_special_request(id, status):

    sql = """

    UPDATE special_pickup_requests

    SET request_status=%s

    WHERE special_request_id=%s

    """

    values = (

        status,
        id

    )

    db.reconnect()

    cursor.execute(sql, values)

    db.commit()

    return redirect('/view_special_requests')

if __name__ == '__main__':
    app.run(debug=True)