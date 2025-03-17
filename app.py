from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = 'users.json'
BOOKS_FILE = 'books.json'
TRANSACTIONS_FILE='transactions.json'
ISSUES_FILE='issues.json'
MEMBERSHIP_FILE='membership.json'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return [] if file_path == BOOKS_FILE else {}

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def initialize_books():
    if not os.path.exists(BOOKS_FILE):
        books = [
            {'id': 1, 'title': 'Python Programming', 'author': 'John Doe', 'available': True},
            {'id': 2, 'title': 'Flask Web Development', 'author': 'Jane Smith', 'available': True}
        ]
        save_json(books, BOOKS_FILE)

def initialize_users():
    if not os.path.exists(USERS_FILE):
        users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'user': {'password': 'user123', 'role': 'user'}
        }
        save_json(users, USERS_FILE)

def initialize_issues():
    if not os.path.exists(ISSUES_FILE):
        with open(ISSUES_FILE, 'w') as file:
            json.dump([], file)

def initialize_transactions():
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w') as file:
            json.dump([], file)
initialize_users()
initialize_books()
initialize_issues()
initialize_transactions()
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_json(USERS_FILE)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session['role'])

@app.route('/books', methods=['GET', 'POST'])
def books():
    books = load_json(BOOKS_FILE)
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        if not title and not author:
            flash('Please enter a book title or select an author.', 'danger')
        else:
            filtered_books = [book for book in books if (title and book['title'] == title) or (author and book['author'] == author)]
            return render_template('books.html', books=filtered_books)
    return render_template('books.html', books=books)

##issue
@app.route('/issue-book', methods=['GET', 'POST'])
def issue_book():
    # Check if the user is logged in and has the correct role (user or admin)
    if 'username' not in session or (session.get('role') not in ['user', 'admin']):
        return redirect(url_for('login'))  # Redirect to login page if not logged in or not authorized

    # Current date and return date calculation
    today_date = datetime.today().strftime('%Y-%m-%d')
    return_date = (datetime.today() + timedelta(days=15)).strftime('%Y-%m-%d')

    # Load the books data from the JSON file
    with open('books.json', 'r') as file:
        try:
            books_data = json.load(file)
        except:
            error="no issued books"
    
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        author_name = request.form.get('author_name')
        issue_date = request.form.get('issue_date')
        return_date_input = request.form.get('return_date')
        remarks = request.form.get('remarks')

        # Check if the book exists in the database (JSON)
        book = next((b for b in books_data if b['title'].lower() == book_name.lower()), None)

        if not book:
            error = "The book name does not exist in our database."
            return render_template('issue.html', today_date=today_date, return_date=return_date, error=error)

        # Ensure the author name matches the book (non-editable field)
        if author_name != book['author']:
            error = "Author name doesn't match the selected book."
            return render_template('issue.html', today_date=today_date, return_date=return_date, error=error)

        # Ensure the book is available
        if not book['available']:
            error = "The selected book is currently not available."
            return render_template('issue.html', today_date=today_date, return_date=return_date, error=error)

        # Validate Issue Date (cannot be before today)
        if datetime.strptime(issue_date, '%Y-%m-%d') < datetime.today():
            error = "The issue date cannot be before today."
            return render_template('issue.html', today_date=today_date, return_date=return_date, error=error)

        # Validate Return Date (cannot be more than 15 days from today)
        if datetime.strptime(return_date_input, '%Y-%m-%d') > datetime.strptime(return_date, '%Y-%m-%d'):
            error = "The return date cannot be more than 15 days from today."
            return render_template('issue.html', today_date=today_date, return_date=return_date, error=error)

        # If everything is valid, process the data and create an issue entry
        # Generate a new issue ID (increment the highest existing ID)
        with open('issues.json', 'r') as issue_file:
            issues_data = json.load(issue_file)

        new_issue_id = max([issue['id'] for issue in issues_data], default=0) + 1

        # Create a new issue entry
        new_issue = {
            "id": new_issue_id,
            "username": session['username'],
            "book_title": book['title'],
            "author": book['author'],
            "issue_date": issue_date,
            "return_date": return_date_input,
            "remarks": remarks if remarks else "",
            "status": "issued"
        }

        # Add the new issue to the issues database (issues.json)
        issues_data.append(new_issue)

        with open('issues.json', 'w') as issue_file:
            json.dump(issues_data, issue_file, indent=4)

        # Mark the book as unavailable in books.json
        book['available'] = False
        with open('books.json', 'w') as file:
            json.dump(books_data, file, indent=4)

        return redirect(url_for('success_page'))  # Redirect to success page

    return render_template('issue.html', today_date=today_date, return_date=return_date)
##return 

def read_issues():
    try:
        with open(ISSUES_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to update the issues JSON file
def update_issues(issues):
    with open(ISSUES_FILE, 'w') as file:
        json.dump(issues, file, indent=4)

# Return book route
@app.route('/return-book', methods=['GET', 'POST'])
def return_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Load the list of issued books
    try:
        issued_books = read_issues()
    except:
        flash("No issued books found.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        book_id = request.form['book_id']  # Get the book ID from the form
        serial_no = request.form['serial_no']  # Get the serial number from the form
        return_date_input = request.form['return_date']  # Get the return date from the form
        remarks = request.form.get('remarks', '')  # Get remarks, if any

        # Search for the book issue by the logged-in user
        book_to_return = None
        for book in issued_books:
            if book['username'] == session['username'] and str(book['id']) == str(book_id):
                book_to_return = book
                break

        if not book_to_return:
            return "No book found with that ID for the current user."

        # Handle the fine logic
        fine = 0
        if 'fine' in book_to_return and book_to_return['fine'] > 0:
            fine = book_to_return['fine']
            if not request.form.get('pay_fine', False):
                return "Please pay the fine before returning the book."

        # Update the book issue status to 'returned' and set return date
        book_to_return['status'] = 'returned'
        book_to_return['return_date'] = return_date_input
        book_to_return['remarks'] = remarks

        # Add the fine details if applicable
        if fine > 0 and request.form.get('pay_fine', False):
            book_to_return['fine'] = fine  # Add fine if paid

        # Update the issues list in the JSON file
        update_issues(issued_books)

        # Redirect to the payment page if fine is pending
        if fine > 0:
            return redirect(url_for('pay_fine', fine=fine))  # Adjust this URL as per your routing for payment page

        return "Book returned successfully."

    # Get the list of books issued to the logged-in user
    user_books = [book for book in issued_books if book['username'] == session['username']]
    
    return render_template('return_book.html', user_books=user_books)

####################### **membership**
def read_memberships():
    try:
        with open('MEMBERSHIP_FILE', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to write memberships to the JSON file
def update_memberships(memberships):
    with open('MEMBERSHIP_FILE', 'w') as file:
        json.dump(memberships, file, indent=4)

# Function to write transactions to the JSON file
def update_transactions(transaction):
    try:
        with open(TRANSACTIONS_FILE, 'r') as file:
            transactions = json.load(file)
    except FileNotFoundError:
        transactions = []

    transactions.append(transaction)

    with open(TRANSACTIONS_FILE, 'w') as file:
        json.dump(transactions, file, indent=4)

# Membership route
@app.route('/membership', methods=['GET', 'POST'])
def membership():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form['action']
        
        # Add Membership
        if action == 'add':
            membership_type = request.form['membership_type']
            membership_number = f"{session['username']}-{membership_type}-{len(read_memberships()) + 1}"  # Generate a unique membership number
            new_membership = {
                "membership_number": membership_number,
                "username": session['username'],
                "membership_type": membership_type,
                "status": "active"
            }

            # Add the new membership
            memberships = read_memberships()
            memberships.append(new_membership)
            update_memberships(memberships)

            # Log this in transactions
            transaction = {
                "username": session['username'],
                "action": "Added Membership",
                "membership_number": membership_number,
                "membership_type": membership_type
            }
            update_transactions(transaction)

        # Update Membership
        elif action == 'update':
            membership_number = request.form['membership_number']
            memberships = read_memberships()

            # Find the membership based on the membership number
            membership_to_update = None
            for membership in memberships:
                if membership['membership_number'] == membership_number and membership['username'] == session['username']:
                    membership_to_update = membership
                    break

            if membership_to_update:
                if request.form.get('cancel') == 'yes':
                    # Cancel the membership
                    memberships.remove(membership_to_update)
                    update_memberships(memberships)

                    # Log the cancellation in transactions
                    transaction = {
                        "username": session['username'],
                        "action": "Cancelled Membership",
                        "membership_number": membership_number
                    }
                    update_transactions(transaction)
                else:
                    # Extend the membership
                    extend_type = request.form['extend']
                    membership_to_update['membership_type'] = extend_type
                    update_memberships(memberships)

                    # Log the extension in transactions
                    transaction = {
                        "username": session['username'],
                        "action": f"Extended Membership by {extend_type}",
                        "membership_number": membership_number
                    }
                    update_transactions(transaction)

        return redirect(url_for('membership'))

    return render_template('membership.html')

#########
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
