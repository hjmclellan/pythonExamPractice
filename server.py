from flask import Flask, render_template, request, redirect, session, flash
from mysqlconn import connectToMySQL
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

app = Flask(__name__)
from flask_bcrypt import Bcrypt        
bcrypt = Bcrypt(app)
app.secret_key = "This code is bananas; BaNaNaS"

def validate_recipe(recipe):
    is_valid= True
    print(recipe)
    if len(recipe['name'])<3:
        is_valid = False
        flash("Recipe name must be at least 3 characters","recipe")
    if len(recipe['description'])<3:
        is_valid = False
        flash("Recipe description must be at least 3 characters","recipe")
    if len(recipe['instructions'])<3:
        is_valid = False
        flash("Recipe instructions must be at least 3 characters","recipe")
    print(is_valid)
    return is_valid

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/create_user',methods=['POST'])
def create_user():
    if len(request.form['fname']) < 2:
        flash("***Please enter a first name***","register")
    if len(request.form['lname']) < 2:
        flash("***Please enter a last name***","register")
    if not EMAIL_REGEX.match(request.form['email']):
        flash("***Invalid email address***")
    if len(request.form['password']) < 8:
        flash("Password must contain at least 8 characters","register")
    if request.form['cpassword'] != request.form['password']:
        flash("Passwords do not match","register")
    if not '_flashes' in session.keys():
        flash("Successfully registered!")
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pass)s, NOW(), NOW());"
        data = {
            'fn': request.form['fname'],
            'ln': request.form['lname'],
            'em': request.form['email'],
            'pass': pw_hash,
        }
        mysql = connectToMySQL('recipes')
        user=mysql.query_db(query, data)
        session['user_id'] = user
        return redirect("/recipes")
    else:
        return redirect('/')

@app.route('/login_user',methods=['POST'])
def login_user():
    query = "SELECT * FROM users WHERE email = %(em)s;"
    data={
        'em': request.form['email']
    }
    mysql = connectToMySQL('recipes')
    result = mysql.query_db(query, data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['user_id'] = result[0]['id']
            print(session['user_id'])
            return redirect('/recipes')
    flash("You could not be logged in","login")
    return redirect("/")

@app.route('/recipes')
def recipes():
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    query = "SELECT * FROM users LEFT JOIN recipes ON users.id = user_id WHERE users.id =  %(id)s;"
    data ={
        'id': session['user_id']
    }
    mysql = connectToMySQL('recipes')
    user=mysql.query_db(query, data)
    print(user)
    return render_template("recipes.html", recipes=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/new')
def new():
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    return render_template("new.html")

@app.route('/create/recipe', methods=['POST'])
def create_recipe():
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')

    if not validate_recipe(request.form):
        return redirect('/new')

    query = "INSERT INTO recipes (name,description,instructions,under_thirty,created_at,updated_at,user_id) VALUES (%(name)s, %(description)s, %(instructions)s, %(under_thirty)s, NOW(), NOW(),%(user_id)s);"
    data = {
        'name': request.form['name'],
        'description': request.form['description'],
        'instructions': request.form['instructions'],
        'under_thirty': request.form['under_thirty'],
        'user_id': session['user_id']
    }
    print(data['user_id'])
    mysql = connectToMySQL('recipes')
    recipe=mysql.query_db(query, data)
    return redirect("/recipes")

@app.route('/show/<int:recipe_id>')
def show_recipe(recipe_id):
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    query = "SELECT * FROM recipes WHERE id =  %(id)s;"
    data ={
        'id': recipe_id
    }
    mysql = connectToMySQL('recipes')
    results=mysql.query_db(query, data)
    return render_template("show.html",recipe=results[0])

@app.route('/edit/<int:recipe_id>')
def edit_recipe(recipe_id):
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    query = "SELECT * FROM recipes WHERE id =  %(id)s;"
    data ={
        'id': recipe_id
    }
    mysql = connectToMySQL('recipes')
    results=mysql.query_db(query, data)
    return render_template("edit.html",recipe=results[0])

@app.route('/delete/<int:recipe_id>')
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    query = "DELETE FROM recipes WHERE id =  %(id)s;"
    data ={
        'id': recipe_id
    }
    mysql = connectToMySQL('recipes')
    results=mysql.query_db(query, data)
    return redirect("/recipes")

@app.route('/update/recipe/<int:recipe_id>',methods=['POST'])
def updated_recipe(recipe_id):
    if 'user_id' not in session:
        flash("Must be logged in to access the requested page :(",'invallogin')
        return redirect ('/')
    if not validate_recipe(request.form):
        return redirect(f"/edit/{recipe_id}")
    query = "UPDATE recipes SET name=%(name)s, description=%(description)s, instructions=%(instructions)s, under_thirty=%(under_thirty)s, user_id=%(user_id)s, updated_at=NOW() WHERE recipes.id = %(id)s;"
    data ={
        'id': recipe_id,
        'name': request.form ['name'],
        'description': request.form['description'],
        'instructions': request.form['instructions'],
        'under_thirty': request.form['under_thirty'],
        'user_id': request.form['user_id']
    }
    mysql = connectToMySQL('recipes')
    results=mysql.query_db(query, data)
    return redirect(f"/show/{recipe_id}")

if __name__=="__main__":
    app.run(debug=True)