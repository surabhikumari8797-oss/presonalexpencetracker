from flask import Flask, request, redirect, render_template_string
import pandas as pd
import numpy as np
import os
import json
from datetime import date

app = Flask(__name__)

FILE = "expenses.csv"
BUDGET_FILE = "budget.txt"

COLUMNS = ["Amount", "Category", "Bill Type", "Date", "Description"]

# Load existing expense data
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS]
else:
    df = pd.DataFrame(columns=COLUMNS)

df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df = df.fillna("")


def save_data():
    df.to_csv(FILE, index=False)


def read_budget():
    try:
        with open(BUDGET_FILE, "r") as f:
            return float(f.read())
    except (OSError, ValueError):
        return 0.0


budget = read_budget()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Personal Expense Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef2f7;
            margin: 0;
            padding: 24px;
            color: #23395d;
        }
        .container {
            max-width: 1100px;
            margin: auto;
        }
        h1 { text-align: center; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin: 20px 0;
        }
        .card, .panel {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 3px 12px #0000000d;
        }
        .card h3 { font-size: 14px; color: #667085; }
        .card p { font-size: 23px; font-weight: bold; }
        form { margin-bottom: 15px; }
        input, select, button {
            padding: 10px;
            margin: 5px 3px;
            border: 1px solid #ccd3df;
            border-radius: 6px;
        }
        button {
            background: #315caa;
            color: white;
            cursor: pointer;
            border: none;
        }
        .delete { background: #c0392b; }
        .add { background: #25855a; }
        .warning { color: #c0392b; font-weight: bold; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            border-bottom: 1px solid #e5e7eb;
            padding: 11px;
            text-align: left;
        }
        th { background: #e1e9f5; }
        .table-wrap { overflow-x: auto; }
        .chart { max-width: 450px; margin: 25px auto; }
        @media (max-width: 600px) {
            body { padding: 10px; }
            input, select { max-width: 90%; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Personal Expense Tracker</h1>
    <p style="text-align:center">Manage your daily expenses</p>

    <div class="cards">
        <div class="card">
            <h3>Total Expenses</h3>
            <p>₹{{ "%.2f"|format(total) }}</p>
        </div>
        <div class="card">
            <h3>Average Expense</h3>
            <p>₹{{ "%.2f"|format(average) }}</p>
        </div>
        <div class="card">
            <h3>Highest Expense</h3>
            <p>₹{{ "%.2f"|format(highest) }}</p>
        </div>
        <div class="card">
            <h3>Remaining Budget</h3>
            <p>₹{{ "%.2f"|format(budget-total) }}</p>
        </div>
    </div>

    {% if budget > 0 and total >= budget %}
        <p class="warning">Your budget has been reached!</p>
    {% elif budget > 0 and total >= budget * 0.8 %}
        <p class="warning">Warning: 80% of your budget has been used.</p>
    {% endif %}

    <div class="panel">
        <h2>Add Expense</h2>
        <form action="/add" method="post">
            <input type="number" name="amount" step="0.01"
                   min="0.01" placeholder="Amount (₹)" required>

            <select name="category" id="category"
                    onchange="toggleBill()" required>
                <option>Food</option>
                <option>Travel</option>
                <option>Shopping</option>
                <option>Education</option>
                <option>Bills</option>
                <option>Other</option>
            </select>

            <select name="bill_type" id="bill_type" disabled>
                <option value="">Select bill type</option>
                <option>Electricity</option>
                <option>Water</option>
                <option>Mobile Recharge</option>
                <option>Internet/Wi-Fi</option>
                <option>Gas Cylinder</option>
                <option>Rent</option>
                <option>DTH/Cable</option>
                <option>Subscription</option>
                <option>Maintenance</option>
                <option>Other Bill</option>
            </select>

            <input type="date" name="expense_date"
                   value="{{ today }}" required>

            <input type="text" name="description"
                   placeholder="Description">

            <button class="add" type="submit">Add Expense</button>
        </form>

        <script>
        function toggleBill() {
            const category = document.getElementById("category").value;
            const bill = document.getElementById("bill_type");
            bill.disabled = category !== "Bills";
            bill.required = category === "Bills";
            if (category !== "Bills") bill.value = "";
        }
        </script>
    </div>

    <div class="panel">
        <h2>Monthly Budget</h2>
        <form action="/budget" method="post">
            <input type="number" name="budget" min="0.01"
                   step="0.01" placeholder="Enter monthly budget"
                   value="{{ budget if budget else '' }}" required>
            <button type="submit">Set Budget</button>
        </form>
    </div>

    <div class="panel">
        <h2>Search and Filter</h2>
        <form action="/" method="get">
            <input name="search" placeholder="Search category or description"
                   value="{{ search }}">
            <input type="month" name="month" value="{{ month }}">
            <button type="submit">Apply Filter</button>
            <a href="/" style="margin-left:8px">Show All</a>
        </form>

        <div class="table-wrap">
        <table>
            <thead>
            <tr>
                <th>Amount</th>
                <th>Category</th>
                <th>Bill Type</th>
                <th>Date</th>
                <th>Description</th>
                <th>Action</th>
            </tr>
            </thead>
            <tbody>
            {% for row in records %}
            <tr>
                <td>₹{{ row.Amount }}</td>
                <td>{{ row.Category }}</td>
                <td>{{ row["Bill Type"] }}</td>
                <td>{{ row.Date }}</td>
                <td>{{ row.Description }}</td>
                <td>
                    <form action="/delete/{{ row.idx }}" method="post"
                          onsubmit="return confirm('Delete this expense?')">
                        <button class="delete" type="submit">Delete</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6">No expenses found.</td></tr>
            {% endfor %}
            </tbody>
        </table>
        </div>
    </div>

    <div class="panel">
        <h2>Category-wise Expense Chart</h2>
        <div class="chart">
            <canvas id="expenseChart"></canvas>
        </div>
    </div>
</div>

<script>
const labels = {{ chart_labels|safe }};
const values = {{ chart_values|safe }};

if (labels.length > 0) {
    new Chart(document.getElementById("expenseChart"), {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{ data: values }]
        },
        options: { responsive: true }
    });
}
</script>
</body>
</html>
"""


@app.route("/")
def home():
    search = request.args.get("search", "").strip()
    month = request.args.get("month", "").strip()

    view = df.copy()

    if search:
        mask = (
            view["Category"].astype(str).str.contains(
                search, case=False, na=False
            )
            | view["Bill Type"].astype(str).str.contains(
                search, case=False, na=False
            )
            | view["Description"].astype(str).str.contains(
                search, case=False, na=False
            )
        )
        view = view[mask]

    if month:
        view = view[view["Date"].astype(str).str.startswith(month)]

    # NumPy calculations for the selected month or filtered records
    amounts = view["Amount"].to_numpy(dtype=float)
    total = float(np.sum(amounts)) if len(amounts) else 0.0
    average = float(np.mean(amounts)) if len(amounts) else 0.0
    highest = float(np.max(amounts)) if len(amounts) else 0.0

    # Chart uses the currently filtered records
    chart = view.groupby("Category")["Amount"].sum()

    records = []
    for idx, row in view.iterrows():
        item = row.to_dict()
        item["idx"] = int(idx)
        records.append(item)

    return render_template_string(
        HTML,
        records=records,
        total=total,
        average=average,
        highest=highest,
        budget=budget,
        today=date.today().isoformat(),
        search=search,
        month=month,
        chart_labels=json.dumps(chart.index.tolist()),
        chart_values=json.dumps(chart.tolist())
    )


@app.route("/add", methods=["POST"])
def add_expense():
    global df

    try:
        amount = float(request.form["amount"])
        category = request.form["category"]
        bill_type = request.form.get("bill_type", "")
        expense_date = request.form["expense_date"]
        description = request.form.get("description", "").strip()

        if amount <= 0:
            return "Amount must be greater than zero.", 400

        date.fromisoformat(expense_date)

        allowed_categories = [
            "Food", "Travel", "Shopping", "Education", "Bills", "Other"
        ]
        if category not in allowed_categories:
            return "Invalid category.", 400

        if category != "Bills":
            bill_type = ""

        new_row = pd.DataFrame([{
            "Amount": amount,
            "Category": category,
            "Bill Type": bill_type,
            "Date": expense_date,
            "Description": description
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        save_data()

        return redirect("/")

    except (ValueError, KeyError):
        return "Please enter a valid amount and date.", 400


@app.route("/delete/<int:idx>", methods=["POST"])
def delete_expense(idx):
    global df

    if idx not in df.index:
        return "Expense not found.", 404

    df = df.drop(index=idx).reset_index(drop=True)
    save_data()
    return redirect("/")


@app.route("/budget", methods=["POST"])
def set_budget():
    global budget

    try:
        value = float(request.form["budget"])
        if value <= 0:
            return "Budget must be greater than zero.", 400

        budget = value

        with open(BUDGET_FILE, "w") as f:
            f.write(str(budget))

        return redirect("/")

    except (ValueError, KeyError):
        return "Please enter a valid budget.", 400


if __name__ == "__main__":
    app.run(debug=True)
