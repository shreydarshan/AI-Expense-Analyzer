from flask import Flask, render_template, request, redirect
import sqlite3
import pandas as pd

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  amount REAL,
                  category TEXT,
                  date TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    total = df['amount'].sum() if not df.empty else 0
    category_data = df.groupby('category')['amount'].sum().to_dict() if not df.empty else {}
    insights = generate_insights(df)

    return render_template('index.html',
                           expenses=df.to_dict('records'),
                           total=total,
                           category_data=category_data,
                           insights=insights)

@app.route('/add', methods=['POST'])
def add():
    amount = request.form['amount']
    category = request.form['category']
    date = request.form['date']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
              (amount, category, date))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

def generate_insights(df):
    if df.empty:
        return ["Start adding expenses to see insights"]

    insights = []
    total = df['amount'].sum()
    category_sum = df.groupby('category')['amount'].sum()

    top_category = category_sum.idxmax()
    insights.append(f"Highest spending category: {top_category}")

    for cat, val in category_sum.items():
        percent = (val / total) * 100
        if percent > 40:
            insights.append(f"{cat} takes {percent:.1f}% of your spending")

    if total > 10000:
        insights.append("Spending is high this month, consider reducing costs")
    elif total < 2000:
        insights.append("Great control over spending, keep it up")

    if len(category_sum) >= 4:
        insights.append("Spending is spread across multiple categories")

    return insights

if __name__ == '__main__':
    app.run(debug=True)