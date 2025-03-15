from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import os
import logging
from locale import setlocale, LC_ALL
import locale
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flash messages

# Set locale to Indian English for proper currency formatting
try:
    setlocale(LC_ALL, 'en_IN.UTF-8')
except:
    try:
        setlocale(LC_ALL, 'en_IN')
    except:
        setlocale(LC_ALL, '')  # Fallback to system default

# Database configuration
DATABASE = 'finance.db'

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Custom exceptions
class DatabaseError(Exception):
    pass

class ValidationError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class DateValidationError(Exception):
    pass

def get_db():
    """Get database connection with improved error handling."""
    try:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        return db
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise DatabaseError("Failed to connect to database")

def init_db():
    """Initialize database tables."""
    try:
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise DatabaseError("Failed to initialize database")
    finally:
        db.close()

def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees with proper formatting."""
    try:
        return f"₹{amount:,.2f}"
    except:
        return f"₹{amount:.2f}"

def validate_amount(amount: float) -> float:
    """Validate and format amount to 2 decimal places."""
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN))
    except (ValueError, TypeError):
        raise ValidationError("Invalid amount format")

def validate_date(date_str: str) -> datetime:
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")

def get_total_allocations() -> float:
    """Calculate total allocations (expenses + investments + budgets)."""
    try:
        db = get_db()
        expenses = db.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses').fetchone()[0]
        investments = db.execute('SELECT COALESCE(SUM(amount), 0) FROM investments').fetchone()[0]
        budgets = db.execute('SELECT COALESCE(SUM(amount), 0) FROM budget').fetchone()[0]
        return expenses + investments + budgets
    except Exception as e:
        logger.error(f"Error calculating total allocations: {str(e)}")
        raise DatabaseError("Failed to calculate total allocations")
    finally:
        db.close()

def check_income_set() -> float:
    """Check if income is set and return the latest income."""
    try:
        db = get_db()
        income = db.execute('SELECT amount FROM income ORDER BY date DESC LIMIT 1').fetchone()
        if not income:
            raise ValidationError("Please set your income first")
        return income[0]
    finally:
        db.close()

def handle_database_error(f):
    """Decorator to handle database errors with improved error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            flash(str(e), "warning")
            return render_template('error.html', error=str(e)), 400
        except InsufficientFundsError as e:
            logger.warning(f"Insufficient funds error in {f.__name__}: {str(e)}")
            flash(str(e), "warning")
            return render_template('error.html', error=str(e)), 400
        except DatabaseError as e:
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            flash("A database error occurred. Please try again.", "error")
            return render_template('error.html', error="Database error occurred"), 500
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            flash("An unexpected error occurred. Please try again.", "error")
            return render_template('error.html', error="Unexpected error occurred"), 500
    return decorated_function

# Routes with improved error handling
@app.route('/')
def home():
    """Home route that renders dashboard directly instead of redirecting."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@handle_database_error
def dashboard():
    """Main dashboard view with improved error handling."""
    db = None
    try:
        db = get_db()
        
        # Get latest income with proper error handling
        income = db.execute('SELECT amount FROM income ORDER BY date DESC LIMIT 1').fetchone()
        total_income = income[0] if income else 0

        # Get total expenses with error handling
        try:
            expenses = db.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses').fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching expenses: {str(e)}")
            expenses = 0

        # Get total investments with error handling
        try:
            investments = db.execute('SELECT COALESCE(SUM(amount), 0) FROM investments').fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching investments: {str(e)}")
            investments = 0

        # Get savings goal with error handling
        try:
            savings_goal = db.execute('SELECT amount FROM savings_goals ORDER BY date DESC LIMIT 1').fetchone()
            savings_target = savings_goal[0] if savings_goal else 0
        except Exception as e:
            logger.error(f"Error fetching savings goal: {str(e)}")
            savings_target = 0

        # Calculate savings
        savings = total_income - expenses

        # Get recent transactions with error handling
        try:
            recent_expenses = db.execute('''
                SELECT amount, category, description, date 
                FROM expenses 
                ORDER BY date DESC LIMIT 5
            ''').fetchall()
        except Exception as e:
            logger.error(f"Error fetching recent expenses: {str(e)}")
            recent_expenses = []

        try:
            recent_investments = db.execute('''
                SELECT amount, type, date 
                FROM investments 
                ORDER BY date DESC LIMIT 5
            ''').fetchall()
        except Exception as e:
            logger.error(f"Error fetching recent investments: {str(e)}")
            recent_investments = []

        # Get budget overview with error handling
        try:
            budgets = db.execute('''
                SELECT category, amount 
                FROM budget 
                ORDER BY category
            ''').fetchall()
            
            budget_data = []
            for budget in budgets:
                try:
                    spent = db.execute('''
                        SELECT COALESCE(SUM(amount), 0) 
                        FROM expenses 
                        WHERE category = ?
                    ''', (budget['category'],)).fetchone()[0]
                    
                    budget_data.append({
                        'category': budget['category'],
                        'total': budget['amount'],
                        'spent': spent,
                        'remaining': budget['amount'] - spent,
                        'percentage': (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
                    })
                except Exception as e:
                    logger.error(f"Error processing budget {budget['category']}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching budgets: {str(e)}")
            budget_data = []

        return render_template('index.html',
                             total_income=format_currency(total_income),
                             total_expenses=format_currency(expenses),
                             total_investments=format_currency(investments),
                             savings=format_currency(savings),
                             savings_target=format_currency(savings_target),
                             recent_expenses=[(e, format_currency(e['amount'])) for e in recent_expenses],
                             recent_investments=[(i, format_currency(i['amount'])) for i in recent_investments],
                             budget_data=budget_data,
                             has_income=income is not None)
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        flash("An error occurred while loading the dashboard.", "error")
        return render_template('error.html', error="Failed to load dashboard"), 500
    finally:
        if db:
            db.close()

@app.route('/set_income', methods=['GET', 'POST'])
@handle_database_error
def set_income():
    if request.method == 'POST':
        amount = validate_amount(float(request.form['amount']))
        
        # Check if new income would be less than current allocations
        current_allocations = get_total_allocations()
        
        if amount < current_allocations:
            raise InsufficientFundsError("New income cannot be less than current allocations")
        
        db = get_db()
        try:
            db.execute('INSERT INTO income (amount, date) VALUES (?, ?)',
                      (amount, datetime.utcnow()))
            db.commit()
            flash("Income set successfully", "success")
            return redirect(url_for('dashboard'))
        finally:
            db.close()
    
    return render_template('set_income.html')

@app.route('/set_budget', methods=['GET', 'POST'])
@handle_database_error
def set_budget():
    if request.method == 'POST':
        amount = validate_amount(float(request.form['amount']))
        category = request.form['category'].strip()
        
        if not category:
            raise ValidationError("Category cannot be empty")
        
        # Check if budget exceeds available funds
        income = check_income_set()
        current_allocations = get_total_allocations()
        
        if current_allocations + amount > income:
            raise InsufficientFundsError("Total allocations cannot exceed your income")
        
        # Check if category already has a budget
        db = get_db()
        try:
            existing = db.execute('SELECT 1 FROM budget WHERE category = ?', (category,)).fetchone()
            if existing:
                raise ValidationError(f"Budget already exists for category: {category}")
            
            db.execute('INSERT INTO budget (amount, category, date) VALUES (?, ?, ?)',
                      (amount, category, datetime.utcnow()))
            db.commit()
            flash("Budget set successfully", "success")
            return redirect(url_for('dashboard'))
        finally:
            db.close()
    
    # Check if income is set
    db = get_db()
    try:
        if not db.execute('SELECT 1 FROM income LIMIT 1').fetchone():
            flash("Please set your income first", "error")
            return redirect(url_for('set_income'))
    finally:
        db.close()
    
    return render_template('set_budget.html')

@app.route('/set_savings_goal', methods=['GET', 'POST'])
@handle_database_error
def set_savings_goal():
    if request.method == 'POST':
        amount = validate_amount(float(request.form['amount']))
        target_date = validate_date(request.form['target_date'])
        
        # Check if savings goal exceeds available funds
        income = check_income_set()
        current_allocations = get_total_allocations()
        
        if current_allocations + amount > income:
            raise InsufficientFundsError("Total allocations cannot exceed your income")
        
        # Check if target date is too far in the future
        if target_date > datetime.now() + timedelta(days=5*365):
            raise DateValidationError("Target date cannot be more than 5 years in the future")
        
        db = get_db()
        try:
            db.execute('INSERT INTO savings_goals (amount, target_date, date) VALUES (?, ?, ?)',
                      (amount, target_date, datetime.utcnow()))
            db.commit()
            flash("Savings goal set successfully", "success")
            return redirect(url_for('dashboard'))
        finally:
            db.close()
    
    # Check if income is set
    db = get_db()
    try:
        if not db.execute('SELECT 1 FROM income LIMIT 1').fetchone():
            flash("Please set your income first", "error")
            return redirect(url_for('set_income'))
    finally:
        db.close()
    
    return render_template('set_savings_goal.html')

@app.route('/add_expense', methods=['GET', 'POST'])
@handle_database_error
def add_expense():
    if request.method == 'POST':
        amount = validate_amount(float(request.form['amount']))
        category = request.form['category'].strip()
        description = request.form['description'].strip()
        
        if not category:
            raise ValidationError("Category cannot be empty")
        
        # Check if expense exceeds available funds
        income = check_income_set()
        current_allocations = get_total_allocations()
        
        if current_allocations + amount > income:
            raise InsufficientFundsError("Total allocations cannot exceed your income")
        
        db = get_db()
        try:
            # Check if expense exceeds budget for category
            budget = db.execute('SELECT amount FROM budget WHERE category = ?', (category,)).fetchone()
            if budget:
                category_expenses = db.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE category = ?
                ''', (category,)).fetchone()[0]
                if category_expenses + amount > budget[0]:
                    raise InsufficientFundsError(f"Expense exceeds budget for category: {category}")
            
            db.execute('''
                INSERT INTO expenses (amount, category, description, date) 
                VALUES (?, ?, ?, ?)
            ''', (amount, category, description, datetime.utcnow()))
            db.commit()
            flash("Expense added successfully", "success")
            return redirect(url_for('dashboard'))
        finally:
            db.close()
    
    # Check if income is set
    db = get_db()
    try:
        if not db.execute('SELECT 1 FROM income LIMIT 1').fetchone():
            flash("Please set your income first", "error")
            return redirect(url_for('set_income'))
    finally:
        db.close()
    
    return render_template('add_expense.html')

@app.route('/add_investment', methods=['GET', 'POST'])
@handle_database_error
def add_investment():
    if request.method == 'POST':
        amount = validate_amount(float(request.form['amount']))
        type = request.form['type'].strip()
        
        if not type:
            raise ValidationError("Investment type cannot be empty")
        
        # Check if investment exceeds available funds
        income = check_income_set()
        current_allocations = get_total_allocations()
        
        if current_allocations + amount > income:
            raise InsufficientFundsError("Total allocations cannot exceed your income")
        
        # Check if investment type is valid
        valid_types = ["Stocks", "Bonds", "Mutual Funds", "Real Estate", "Other"]
        if type not in valid_types:
            raise ValidationError(f"Invalid investment type. Must be one of: {', '.join(valid_types)}")
        
        db = get_db()
        try:
            db.execute('INSERT INTO investments (amount, type, date) VALUES (?, ?, ?)',
                      (amount, type, datetime.utcnow()))
            db.commit()
            flash("Investment added successfully", "success")
            return redirect(url_for('dashboard'))
        finally:
            db.close()
    
    # Check if income is set
    db = get_db()
    try:
        if not db.execute('SELECT 1 FROM income LIMIT 1').fetchone():
            flash("Please set your income first", "error")
            return redirect(url_for('set_income'))
    finally:
        db.close()
    
    return render_template('add_investment.html')

@app.route('/api/expenses')
@handle_database_error
def get_expenses():
    db = get_db()
    try:
        expenses = db.execute('''
            SELECT amount, category, description, date 
            FROM expenses 
            ORDER BY date DESC
        ''').fetchall()
        return jsonify([{
            "amount": format_currency(expense['amount']),
            "category": expense['category'],
            "description": expense['description'],
            "date": expense['date']
        } for expense in expenses])
    finally:
        db.close()

@app.route('/api/investments')
@handle_database_error
def get_investments():
    db = get_db()
    try:
        investments = db.execute('''
            SELECT amount, type, date 
            FROM investments 
            ORDER BY date DESC
        ''').fetchall()
        return jsonify([{
            "amount": format_currency(investment['amount']),
            "type": investment['type'],
            "date": investment['date']
        } for investment in investments])
    finally:
        db.close()

@app.route('/clear_all', methods=['POST'])
@handle_database_error
def clear_all():
    """Clear all financial data from the database."""
    db = get_db()
    try:
        db.execute('DELETE FROM income')
        db.execute('DELETE FROM expenses')
        db.execute('DELETE FROM investments')
        db.execute('DELETE FROM budget')
        db.execute('DELETE FROM savings_goals')
        db.commit()
        flash("All data has been cleared successfully", "success")
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing data: {str(e)}")
        flash("Failed to clear data", "error")
    finally:
        db.close()
    return redirect(url_for('dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(ValidationError)
def validation_error(error):
    flash(str(error), "error")
    return redirect(url_for('dashboard'))

@app.errorhandler(InsufficientFundsError)
def insufficient_funds_error(error):
    flash(str(error), "error")
    return redirect(url_for('dashboard'))

@app.errorhandler(DateValidationError)
def date_validation_error(error):
    flash(str(error), "error")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE):
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    # Try ports in sequence until one works
    ports = [3000, 3001, 3002, 3003, 3004, 3005]
    
    for port in ports:
        try:
            app.run(debug=True, port=port)
            break
        except OSError as e:
            if port == ports[-1]:
                print(f"Could not find an available port in range {ports[0]}-{ports[-1]}")
                raise e
            print(f"Port {port} is in use, trying next port...")
            continue
