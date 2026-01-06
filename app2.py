# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# ======================
# Database Setup & Helpers
# ======================
DB_FILE = "fleet.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS trucks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        purchase_date DATE,
        mileage REAL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        truck_id INTEGER,
        date DATE,
        description TEXT NOT NULL,
        cost REAL,
        FOREIGN KEY(truck_id) REFERENCES trucks(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    conn.close()

# CRUD Operations (modular and reusable)
def add_truck(make: str, model: str, purchase_date: date, mileage: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO trucks (make, model, purchase_date, mileage) VALUES (?, ?, ?, ?)',
              (make, model, purchase_date, mileage))
    conn.commit()
    conn.close()

def get_trucks_df() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query('SELECT id, make, model, purchase_date, mileage FROM trucks', conn)
    conn.close()
    if not df.empty:
        df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.date
    return df

def update_truck(truck_id: int, make: str, model: str, purchase_date: date, mileage: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE trucks SET make=?, model=?, purchase_date=?, mileage=? WHERE id=?',
              (make, model, purchase_date, mileage, truck_id))
    conn.commit()
    conn.close()

def delete_truck(truck_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM trucks WHERE id=?', (truck_id,))
    conn.commit()
    conn.close()

def add_expense(truck_id: int, date: date, description: str, cost: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO expenses (truck_id, date, description, cost) VALUES (?, ?, ?, ?)',
              (truck_id, date, description, cost))
    conn.commit()
    conn.close()

def get_expenses_df(truck_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query('SELECT date, description, cost FROM expenses WHERE truck_id=? ORDER BY date DESC',
                           conn, params=(truck_id,))
    conn.close()
    return df

def get_total_expenses(truck_id: int) -> float:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT SUM(cost) FROM expenses WHERE truck_id=?', (truck_id,))
    total = c.fetchone()[0] or 0.0
    conn.close()
    return float(total)

# Initialize DB on app start
init_db()

# ======================
# Streamlit App Layout
# ======================
st.title("🚛 Fleet Management System")

tab1, tab2, tab3 = st.tabs(["Add Truck", "Manage Trucks", "Expenses"])

# ====================
# Tab 1: Add Truck
# ====================
with tab1:
    st.header("Add New Truck")
    with st.form("add_truck_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            make = st.text_input("Make", placeholder="e.g., Volvo")
            purchase_date = st.date_input("Purchase Date", value=date.today())
        with col2:
            model = st.text_input("Model", placeholder="e.g., VNL 760")
            mileage = st.number_input("Initial Mileage", min_value=0.0, step=1000.0)

        submitted = st.form_submit_button("Add Truck")
        if submitted:
            if make.strip() and model.strip():
                add_truck(make.strip(), model.strip(), purchase_date, mileage)
                st.success(f"Added {make} {model}!")
                st.rerun()
            else:
                st.error("Make and Model are required.")

# ====================
# Tab 2: Manage Trucks (Table View + Edit + Delete)
# ====================
with tab2:
    st.header("Fleet Overview")
    trucks_df = get_trucks_df()

    if trucks_df.empty:
        st.info("No trucks in the fleet yet. Add one in the 'Add Truck' tab.")
    else:
        # Use data_editor for inline editing
        edited_df = st.data_editor(
            trucks_df,
            num_rows="fixed",
            use_container_width=True,
            hide_index=False,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "make": st.column_config.TextColumn("Make", required=True),
                "model": st.column_config.TextColumn("Model", required=True),
                "purchase_date": st.column_config.DateColumn("Purchase Date"),
                "mileage": st.column_config.NumberColumn("Mileage", min_value=0.0, step=1000.0),
            },
            key="trucks_editor"
        )

        col_save, col_del = st.columns([1, 3])
        with col_save:
            if st.button("💾 Save Changes", type="primary"):
                # Find changed rows
                for idx, row in edited_df.iterrows():
                    orig_row = trucks_df.loc[trucks_df['id'] == row['id']].iloc[0]
                    if not row.equals(orig_row):
                        update_truck(row['id'], row['make'], row['model'], row['purchase_date'], row['mileage'])
                st.success("All changes saved!")
                st.rerun()

        with col_del:
            truck_to_delete = st.selectbox("Select truck to delete", options=trucks_df['id'],
                                           format_func=lambda x: f"ID {x}: {trucks_df[trucks_df['id']==x]['make'].values[0]} {trucks_df[trucks_df['id']==x]['model'].values[0]}")
            if st.button("🗑️ Delete Selected Truck", type="secondary"):
                delete_truck(truck_to_delete)
                st.success("Truck deleted!")
                st.rerun()

# ====================
# Tab 3: Expenses
# ====================
with tab3:
    st.header("Expense Management")
    trucks_df = get_trucks_df()

    if trucks_df.empty:
        st.info("Add trucks first before managing expenses.")
    else:
        # Truck selector with nice label
        truck_options = {f"ID {row['id']}: {row['make']} {row['model']}": row['id'] for _, row in trucks_df.iterrows()}
        selected_label = st.selectbox("Select Truck", options=list(truck_options.keys()))
        selected_truck_id = truck_options[selected_label]

        col_form, col_list = st.columns([1, 1])

        with col_form:
            st.subheader("Add Expense")
            with st.form("add_expense_form", clear_on_submit=True):
                exp_date = st.date_input("Date", value=date.today())
                description = st.text_input("Description", placeholder="e.g., Oil change, tire replacement")
                cost = st.number_input("Cost ($)", min_value=0.0, step=10.0)
                if st.form_submit_button("Add Expense"):
                    if description.strip():
                        add_expense(selected_truck_id, exp_date, description.strip(), cost)
                        st.success("Expense recorded!")
                        st.rerun()
                    else:
                        st.error("Description is required.")

        with col_list:
            st.subheader("Expense History")
            expenses_df = get_expenses_df(selected_truck_id)
            if expenses_df.empty:
                st.info("No expenses recorded yet.")
            else:
                st.dataframe(expenses_df.assign(cost=lambda x: x['cost'].map("${:,.2f}".format)),
                             use_container_width=True)
                total = get_total_expenses(selected_truck_id)
                st.metric("Total Expenses", f"${total:,.2f}")