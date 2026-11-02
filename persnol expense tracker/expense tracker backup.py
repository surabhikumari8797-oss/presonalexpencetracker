
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

FILE_NAME = "expenses.csv"

# Load existing expenses or create an empty DataFrame
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(
        columns=["Amount", "Category", "Date", "Description"]
    )


def save_data():
    df.to_csv(FILE_NAME, index=False)


def refresh_table():
    for item in table.get_children():
        table.delete(item)

    for index, row in df.iterrows():
        table.insert(
            "",
            "end",
            iid=str(index),
            values=(
                row["Amount"],
                row["Category"],
                row["Date"],
                row["Description"]
            )
        )

    update_summary()


def update_summary():
    if df.empty:
        total = 0
        average = 0
        highest = 0
    else:
        amounts = df["Amount"].to_numpy(dtype=float)

        # NumPy calculations
        total = np.sum(amounts)
        average = np.mean(amounts)
        highest = np.max(amounts)

    summary_label.config(
        text=f"Total: Rs. {total:.2f}  |  "
             f"Average: Rs. {average:.2f}  |  "
             f"Highest: Rs. {highest:.2f}"
    )


def add_expense():
    global df

    try:
        amount = float(amount_entry.get())

        if amount <= 0:
            messagebox.showerror(
                "Error", "Amount must be greater than zero."
            )
            return

        category = category_box.get()
        expense_date = date_entry.get().strip()
        description = description_entry.get().strip()

        if not category:
            messagebox.showerror("Error", "Select a category.")
            return

        # Validate the date
        try:
            expense_date = str(
                pd.to_datetime(
                    expense_date, format="%Y-%m-%d", errors="raise"
                ).date()
            )
        except (ValueError, TypeError):
            messagebox.showerror(
                "Error", "Enter date in YYYY-MM-DD format."
            )
            return

        new_row = pd.DataFrame([{
            "Amount": amount,
            "Category": category,
            "Date": expense_date,
            "Description": description
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        save_data()
        refresh_table()

        amount_entry.delete(0, tk.END)
        description_entry.delete(0, tk.END)

        messagebox.showinfo("Success", "Expense added successfully!")

    except ValueError:
        messagebox.showerror(
            "Error", "Please enter a valid amount."
        )


def delete_expense():
    global df

    selected = table.selection()

    if not selected:
        messagebox.showwarning(
            "Warning", "Select an expense first."
        )
        return

    index = int(selected[0])
    df = df.drop(index=index).reset_index(drop=True)

    save_data()
    refresh_table()


def show_chart():
    if df.empty:
        messagebox.showinfo(
            "No Data", "Please add expenses first."
        )
        return

    category_totals = df.groupby("Category")["Amount"].sum()

    plt.figure(figsize=(7, 5))
    plt.pie(
        category_totals.values,
        labels=category_totals.index,
        autopct="%1.1f%%"
    )
    plt.title("Expenses by Category")
    plt.tight_layout()
    plt.show()


# Main window
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("900x600")
root.configure(bg="#eef2f7")

heading = tk.Label(
    root,
    text="Personal Expense Tracker",
    font=("Arial", 22, "bold"),
    bg="#eef2f7",
    fg="#23395d"
)
heading.pack(pady=15)

# Input form
form = tk.Frame(root, bg="#eef2f7")
form.pack(pady=5)

tk.Label(form, text="Amount (Rs.)", bg="#eef2f7").grid(
    row=0, column=0, padx=6, pady=8
)
amount_entry = tk.Entry(form, width=18)
amount_entry.grid(row=0, column=1, padx=6, pady=8)

tk.Label(form, text="Category", bg="#eef2f7").grid(
    row=0, column=2, padx=6, pady=8
)
category_box = ttk.Combobox(
    form,
    values=[
        "Food", "Travel", "Shopping",
        "Education", "Bills", "Other"
    ],
    state="readonly",
    width=16
)
category_box.grid(row=0, column=3, padx=6, pady=8)
category_box.set("Food")

tk.Label(form, text="Date (YYYY-MM-DD)", bg="#eef2f7").grid(
    row=1, column=0, padx=6, pady=8
)
date_entry = tk.Entry(form, width=18)
date_entry.grid(row=1, column=1, padx=6, pady=8)
date_entry.insert(0, pd.Timestamp.today().strftime("%Y-%m-%d"))

tk.Label(form, text="Description", bg="#eef2f7").grid(
    row=1, column=2, padx=6, pady=8
)
description_entry = tk.Entry(form, width=18)
description_entry.grid(row=1, column=3, padx=6, pady=8)

# Summary
summary_label = tk.Label(
    root,
    text="Total: Rs. 0.00",
    font=("Arial", 12, "bold"),
    bg="#eef2f7",
    fg="#176b45"
)
summary_label.pack(pady=12)

# Expense table
columns = ("Amount", "Category", "Date", "Description")

table = ttk.Treeview(
    root, columns=columns, show="headings", height=12
)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=200, anchor="center")

table.pack(fill="both", expand=True, padx=20, pady=10)

# Buttons
buttons = tk.Frame(root, bg="#eef2f7")
buttons.pack(pady=12)

tk.Button(
    buttons, text="Add Expense",
    command=add_expense, bg="#25855a",
    fg="white", width=16
).grid(row=0, column=0, padx=8)

tk.Button(
    buttons, text="Delete Selected",
    command=delete_expense, bg="#c0392b",
    fg="white", width=16
).grid(row=0, column=1, padx=8)

tk.Button(
    buttons, text="Show Chart",
    command=show_chart, bg="#315caa",
    fg="white", width=16
).grid(row=0, column=2, padx=8)

refresh_table()
root.mainloop()

