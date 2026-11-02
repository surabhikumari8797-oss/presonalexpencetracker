
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
import os

FILE = "expenses.csv"
BUDGET_FILE = "budget.txt"

COLUMNS = ["Amount", "Category", "Bill Type", "Date", "Description"]

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS]
else:
    df = pd.DataFrame(columns=COLUMNS)

df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df["Category"] = df["Category"].fillna("")
df["Bill Type"] = df["Bill Type"].fillna("")
df["Date"] = df["Date"].fillna("")
df["Description"] = df["Description"].fillna("")

budget = 0.0
if os.path.exists(BUDGET_FILE):
    try:
        with open(BUDGET_FILE, "r") as f:
            budget = float(f.read().strip())
    except (ValueError, OSError):
        budget = 0.0

root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("1100x720")
root.configure(bg="#eef2f7")

selected_index = None

BILL_TYPES = [
    "Electricity", "Water", "Mobile Recharge", "Internet/Wi-Fi",
    "Gas Cylinder", "Rent", "DTH/Cable", "Subscription",
    "Maintenance", "Other Bill"
]

def save_data():
    df.to_csv(FILE, index=False)

def current_month():
    return date.today().strftime("%Y-%m")

def filtered_data():
    result = df.copy()
    query = search_entry.get().strip().lower()
    month = month_entry.get().strip()

    if query:
        mask = (
            result["Category"].astype(str).str.lower().str.contains(query, na=False)
            | result["Bill Type"].astype(str).str.lower().str.contains(query, na=False)
            | result["Description"].astype(str).str.lower().str.contains(query, na=False)
        )
        result = result[mask]

    if month:
        result = result[result["Date"].astype(str).str.startswith(month)]

    return result

def refresh_table():
    for item in table.get_children():
        table.delete(item)

    result = filtered_data()

    for idx, row in result.iterrows():
        table.insert(
            "", "end", iid=str(idx),
            values=(
                row["Amount"], row["Category"], row["Bill Type"],
                row["Date"], row["Description"]
            )
        )

    update_summary()

def update_summary():
    month = month_entry.get().strip()

    if month:
        data = df[df["Date"].astype(str).str.startswith(month)]
    else:
        data = df

    amounts = data["Amount"].to_numpy(dtype=float)

    total = float(np.sum(amounts)) if len(amounts) else 0
    average = float(np.mean(amounts)) if len(amounts) else 0
    highest = float(np.max(amounts)) if len(amounts) else 0
    remaining = budget - total

    summary.config(
        text=f"Total: Rs. {total:.2f}   |   "
             f"Average: Rs. {average:.2f}   |   "
             f"Highest: Rs. {highest:.2f}   |   "
             f"Remaining Budget: Rs. {remaining:.2f}"
    )

    if budget > 0 and total >= budget:
        warning.config(text="Warning: Your budget is used up!")
    elif budget > 0 and total >= budget * 0.8:
        warning.config(text="Warning: You have used 80% of your budget.")
    else:
        warning.config(text="")

def set_budget():
    global budget

    try:
        value = float(budget_entry.get())
        if value <= 0:
            raise ValueError

        budget = value

        with open(BUDGET_FILE, "w") as f:
            f.write(str(budget))

        update_summary()
        messagebox.showinfo("Success", "Monthly budget saved!")

    except ValueError:
        messagebox.showerror("Error", "Enter a valid positive budget.")

def update_bill_options(event=None):
    if category_box.get() == "Bills":
        bill_box.config(state="readonly")
        bill_box.set("Electricity")
    else:
        bill_box.set("")
        bill_box.config(state="disabled")

def add_or_update():
    global df, selected_index

    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            raise ValueError

        category = category_box.get()
        bill_type = bill_box.get() if category == "Bills" else ""
        expense_date = date_entry.get().strip()
        description = description_entry.get().strip()

        if not category:
            messagebox.showerror("Error", "Select a category.")
            return

        parsed_date = pd.to_datetime(
            expense_date, format="%Y-%m-%d", errors="coerce"
        )
        if pd.isna(parsed_date):
            messagebox.showerror(
                "Error", "Date format must be YYYY-MM-DD."
            )
            return

        row = {
            "Amount": amount,
            "Category": category,
            "Bill Type": bill_type,
            "Date": expense_date,
            "Description": description
        }

        if selected_index is None:
            df.loc[len(df)] = row
            message = "Expense added successfully!"
        else:
            df.loc[selected_index, COLUMNS] = [
                row[col] for col in COLUMNS
            ]
            selected_index = None
            add_button.config(text="Add Expense")
            message = "Expense updated successfully!"

        save_data()
        clear_form()
        refresh_table()
        messagebox.showinfo("Success", message)

    except ValueError:
        messagebox.showerror(
            "Error", "Enter a valid amount greater than zero."
        )

def clear_form():
    global selected_index

    selected_index = None
    amount_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)
    category_box.set("Food")
    bill_box.set("")
    bill_box.config(state="disabled")
    date_entry.delete(0, tk.END)
    date_entry.insert(0, date.today().isoformat())
    add_button.config(text="Add Expense")

def load_selected(event=None):
    global selected_index

    selection = table.selection()
    if not selection:
        return

    selected_index = int(selection[0])
    row = df.loc[selected_index]

    amount_entry.delete(0, tk.END)
    amount_entry.insert(0, str(row["Amount"]))

    category_box.set(row["Category"])
    update_bill_options()
    bill_box.set(row["Bill Type"])

    date_entry.delete(0, tk.END)
    date_entry.insert(0, str(row["Date"]))

    description_entry.delete(0, tk.END)
    description_entry.insert(0, str(row["Description"]))

    add_button.config(text="Save Changes")

def delete_expense():
    global df, selected_index

    selection = table.selection()
    if not selection:
        messagebox.showwarning("Warning", "Select an expense first.")
        return

    idx = int(selection[0])

    if messagebox.askyesno("Confirm", "Delete this expense?"):
        df = df.drop(index=idx).reset_index(drop=True)
        save_data()
        clear_form()
        refresh_table()

def show_chart():
    data = filtered_data()

    if data.empty:
        messagebox.showinfo("No Data", "No expenses to display.")
        return

    totals = data.groupby("Category")["Amount"].sum()

    plt.figure(figsize=(7, 5))
    plt.pie(
        totals.values,
        labels=totals.index,
        autopct="%1.1f%%"
    )
    plt.title("Expenses by Category")
    plt.tight_layout()
    plt.show()

def show_monthly_chart():
    if df.empty:
        messagebox.showinfo("No Data", "Add expenses first.")
        return

    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"])

    if data.empty:
        messagebox.showinfo("No Data", "No valid dates found.")
        return

    data["Month"] = data["Date"].dt.to_period("M").astype(str)
    totals = data.groupby("Month")["Amount"].sum()

    plt.figure(figsize=(8, 5))
    plt.bar(totals.index, totals.values)
    plt.title("Monthly Expenses")
    plt.xlabel("Month")
    plt.ylabel("Amount (Rs.)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def export_excel():
    if df.empty:
        messagebox.showinfo("No Data", "No expenses to export.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile="expense_report.xlsx"
    )

    if not path:
        return

    try:
        df.to_excel(path, index=False)
        messagebox.showinfo("Success", "Excel report exported!")
    except ImportError:
        messagebox.showerror(
            "Library Missing",
            "Run: python -m pip install openpyxl"
        )
    except Exception as error:
        messagebox.showerror("Export Error", str(error))

# Heading
tk.Label(
    root, text="PERSONAL EXPENSE TRACKER",
    font=("Arial", 22, "bold"),
    bg="#eef2f7", fg="#23395d"
).pack(pady=12)

# Input form
form = tk.Frame(root, bg="#eef2f7")
form.pack(pady=5)

tk.Label(form, text="Amount (Rs.)", bg="#eef2f7").grid(
    row=0, column=0, padx=5, pady=6
)
amount_entry = tk.Entry(form, width=18)
amount_entry.grid(row=0, column=1, padx=5, pady=6)

tk.Label(form, text="Category", bg="#eef2f7").grid(
    row=0, column=2, padx=5, pady=6
)
category_box = ttk.Combobox(
    form,
    values=["Food", "Travel", "Shopping", "Education", "Bills", "Other"],
    state="readonly", width=17
)
category_box.grid(row=0, column=3, padx=5, pady=6)
category_box.set("Food")
category_box.bind("<<ComboboxSelected>>", update_bill_options)

tk.Label(form, text="Bill Type", bg="#eef2f7").grid(
    row=1, column=0, padx=5, pady=6
)
bill_box = ttk.Combobox(
    form, values=BILL_TYPES, state="disabled", width=17
)
bill_box.grid(row=1, column=1, padx=5, pady=6)

tk.Label(form, text="Date (YYYY-MM-DD)", bg="#eef2f7").grid(
    row=1, column=2, padx=5, pady=6
)
date_entry = tk.Entry(form, width=20)
date_entry.grid(row=1, column=3, padx=5, pady=6)
date_entry.insert(0, date.today().isoformat())

tk.Label(form, text="Description", bg="#eef2f7").grid(
    row=2, column=0, padx=5, pady=6
)
description_entry = tk.Entry(form, width=20)
description_entry.grid(row=2, column=1, padx=5, pady=6)

# Budget
tk.Label(form, text="Monthly Budget (Rs.)", bg="#eef2f7").grid(
    row=2, column=2, padx=5, pady=6
)
budget_entry = tk.Entry(form, width=20)
budget_entry.grid(row=2, column=3, padx=5, pady=6)
budget_entry.insert(0, str(budget) if budget else "")

tk.Button(
    form, text="Set Budget", command=set_budget
).grid(row=2, column=4, padx=5, pady=6)

# Search and month filter
filters = tk.Frame(root, bg="#eef2f7")
filters.pack(pady=8)

tk.Label(filters, text="Search", bg="#eef2f7").grid(
    row=0, column=0, padx=5
)
search_entry = tk.Entry(filters, width=22)
search_entry.grid(row=0, column=1, padx=5)

tk.Label(filters, text="Month (YYYY-MM)", bg="#eef2f7").grid(
    row=0, column=2, padx=5
)
month_entry = tk.Entry(filters, width=14)
month_entry.grid(row=0, column=3, padx=5)
month_entry.insert(0, current_month())

tk.Button(
    filters, text="Apply Filter", command=refresh_table
).grid(row=0, column=4, padx=5)

tk.Button(
    filters, text="Show All",
    command=lambda: (
        search_entry.delete(0, tk.END),
        month_entry.delete(0, tk.END),
        refresh_table()
    )
).grid(row=0, column=5, padx=5)

summary = tk.Label(
    root, text="", font=("Arial", 11, "bold"),
    bg="#eef2f7", fg="#176b45"
)
summary.pack(pady=8)

warning = tk.Label(
    root, text="", font=("Arial", 10, "bold"),
    bg="#eef2f7", fg="#c0392b"
)
warning.pack()

# Expense table
table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=18, pady=8)

columns = tuple(COLUMNS)
table = ttk.Treeview(
    table_frame, columns=columns, show="headings", height=10
)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=175, anchor="center")

table.column("Description", width=210)
table.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(
    table_frame, orient="vertical", command=table.yview
)
scrollbar.pack(side="right", fill="y")
table.configure(yscrollcommand=scrollbar.set)
table.bind("<<TreeviewSelect>>", load_selected)

# Buttons
button_frame = tk.Frame(root, bg="#eef2f7")
button_frame.pack(pady=12)

add_button = tk.Button(
    button_frame, text="Add Expense", command=add_or_update,
    bg="#25855a", fg="white", width=15
)
add_button.grid(row=0, column=0, padx=5)

tk.Button(
    button_frame, text="Delete Selected", command=delete_expense,
    bg="#c0392b", fg="white", width=15
).grid(row=0, column=1, padx=5)

tk.Button(
    button_frame, text="Pie Chart", command=show_chart,
    bg="#315caa", fg="white", width=13
).grid(row=0, column=2, padx=5)

tk.Button(
    button_frame, text="Monthly Chart", command=show_monthly_chart,
    bg="#7952a0", fg="white", width=15
).grid(row=0, column=3, padx=5)

tk.Button(
    button_frame, text="Export Excel", command=export_excel,
    bg="#087f8c", fg="white", width=13
).grid(row=0, column=4, padx=5)

refresh_table()
root.mainloop()

