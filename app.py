import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Connect to SQLite database (creates if not exists)
conn = sqlite3.connect('fleet.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT,
    model TEXT,
    purchase_date DATE,
    mileage REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER,
    date DATE,
    description TEXT,
    cost REAL,
    FOREIGN KEY(truck_id) REFERENCES trucks(id)
)
''')
conn.commit()

# Functions for CRUD operations
def add_truck(make, model, purchase_date, mileage):
    c.execute('INSERT INTO trucks (make, model, purchase_date, mileage) VALUES (?, ?, ?, ?)',
              (make, model, purchase_date, mileage))
    conn.commit()

def get_trucks():
    return pd.read_sql_query('SELECT * FROM trucks', conn)

def update_truck(truck_id, make, model, purchase_date, mileage):
    c.execute('UPDATE trucks SET make=?, model=?, purchase_date=?, mileage=? WHERE id=?',
              (make, model, purchase_date, mileage, truck_id))
    conn.commit()

def delete_truck(truck_id):
    c.execute('DELETE FROM trucks WHERE id=?', (truck_id,))
    c.execute('DELETE FROM expenses WHERE truck_id=?', (truck_id,))
    conn.commit()

def add_expense(truck_id, date, description, cost):
    c.execute('INSERT INTO expenses (truck_id, date, description, cost) VALUES (?, ?, ?, ?)',
              (truck_id, date, description, cost))
    conn.commit()

def get_expenses(truck_id):
    return pd.read_sql_query('SELECT * FROM expenses WHERE truck_id=?', conn, params=(truck_id,))

def get_total_expenses(truck_id):
    c.execute('SELECT SUM(cost) FROM expenses WHERE truck_id=?', (truck_id,))
    return c.fetchone()[0] or 0.0

# Streamlit App
st.title("Fleet Management MVP")

# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["Add Truck", "View/Edit Trucks", "Manage Expenses"])

if page == "Add Truck":
    st.header("Add New Truck")
    make = st.text_input("Make")
    model = st.text_input("Model")
    purchase_date = st.date_input("Purchase Date", value=date.today())
    mileage = st.number_input("Initial Mileage", min_value=0.0)
    if st.button("Add Truck"):
        if make and model:
            add_truck(make, model, purchase_date, mileage)
            st.success("Truck added!")
        else:
            st.error("Make and model are required.")

elif page == "View/Edit Trucks":
    st.header("View and Edit Trucks")
    trucks = get_trucks()
    if not trucks.empty:
        search = st.text_input("Search by Make or Model")
        if search:
            trucks = trucks[trucks['make'].str.contains(search, case=False) | trucks['model'].str.contains(search, case=False)]
        
        for idx, row in trucks.iterrows():
            with st.expander(f"Truck ID: {row['id']} - {row['make']} {row['model']}"):
                new_make = st.text_input("Make", value=row['make'], key=f"make_{row['id']}")
                new_model = st.text_input("Model", value=row['model'], key=f"model_{row['id']}")
                new_purchase_date = st.date_input("Purchase Date", value=date.fromisoformat(row['purchase_date']), key=f"date_{row['id']}")
                new_mileage = st.number_input("Mileage", value=float(row['mileage']), key=f"mileage_{row['id']}")
                if st.button("Update", key=f"update_{row['id']}"):
                    update_truck(row['id'], new_make, new_model, new_purchase_date, new_mileage)
                    st.success("Updated!")
                if st.button("Delete", key=f"delete_{row['id']}"):
                    delete_truck(row['id'])
                    st.success("Deleted!")
                    st.rerun()  # Refresh page
    else:
        st.info("No trucks added yet.")

elif page == "Manage Expenses":
    st.header("Manage Expenses")
    trucks = get_trucks()
    if not trucks.empty:
        truck_id = st.selectbox("Select Truck", trucks['id'].tolist(), format_func=lambda x: f"ID {x}: {trucks[trucks['id']==x]['make'].values[0]} {trucks[trucks['id']==x]['model'].values[0]}")
        
        st.subheader("Add Expense")
        exp_date = st.date_input("Date", value=date.today())
        description = st.text_input("Description (e.g., Repair, Breakdown)")
        cost = st.number_input("Cost", min_value=0.0)
        if st.button("Add Expense"):
            if description:
                add_expense(truck_id, exp_date, description, cost)
                st.success("Expense added!")
            else:
                st.error("Description is required.")
        
        st.subheader("Expenses for This Truck")
        expenses = get_expenses(truck_id)
        if not expenses.empty:
            st.dataframe(expenses)
            total = get_total_expenses(truck_id)
            st.write(f"Total Expenses: ${total:.2f}")
        else:
            st.info("No expenses yet.")
    else:
        st.info("No trucks added yet.")

# Close connection
conn.close()