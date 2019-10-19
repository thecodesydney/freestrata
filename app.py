from flask import Flask, render_template, g, request, redirect, url_for,session
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os


# settingup the app
app = Flask(__name__)


# config
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.urandom(24)

# MYSQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '12er34ty'
app.config['MYSQL_DATABASE_DB'] = 'strata'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

flaskmysql = MySQL()
flaskmysql.init_app(app)


def connect_db(flaskmysql):
    """
    connecting to the database
    :param flaskmysql:
    :return:
    """
    con = flaskmysql.connect()
    return con


def get_db(flaskmysql):
    if not hasattr(g,'mysql_db'):
        g.mysql_db = connect_db(flaskmysql)
    return g.mysql_db


@app.teardown_appcontext
def close_db(error):
    """
    dissconnecting the database
    :param error:
    :return:
    """
    if hasattr(g, 'mysql_db'):
        g.mysql_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    print("hello")
    db = get_db(flaskmysql)
    cur = db.cursor()
    cur.execute("Select * from issues")
    results = cur.fetchall()

    return render_template('index.html',result=results,)


@app.route('/unit_login',methods = ['GET', 'POST'])
def unit_login():
    if 'unit' in session:
        return redirect(url_for('issues'))

    if request.method == 'GET':
        return render_template("unit_login.html")

    else:
        unit = request.form['unit']
        print("hello1")
        # calling database and select query to determine whether there is unit or not
        db = get_db(flaskmysql)
        cr = db.cursor()
        cr.execute("select * from unit where unit_no = %s ", [unit])
        result = cr.fetchone()
        if result and 'unit' not in session:
            session['unit'] = unit
            return redirect(url_for('issues'))
        else:
            return "no valid unit"

    
@app.route('/stat')
def stat():
    if 'unit' in session:
        db = get_db(flaskmysql)
        cur = db.cursor()
        cur.execute('select * from issues')
        result = cur.fetchall()
        td = 0
        ip = 0
        done = 0
        for x in result:
            print(x)
            if x[3] == 0:
                td = td +1
            elif x[3] == 1:
                ip = ip +1
            else :
                done = done+1

        return render_template('stat.html',unit=session['unit'], td=td, ip=ip, done=done)
    else:
        return redirect('/')


@app.route('/logout')
def logout():
    if 'unit' not in session:
        return redirect(url_for('index'))

    session.pop('unit')
    return redirect(url_for('index'))

@app.route('/issues')
def issues():
    """
    index page with list of the issues
    :return:
    """

    if 'unit' not in session:
        return redirect(url_for('index'))
    # Getting data from database
    db = get_db(flaskmysql)
    cur = db.cursor()
    cur.execute("Select * from issues")
    results = cur.fetchall()
    print(results)
    return render_template('issues.html',unit=int(session['unit']), result = results)


@app.route('/new', methods=['GET','POST'])
def new_issue():
    """
    Create a new issue
    :return:
    """
    if 'unit' not in session:
        return redirect(url_for('unit_login'))
    #connecting to db
    db = get_db(flaskmysql)
    cur = db.cursor()
    if request.method == 'GET':
        return render_template('new_issue.html', unit=session['unit'])

    des = request.form['description']

    cur.execute("insert into issues (issue_description,unit) values (%s,%s) ", (des,session['unit']))
    db.commit()

    return redirect(url_for('issues'))



@app.route('/edit/<id>',methods = ['POST','GET'])
def edit(id):
    """
    edit the issue
    :param id:
    :return: edit or index page
    """
    if 'unit' not in session:
        return redirect(url_for('index'))
    db = get_db(flaskmysql)
    cur = db.cursor()

    if request.method == 'GET':
        cur.execute("select * from issues where issue_number = %s ", [id])
        result = cur.fetchone()
        return render_template('edit.html', result=result)

    else:
        des = request.form['description']
        cur.execute("update issues set issue_description = %s where issue_number = %s",[des,id])
        db.commit()
        return redirect(url_for('index'))


@app.route('/admin', methods=['POST', 'GET'])
def admin_login():
    error = None
    if request.method == 'POST':
        db = get_db(flaskmysql)
        cur = db.cursor()
        cur.execute("select * from users where email = %s", [request.form['email']])
        result = cur.fetchone()

        # checking the login detail
        if result and check_password_hash(result[2], request.form['pass']):
            session['user'] = result[1]
            session['admin'] = result[3]
            session['unit'] = -1
            return redirect(url_for('stat'))

            return render_template('issues.html', unit=session['unit'])
        else:
            error = "Login information Not Correct"

    return render_template('login.html', error=error)


def get_current_user():
    """
    gets the current user if there is
    :return:
    """
    if 'user' in session:
        db = get_db(flaskmysql)
        cur = db.cursor()
        cur.execute("select * from users where email = %s", [session['user']])
        result = cur.fetchone()
        return result
    return None

@app.route('/deleteissue/<id>')
def delete_issue(id):
    """
    deleting issue
    :param id:
    :return:
    """
    # verifing session
    user_result = get_current_user()
    if user_result is None:
        print('none')
        return redirect(url_for('login'))

    db = get_db(flaskmysql)
    cur = db.cursor()
    cur.execute('delete from issues where issue_number = %s',[id])
    db.commit()
    return redirect(url_for('issues'))


@app.route('/admin_dash')
def admin_dash():
    return "this is admin dash"

if __name__ == '__main__':
    app.run()