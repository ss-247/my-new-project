# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import math  # For NaN checks if needed

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
        year INTEGER,
        plate_reg TEXT,
        vin TEXT,
        status TEXT DEFAULT 'Active',
        gas_type TEXT,
        tank_capacity TEXT,
        operator TEXT,
        location TEXT,
        purchase_date DATE,
        exp_date DATE,
        next_service_due DATE,
        mileage REAL DEFAULT 0.0
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        truck_id INTEGER,
        date DATE,
        description TEXT NOT NULL,
        odometer REAL,
        service_provider TEXT,
        mechanic TEXT,
        part_no TEXT,
        next_service_due DATE,
        material_cost REAL DEFAULT 0.0,
        labor_cost REAL DEFAULT 0.0,
        warranty TEXT,
        total_cost REAL DEFAULT 0.0,
        FOREIGN KEY(truck_id) REFERENCES trucks(id) ON DELETE CASCADE
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS monthly_mileages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        truck_id INTEGER,
        month_date DATE,
        starting_mileage REAL DEFAULT 0.0,
        ending_mileage REAL DEFAULT 0.0,
        FOREIGN KEY(truck_id) REFERENCES trucks(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    conn.close()

# Truck CRUD
def add_truck(make, model, year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    INSERT INTO trucks (make, model, year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (make, model, year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage))
    conn.commit()
    conn.close()

def get_trucks_df():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM trucks', conn)
    conn.close()
    if not df.empty:
        df['purchase_date'] = pd.to_datetime(df['purchase_date']).dt.date
        df['exp_date'] = pd.to_datetime(df['exp_date']).dt.date
        df['next_service_due'] = pd.to_datetime(df['next_service_due']).dt.date
    return df

def update_truck(truck_id, make, model, year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    UPDATE trucks SET make=?, model=?, year=?, plate_reg=?, vin=?, status=?, gas_type=?, tank_capacity=?, operator=?, location=?, purchase_date=?, exp_date=?, next_service_due=?, mileage=?
    WHERE id=?
    ''', (make, model, year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage, truck_id))
    conn.commit()
    conn.close()

def delete_truck(truck_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM trucks WHERE id=?', (truck_id,))
    conn.commit()
    conn.close()

# Maintenance Log CRUD
def add_maintenance_log(truck_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, warranty, total_cost):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    INSERT INTO maintenance_logs (truck_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, warranty, total_cost)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (truck_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, warranty, total_cost))
    conn.commit()
    conn.close()

def get_maintenance_logs_df(truck_id):
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM maintenance_logs WHERE truck_id=? ORDER BY date DESC', conn, params=(truck_id,))
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['next_service_due'] = pd.to_datetime(df['next_service_due']).dt.date
    return df

def update_maintenance_log(log_id, truck_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, warranty, total_cost):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    UPDATE maintenance_logs SET truck_id=?, date=?, description=?, odometer=?, service_provider=?, mechanic=?, part_no=?, next_service_due=?, material_cost=?, labor_cost=?, warranty=?, total_cost=?
    WHERE id=?
    ''', (truck_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, warranty, total_cost, log_id))
    conn.commit()
    conn.close()

def delete_maintenance_log(log_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM maintenance_logs WHERE id=?', (log_id,))
    conn.commit()
    conn.close()

def get_total_expenses(truck_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT SUM(total_cost) FROM maintenance_logs WHERE truck_id=?', (truck_id,))
    total = c.fetchone()[0] or 0.0
    conn.close()
    return total

# Monthly Mileage CRUD
def add_monthly_mileage(truck_id, month_date, starting_mileage, ending_mileage):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    INSERT INTO monthly_mileages (truck_id, month_date, starting_mileage, ending_mileage)
    VALUES (?, ?, ?, ?)
    ''', (truck_id, month_date, starting_mileage, ending_mileage))
    conn.commit()
    conn.close()

def get_monthly_mileages_df(truck_id):
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM monthly_mileages WHERE truck_id=? ORDER BY month_date', conn, params=(truck_id,))
    conn.close()
    if not df.empty:
        df['month_date'] = pd.to_datetime(df['month_date']).dt.date
    return df

def update_monthly_mileage(m_id, truck_id, month_date, starting_mileage, ending_mileage):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    UPDATE monthly_mileages SET truck_id=?, month_date=?, starting_mileage=?, ending_mileage=?
    WHERE id=?
    ''', (truck_id, month_date, starting_mileage, ending_mileage, m_id))
    conn.commit()
    conn.close()

def delete_monthly_mileage(m_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM monthly_mileages WHERE id=?', (m_id,))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# ======================
# UI Functions (Modular)
# ======================

def show_fleet_overview():
    st.header("Fleet Overview")
    trucks_df = get_trucks_df()
    if trucks_df.empty:
        st.info("No vehicles in the fleet yet. Add one in the 'Add Truck' page.")
        return

    search = st.text_input("Search by Plate/Reg #, Make, Model, or Operator").strip().lower()
    if search:
        trucks_df = trucks_df[
            trucks_df['plate_reg'].str.lower().str.contains(search) |
            trucks_df['make'].str.lower().str.contains(search) |
            trucks_df['model'].str.lower().str.contains(search) |
            trucks_df['operator'].str.lower().str.contains(search)
        ]

    sorted_df = trucks_df.sort_values('plate_reg')
    if sorted_df.empty:
        st.info("No matching vehicles found.")
        return

    num_cols = 3
    cols = st.columns(num_cols)
    for idx, row in sorted_df.iterrows():
        with cols[idx % num_cols]:
            st.markdown(
                """
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background-color: #f9f9f9; text-align: left; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0;">{plate_reg}</h4>
                    <p style="margin: 5px 0;"><strong>{year} {make} {model}</strong></p>
                    <p style="margin: 5px 0;">Operator: {operator}</p>
                    <p style="margin: 5px 0;">Location: {location}</p>
                    <p style="margin: 5px 0;">Mileage: {mileage:,.0f}</p>
                </div>
                """.format(
                    plate_reg=row['plate_reg'] or "N/A",
                    year=row['year'] or "",
                    make=row['make'],
                    model=row['model'],
                    operator=row['operator'] or "N/A",
                    location=row['location'] or "N/A",
                    mileage=row['mileage'] or 0
                ),
                unsafe_allow_html=True
            )
            if st.button("View Details", key=f"view_{row['id']}_{idx}"):
                st.session_state.selected_truck = int(row['id'])
                st.session_state.page_select = "Vehicle Detail"  # Sync with selectbox
                st.rerun()

def show_add_truck():
    st.header("Add New Truck")
    with st.form("add_truck_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            make = st.text_input("Make", placeholder="e.g., Ford")
            model = st.text_input("Model", placeholder="e.g., Transit-350 Cargo")
            year = st.number_input("Year", min_value=1900, max_value=2100, step=1)
            plate_reg = st.text_input("Plate / Reg #", placeholder="e.g., FLT012")
            vin = st.text_input("VIN", placeholder="e.g., 2T1BR18E8XC165041")
        with col2:
            status = st.selectbox("Status", ["Active", "Inactive"])
            gas_type = st.selectbox("Gasoline Type", ["Regular", "Premium", "Diesel", "Electric", "Other"])
            tank_capacity = st.text_input("Tank Capacity", placeholder="e.g., 25.1 gal")
            operator = st.text_input("Operator", placeholder="e.g., John Smith")
            location = st.text_input("Location", placeholder="e.g., Atlanta")
        with col3:
            purchase_date = st.date_input("Purchase Date", value=date.today())
            exp_date = st.date_input("Expiration Date", value=None)
            next_service_due = st.date_input("Next Service Due", value=None)
            mileage = st.number_input("Initial Mileage", min_value=0.0, step=1000.0)

        submitted = st.form_submit_button("Add Truck")
        if submitted:
            if make.strip() and model.strip():
                add_truck(make.strip(), model.strip(), year, plate_reg, vin, status, gas_type, tank_capacity, operator, location, purchase_date, exp_date, next_service_due, mileage)
                st.success(f"Added {make} {model}!")
                st.rerun()
            else:
                st.error("Make and Model are required.")

def show_manage_trucks():
    st.header("Manage Trucks")
    trucks_df = get_trucks_df()
    if trucks_df.empty:
        st.info("No trucks added yet.")
        return

    search = st.text_input("Search by Make, Model, or Plate/Reg #").strip().lower()
    if search:
        trucks_df = trucks_df[
            trucks_df['make'].str.lower().str.contains(search) |
            trucks_df['model'].str.lower().str.contains(search) |
            trucks_df['plate_reg'].str.lower().str.contains(search)
        ]

    edited_df = st.data_editor(
        trucks_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=False,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "make": st.column_config.TextColumn("Make", required=True),
            "model": st.column_config.TextColumn("Model", required=True),
            "year": st.column_config.NumberColumn("Year", format="%d"),
            "plate_reg": st.column_config.TextColumn("Plate/Reg #"),
            "vin": st.column_config.TextColumn("VIN"),
            "status": st.column_config.SelectboxColumn("Status", options=["Active", "Inactive"]),
            "gas_type": st.column_config.SelectboxColumn("Gas Type", options=["Regular", "Premium", "Diesel", "Electric", "Other"]),
            "tank_capacity": st.column_config.TextColumn("Tank Capacity"),
            "operator": st.column_config.TextColumn("Operator"),
            "location": st.column_config.TextColumn("Location"),
            "purchase_date": st.column_config.DateColumn("Purchase Date"),
            "exp_date": st.column_config.DateColumn("Exp. Date"),
            "next_service_due": st.column_config.DateColumn("Next Service Due"),
            "mileage": st.column_config.NumberColumn("Mileage", min_value=0.0, step=1000.0),
        },
        key="trucks_editor"
    )

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("💾 Save Changes", type="primary"):
            for idx, row in edited_df.iterrows():
                orig_row = trucks_df.loc[trucks_df['id'] == row['id']].iloc[0]
                if not row.equals(orig_row):
                    update_truck(row['id'], row['make'], row['model'], row['year'], row['plate_reg'], row['vin'], row['status'], row['gas_type'], row['tank_capacity'], row['operator'], row['location'], row['purchase_date'], row['exp_date'], row['next_service_due'], row['mileage'])
            st.success("All changes saved!")
            st.rerun()

    with col_del:
        truck_to_delete = st.selectbox("Select Truck to Delete", options=trucks_df['id'], format_func=lambda x: f"ID {x}: {trucks_df[trucks_df['id']==x]['plate_reg'].values[0]} - {trucks_df[trucks_df['id']==x]['make'].values[0]} {trucks_df[trucks_df['id']==x]['model'].values[0]}")
        if st.button("🗑️ Delete Selected Truck"):
            if truck_to_delete:
                delete_truck(truck_to_delete)
                st.success("Truck deleted!")
                st.rerun()

def show_vehicle_detail(truck_id):
    trucks_df = get_trucks_df()
    row = trucks_df[trucks_df['id'] == truck_id].iloc[0]
    st.header(f"{row['plate_reg']} - {row['year']} {row['make']} {row['model']}")

    if st.button("← Back to Fleet Overview"):
        st.session_state.selected_truck = None
        st.session_state.page_select = "Fleet Overview"
        st.rerun()

    # Vehicle Info
    st.subheader("Vehicle Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Status:** {row['status']}")
        st.write(f"**Operator:** {row['operator']}")
        st.write(f"**Location:** {row['location']}")
        st.write(f"**Mileage:** {row['mileage']:,.0f}")
    with col2:
        st.write(f"**Gasoline Type:** {row['gas_type']}")
        st.write(f"**Tank Capacity:** {row['tank_capacity']}")
        st.write(f"**VIN:** {row['vin']}")
    with col3:
        st.write(f"**Acquisition Date:** {row['purchase_date']}")
        st.write(f"**Expiration Date:** {row['exp_date']}")
        st.write(f"**Next Service Due:** {row['next_service_due']}")

    # Monthly Mileage Editor
    st.subheader("Monthly Mileage Data")
    monthly_df = get_monthly_mileages_df(truck_id)
    edited_monthly = monthly_df.copy()
    edited_monthly['delete'] = False
    edited_monthly = st.data_editor(
        edited_monthly,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=False,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "truck_id": st.column_config.NumberColumn("Truck ID", disabled=True),
            "month_date": st.column_config.DateColumn("Month Date", required=True),
            "starting_mileage": st.column_config.NumberColumn("Starting Mileage", min_value=0.0, required=True),
            "ending_mileage": st.column_config.NumberColumn("Ending Mileage", min_value=0.0, required=True),
            "delete": st.column_config.CheckboxColumn("Delete?")
        },
        key=f"monthly_editor_{truck_id}"
    )
    if st.button("Save Monthly Changes"):
        # Deletes
        to_delete = edited_monthly[edited_monthly['delete'] == True]['id'].dropna()
        for d in to_delete:
            delete_monthly_mileage(int(d))
        # Adds/Updates
        for _, r in edited_monthly[edited_monthly['delete'] == False].iterrows():
            if pd.isna(r['id']):
                add_monthly_mileage(truck_id, r['month_date'], r['starting_mileage'], r['ending_mileage'])
            else:
                update_monthly_mileage(int(r['id']), truck_id, r['month_date'], r['starting_mileage'], r['ending_mileage'])
        st.success("Monthly data saved!")
        st.rerun()

    # Cost Per Mile Summary (Computed)
    if not monthly_df.empty:
        st.subheader("Cost Per Mile Summary")
        logs_df = get_maintenance_logs_df(truck_id)
        monthly_df = monthly_df.sort_values('month_date')
        monthly_df['monthly_mileage'] = monthly_df['ending_mileage'] - monthly_df['starting_mileage']
        monthly_df['monthly_cost'] = 0.0
        for i, m in monthly_df.iterrows():
            month_start = m['month_date']
            month_end = month_start + relativedelta(months=1)
            monthly_df.at[i, 'monthly_cost'] = logs_df[(logs_df['date'] >= month_start) & (logs_df['date'] < month_end)]['total_cost'].sum()
        annual_mileage = monthly_df['monthly_mileage'].sum()
        total_costs = monthly_df['monthly_cost'].sum()  # Or from get_total_expenses
        cost_per_mile = total_costs / annual_mileage if annual_mileage > 0 else 0.0
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        col_metrics1.metric("Annual Mileage", f"{annual_mileage:,.0f}")
        col_metrics2.metric("Total Service Costs", f"${total_costs:,.2f}")
        col_metrics3.metric("Service Cost Per Mile", f"${cost_per_mile:.4f}")
        st.dataframe(
            monthly_df[['month_date', 'starting_mileage', 'ending_mileage', 'monthly_mileage', 'monthly_cost']],
            use_container_width=True,
            column_config={
                "month_date": "Month",
                "starting_mileage": "Starting Mileage",
                "ending_mileage": "Ending Mileage",
                "monthly_mileage": "Monthly Mileage",
                "monthly_cost": "Monthly Cost"
            }
        )

    # Maintenance Cost Summary (Computed)
    st.subheader("Maintenance Cost Summary")
    categories = {
        "E N G I N E": [
            "Oil & Filter Change", "Air Filter Change", "Fuel Filter Change",
            "Transmission Fluid", "Engine Coolant", "Hose Replacement",
            "Belt Replacement", "Battery Replacement"
        ],
        "C H A S S I S": [
            "Tire Repair / Replacement", "Tire Rotation / Balance",
            "Tire Alignment", "Brake Pad Replacement"
        ],
        "M I S C": [
            "Windshield Wiper Repl.", "Bulb Replacement", "Other"
        ]
    }
    all_types = [t for sublist in categories.values() for t in sublist]
    if not monthly_df.empty:
        columns = monthly_df['month_date'].tolist()
        cost_summary = pd.DataFrame(0.0, index=all_types, columns=columns)
        logs_df = get_maintenance_logs_df(truck_id)
        for _, log in logs_df.iterrows():
            if log['description'] in all_types:
                for i, m in monthly_df.iterrows():
                    month_start = m['month_date']
                    month_end = month_start + relativedelta(months=1)
                    if month_start <= log['date'] < month_end:
                        cost_summary.at[log['description'], columns[i]] += log['total_cost']
                        break
        total_monthly = cost_summary.sum(axis=0)
        cost_summary.loc['Total Monthly Costs'] = total_monthly

        # Display with categories
        for cat, types_list in categories.items():
            st.write(f"**{cat}**")
            cat_df = cost_summary.loc[[t for t in types_list if t in cost_summary.index]]
            st.dataframe(cat_df, use_container_width=True)
        st.write("**Totals**")
        st.dataframe(cost_summary.loc[['Total Monthly Costs']], use_container_width=True)
    else:
        st.info("Add monthly mileage data to compute costs.")

    # Preventative Maintenance Schedule (Static)
    st.subheader("Preventative Maintenance Schedule")
    schedule_data = [
        {"Mileage": 10000, "Recommended Maintenance": "Rotate Tires, Change Oil and Filter"},
        {"Mileage": 20000, "Recommended Maintenance": "Rotate Tires, Change Oil and Filter"},
        {"Mileage": 30000, "Recommended Maintenance": "Replace Air Filter, Rotate Tires, Fuel Filter Replacement, Change Oil and Filter"},
        {"Mileage": 40000, "Recommended Maintenance": "Rotate Tires, Change Oil and Filter"},
        {"Mileage": 45000, "Recommended Maintenance": "Replace Air Filter, Rotate Tires, Fuel Filter Replacement, Change Oil and Filter"},
        {"Mileage": 50000, "Recommended Maintenance": "Rotate Tires, Change Oil and Filter"},
        {"Mileage": 60000, "Recommended Maintenance": "Replace Air Filter, Rotate Tires, Fuel Filter Replacement, Clean and Repack Wheel Bearing, Change Oil and Filter"},
        # Add more as needed...
    ]
    schedule_df = pd.DataFrame(schedule_data)
    st.dataframe(schedule_df, use_container_width=True)

    # Maintenance Log Editor
    st.subheader("Vehicle Maintenance Log")
    col_form, col_editor = st.columns([1, 2])
    with col_form:
        st.write("Add New Log Entry")
        with st.form("add_log_form", clear_on_submit=True):
            log_col1, log_col2 = st.columns(2)
            with log_col1:
                log_date = st.date_input("Date", value=date.today())
                description = st.text_input("Description", placeholder="e.g., Oil & Filter Change")
                odometer = st.number_input("Odometer", min_value=0.0, value=row['mileage'])
                service_provider = st.text_input("Service Provider", placeholder="e.g., PepBoys")
                mechanic = st.text_input("Mechanic", placeholder="e.g., n/a")
            with log_col2:
                part_no = st.text_input("Part No.", placeholder="e.g., 5729")
                log_next_due = st.date_input("Next Service Due (this type)", value=None)
                material_cost = st.number_input("Material Cost", min_value=0.0)
                labor_cost = st.number_input("Labor Cost", min_value=0.0)
                warranty = st.text_input("Warranty")
            total_cost = material_cost + labor_cost
            st.write(f"Total Cost: ${total_cost:.2f}")
            if st.form_submit_button("Add Log"):
                if description.strip():
                    add_maintenance_log(truck_id, log_date, description.strip(), odometer, service_provider, mechanic, part_no, log_next_due, material_cost, labor_cost, warranty, total_cost)
                    if odometer > row['mileage']:
                        update_truck(truck_id, row['make'], row['model'], row['year'], row['plate_reg'], row['vin'], row['status'], row['gas_type'], row['tank_capacity'], row['operator'], row['location'], row['purchase_date'], row['exp_date'], row['next_service_due'], odometer)
                    st.success("Log added!")
                    st.rerun()
                else:
                    st.error("Description is required.")

    with col_editor:
        logs_df = get_maintenance_logs_df(truck_id)
        if logs_df.empty:
            st.info("No maintenance logs yet.")
        else:
            edited_logs = logs_df.copy()
            edited_logs['delete'] = False
            edited_logs = st.data_editor(
                edited_logs,
                use_container_width=True,
                hide_index=False,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "truck_id": st.column_config.NumberColumn("Truck ID", disabled=True),
                    "date": st.column_config.DateColumn("Date"),
                    "description": st.column_config.TextColumn("Description"),
                    "odometer": st.column_config.NumberColumn("Odometer"),
                    "service_provider": st.column_config.TextColumn("Service Provider"),
                    "mechanic": st.column_config.TextColumn("Mechanic"),
                    "part_no": st.column_config.TextColumn("Part No."),
                    "next_service_due": st.column_config.DateColumn("Next Service Due"),
                    "material_cost": st.column_config.NumberColumn("Material Cost"),
                    "labor_cost": st.column_config.NumberColumn("Labor Cost"),
                    "warranty": st.column_config.TextColumn("Warranty"),
                    "total_cost": st.column_config.NumberColumn("Total Cost", disabled=True),  # Computed
                    "delete": st.column_config.CheckboxColumn("Delete?")
                },
                key=f"logs_editor_{truck_id}"
            )
            if st.button("Save Log Changes"):
                # Deletes
                to_delete = edited_logs[edited_logs['delete'] == True]['id'].dropna()
                for d in to_delete:
                    delete_maintenance_log(int(d))
                # Adds/Updates
                for _, r in edited_logs[edited_logs['delete'] == False].iterrows():
                    total = r['material_cost'] + r['labor_cost']
                    if pd.isna(r['id']):
                        add_maintenance_log(truck_id, r['date'], r['description'], r['odometer'], r['service_provider'], r['mechanic'], r['part_no'], r['next_service_due'], r['material_cost'], r['labor_cost'], r['warranty'], total)
                    else:
                        update_maintenance_log(int(r['id']), truck_id, r['date'], r['description'], r['odometer'], r['service_provider'], r['mechanic'], r['part_no'], r['next_service_due'], r['material_cost'], r['labor_cost'], r['warranty'], total)
                st.success("Logs saved!")
                st.rerun()

# ======================
# Main App
# ======================
st.title("🚛 Fleet Management System")

# Sidebar Navigation
if 'page_select' not in st.session_state:
    st.session_state.page_select = "Fleet Overview"

page = st.sidebar.selectbox("Page", ["Fleet Overview", "Add Truck", "Manage Trucks", "Vehicle Detail"], key="page_select")

if page == "Fleet Overview":
    show_fleet_overview()
elif page == "Add Truck":
    show_add_truck()
elif page == "Manage Trucks":
    show_manage_trucks()
elif page == "Vehicle Detail":
    if 'selected_truck' in st.session_state and st.session_state.selected_truck is not None:
        show_vehicle_detail(st.session_state.selected_truck)
    else:
        st.info("Please select a vehicle from the Fleet Overview page to view details.")