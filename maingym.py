import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import csv
import shutil
import os
from tkinter import font

# ---------------- Database ----------------
DB_FOLDER = os.path.join(os.path.expanduser("~"), "MuscleToneFitness")
DB_NAME = os.path.join(DB_FOLDER, "gym_data.db")

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    membership_type TEXT,
                    payment_status TEXT,
                    trainer TEXT,
                    amount REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add amount column if it doesn't exist (for existing databases)
            try:
                c.execute("ALTER TABLE customers ADD COLUMN amount REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

# ---------------- Validation ----------------
def validate_date(s: str) -> bool:
    try:
        datetime.fromisoformat(s)
        return True
    except ValueError:
        return False

def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1] if email else True

def validate_phone(phone: str) -> bool:
    return phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit() if phone else True

def parse_dates(start_date: str, end_date: str):
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        return start_dt, end_dt
    except ValueError:
        return None, None

# ---------------- App State ----------------
class GymApp:
    def __init__(self):
        self.selected_id = None
        self.theme = "light"
        
    def set_selected_id(self, value):
        self.selected_id = value
        
    def get_selected_id(self):
        return self.selected_id

app_state = GymApp()

# ---------------- Modern Theme Colors ----------------
COLORS = {
    "primary": "#4A90E2",
    "secondary": "#7B68EE", 
    "success": "#50C878",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
    "white": "#FFFFFF",
    "gray": "#6C757D",
    "border": "#E9ECEF",
    "hover": "#E3F2FD",
    "gradient_start": "#667eea",
    "gradient_end": "#764ba2"
}

# ---------------- Enhanced UI Functions ----------------
def animate_button(button, original_color, hover_color):
    def on_enter(e):
        button.config(bg=hover_color, cursor="hand2")
    
    def on_leave(e):
        button.config(bg=original_color, cursor="")
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

def create_modern_button(parent, text, command, bg_color, width=15, height=1):
    button = tk.Button(
        parent, text=text, command=command, bg=bg_color, fg="white",
        font=("Segoe UI", 10, "bold"), width=width, height=height,
        relief="flat", bd=0, cursor="hand2", padx=20, pady=8
    )
    
    # Add hover effect
    hover_color = darken_color(bg_color, 0.8)
    animate_button(button, bg_color, hover_color)
    
    return button

def darken_color(color, factor):
    """Darken a hex color by a factor (0-1)"""
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    rgb = tuple(int(c * factor) for c in rgb)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def show_notification(message, msg_type="info"):
    """Show animated notification"""
    notification = tk.Toplevel(root)
    notification.title("Notification")
    notification.geometry("350x100")
    notification.resizable(False, False)
    
    # Center the notification
    notification.geometry("+{}+{}".format(
        root.winfo_rootx() + 50,
        root.winfo_rooty() + 50
    ))
    
    color = COLORS["success"] if msg_type == "success" else COLORS["primary"]
    notification.configure(bg=color)
    
    label = tk.Label(
        notification, text=message, bg=color, fg="white",
        font=("Segoe UI", 12, "bold"), wraplength=300
    )
    label.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Auto close after 3 seconds
    notification.after(3000, notification.destroy)

# ---------------- Statistics Functions ----------------
def get_statistics():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            
            # Total customers
            c.execute("SELECT COUNT(*) FROM customers")
            total = c.fetchone()[0]
            
            # Active memberships (not expired)
            today = datetime.today().date().isoformat()
            c.execute("SELECT COUNT(*) FROM customers WHERE end_date >= ?", (today,))
            active = c.fetchone()[0]
            
            # Expiring soon (within 7 days)
            week_later = (datetime.today().date() + timedelta(days=7)).isoformat()
            c.execute("SELECT COUNT(*) FROM customers WHERE end_date BETWEEN ? AND ?", (today, week_later))
            expiring = c.fetchone()[0]
            
            return {
                "total": total,
                "active": active,
                "expiring": expiring
            }
    except sqlite3.Error:
        return {"total": 0, "active": 0, "expiring": 0}

def create_stats_card(parent, title, value, color):
    frame = tk.Frame(parent, bg=color, relief="flat", bd=0)
    frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
    
    # Value
    value_label = tk.Label(frame, text=str(value), font=("Segoe UI", 28, "bold"), bg=color, fg="white")
    value_label.pack(pady=(20, 5))
    
    # Title
    title_label = tk.Label(frame, text=title, font=("Segoe UI", 12), bg=color, fg="white")
    title_label.pack(pady=(0, 20))
    
    return frame, value_label

# ---------------- CRUD Functions ----------------
def add_or_update_customer():
    selected_id = app_state.get_selected_id()
    name = name_var.get().strip()
    phone = phone_var.get().strip()
    email = email_var.get().strip()
    start_date = start_var.get().strip()
    end_date = end_var.get().strip()
    mtype = membership_var.get().strip()
    pstatus = payment_var.get().strip()
    trainer = trainer_var.get().strip()
    amount = amount_var.get().strip() or "0"
    notes = notes_text.get("1.0", tk.END).strip()

    # Enhanced validation
    if not name:
        messagebox.showerror("Validation Error", "Name is required.")
        return
    
    if not validate_email(email):
        messagebox.showerror("Validation Error", "Please enter a valid email address.")
        return
        
    if not validate_phone(phone):
        messagebox.showerror("Validation Error", "Please enter a valid phone number.")
        return
    
    if not (validate_date(start_date) and validate_date(end_date)):
        messagebox.showerror("Validation Error", "Dates must be in YYYY-MM-DD format.")
        return
    
    start_dt, end_dt = parse_dates(start_date, end_date)
    if start_dt is None or end_dt is None:
        messagebox.showerror("Validation Error", "Invalid date format.")
        return
    if start_dt is not None and end_dt is not None and end_dt < start_dt:
        messagebox.showerror("Validation Error", "End date cannot be before start date.")
        return
    
    # Validate amount
    try:
        float(amount)
    except ValueError:
        messagebox.showerror("Validation Error", "Amount must be a valid number.")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            if selected_id is None:
                c.execute("""INSERT INTO customers
                    (name, phone, email, start_date, end_date, membership_type, payment_status, trainer, amount, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (name, phone, email, start_date, end_date, mtype, pstatus, trainer, float(amount), notes))
                show_notification("Customer added successfully!", "success")
            else:
                c.execute("""UPDATE customers SET
                    name=?, phone=?, email=?, start_date=?, end_date=?, membership_type=?, payment_status=?, trainer=?, amount=?, notes=?
                    WHERE id=?""",
                    (name, phone, email, start_date, end_date, mtype, pstatus, trainer, float(amount), notes, selected_id))
                show_notification("Customer updated successfully!", "success")
                app_state.set_selected_id(None)
                add_btn.config(text="Add Member")
        
        clear_form()
        load_customers(search_var.get())
        update_dashboard()
        
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to save customer: {e}")

def update_plan():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a customer to update plan.")
        return
    
    values = tree.item(selected, "values")
    cid = values[0]
    customer_name = values[1]
    
    # Create popup window
    popup = tk.Toplevel(root)
    popup.title(f"Update Plan - {customer_name}")
    popup.geometry("500x400")
    popup.resizable(False, False)
    popup.configure(bg=COLORS["white"])
    popup.grab_set()
    
    # Center popup
    popup.geometry("+{}+{}".format(
        root.winfo_rootx() + 200,
        root.winfo_rooty() + 100
    ))
    
    # Variables for popup
    p_start = tk.StringVar(value=datetime.today().date().strftime("%Y-%m-%d"))
    p_end = tk.StringVar(value=(datetime.today().date() + timedelta(days=30)).strftime("%Y-%m-%d"))
    p_membership = tk.StringVar(value=membership_types[0])
    p_payment = tk.StringVar(value="Unpaid")
    p_trainer = tk.StringVar()
    p_amount = tk.StringVar()
    
    # Form fields
    tk.Label(popup, text=f"Update Plan for: {customer_name}", font=("Segoe UI", 14, "bold"), bg=COLORS["white"]).pack(pady=20)
    
    form = tk.Frame(popup, bg=COLORS["white"])
    form.pack(padx=30, pady=10, fill="both", expand=True)
    
    fields = [
        ("Start Date:", tk.Entry(form, textvariable=p_start, width=30)),
        ("End Date:", tk.Entry(form, textvariable=p_end, width=30)),
        ("Membership Type:", ttk.Combobox(form, textvariable=p_membership, values=membership_types, state="readonly", width=28)),
        ("Payment Status:", ttk.Combobox(form, textvariable=p_payment, values=payment_statuses, state="readonly", width=28)),
        ("Trainer:", tk.Entry(form, textvariable=p_trainer, width=30)),
        ("Amount:", tk.Entry(form, textvariable=p_amount, width=30))
    ]
    
    for i, (label, widget) in enumerate(fields):
        tk.Label(form, text=label, bg=COLORS["white"], font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", pady=8, padx=(0,10))
        widget.grid(row=i, column=1, sticky="ew", pady=8)
    
    form.grid_columnconfigure(1, weight=1)
    
    def save_plan():
        start_date = p_start.get().strip()
        end_date = p_end.get().strip()
        mtype = p_membership.get().strip()
        pstatus = p_payment.get().strip()
        trainer = p_trainer.get().strip()
        amount = p_amount.get().strip() or "0"
        
        # Validate
        if not (validate_date(start_date) and validate_date(end_date)):
            messagebox.showerror("Error", "Invalid date format.")
            return
        
        start_dt, end_dt = parse_dates(start_date, end_date)
        if start_dt is not None and end_dt is not None and end_dt < start_dt:
            messagebox.showerror("Error", "End date cannot be before start date.")
            return
        if start_dt is None or end_dt is None:
            messagebox.showerror("Error", "Invalid date format.")
            return        
        try:
            float(amount)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a valid number.")
            return
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("""UPDATE customers SET
                    start_date=?, end_date=?, membership_type=?, payment_status=?, trainer=?, amount=?
                    WHERE id=?""",
                    (start_date, end_date, mtype, pstatus, trainer, float(amount), cid))
            
            show_notification("Plan updated successfully!", "success")
            popup.destroy()
            load_customers(search_var.get())
            update_dashboard()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to update: {e}")
    
    # Buttons
    btn_frame = tk.Frame(popup, bg=COLORS["white"])
    btn_frame.pack(pady=20)
    
    create_modern_button(btn_frame, "Update Plan", save_plan, COLORS["success"]).pack(side="left", padx=10)
    create_modern_button(btn_frame, "Cancel", popup.destroy, COLORS["gray"]).pack(side="left", padx=10)

def delete_customer():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a customer to delete.")
        return
    
    values = tree.item(selected, "values")
    cid = values[0]
    
    if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{values[1]}'?\n\nThis action cannot be undone."):
        try:
            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM customers WHERE id=?", (cid,))
            
            show_notification("Customer deleted successfully!", "success")
            clear_form()
            load_customers(search_var.get())
            update_dashboard()
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete customer: {e}")

def configure_tree_tags():
    tree.tag_configure("even", background="#F8F9FA")
    tree.tag_configure("odd", background="#FFFFFF")
    tree.tag_configure("expiring", background="#FFF3CD", foreground="#856404")
    tree.tag_configure("expired", background="#F8D7DA", foreground="#721C24")
    tree.tag_configure("active", background="#D4EDDA", foreground="#155724")

def load_customers(search=""):
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            if search and search != "Search by name, phone, email, membership type...":
                query = f"%{search}%"
                c.execute("""SELECT id,name,phone,email,start_date,end_date,membership_type,payment_status,trainer,amount 
                    FROM customers 
                    WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? OR membership_type LIKE ? OR payment_status LIKE ? OR trainer LIKE ?
                    ORDER BY id DESC""",
                    (query, query, query, query, query, query))
            else:
                c.execute("""SELECT id,name,phone,email,start_date,end_date,membership_type,payment_status,trainer,amount 
                             FROM customers ORDER BY id DESC""")
            rows = c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to load customers: {e}")
        return

    today = datetime.today().date()
    for idx, row in enumerate(rows):
        try:
            end_date = datetime.fromisoformat(row[5]).date()
            start_date = datetime.fromisoformat(row[4]).date()
            days_left = (end_date - today).days
            duration = (end_date - start_date).days
            
            if days_left > 0:
                display_days = f"Active ({days_left}d left)"
            elif days_left == 0:
                display_days = "Expires today!"
            else:
                display_days = f"Expired ({abs(days_left)}d ago)"
            
            payment_status = row[7]
            amount = f"Rs{row[9]:.2f}" if row[9] is not None else "Rs 0.00"
            
            values = list(row[:7]) + [payment_status, row[8], amount, display_days]
            item_id = tree.insert("", "end", values=values)
            
            # Apply tags based on status
            if days_left < 0:
                tree.item(item_id, tags=("expired",))
            elif days_left <= 7:
                tree.item(item_id, tags=("expiring",))
            elif days_left > 7:
                tree.item(item_id, tags=("active",))
            else:
                tree.item(item_id, tags=("even" if idx % 2 == 0 else "odd",))
                
        except ValueError:
            continue

def clear_form():
    app_state.set_selected_id(None)
    name_var.set("")
    phone_var.set("")
    email_var.set("")
    today = datetime.today().date()
    start_var.set(today.strftime("%Y-%m-%d"))
    end_var.set((today + timedelta(days=30)).strftime("%Y-%m-%d"))
    membership_var.set(membership_types[0])
    payment_var.set(payment_statuses[0])
    trainer_var.set("")
    amount_var.set("")
    notes_text.delete("1.0", tk.END)
    add_btn.config(text="Add Member")

def on_row_select(event):
    selected = tree.focus()
    if not selected:
        return
    values = tree.item(selected, "values")
    if len(values) < 10:
        return
    
    app_state.set_selected_id(values[0])
    selected_id = values[0]
    name_var.set(values[1] if len(values) > 1 else "")
    phone_var.set(values[2] if len(values) > 2 else "")
    email_var.set(values[3] if len(values) > 3 else "")
    start_var.set(values[4] if len(values) > 4 else "")
    end_var.set(values[5] if len(values) > 5 else "")
    membership_var.set(values[6] if len(values) > 6 else membership_types[0])
    payment_clean = values[7] if len(values) > 7 else payment_statuses[0]
    payment_var.set(payment_clean)
    trainer_var.set(values[8] if len(values) > 8 else "")
    amount_clean = values[9].replace("Rs", "") if len(values) > 9 and values[9] else "0"
    amount_var.set(amount_clean)
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT notes FROM customers WHERE id=?", (selected_id,))
            result = c.fetchone()
            notes_text.delete("1.0", tk.END)
            if result and result[0]:
                notes_text.insert("1.0", result[0])
    except sqlite3.Error:
        pass
    
    add_btn.config(text="Update Member")

def export_to_csv():
    path = filedialog.asksaveasfilename(
        defaultextension=".csv", 
        filetypes=[("CSV Files","*.csv")],
        title="Export Customer Data"
    )
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID","Name","Phone","Email","Start Date","End Date","Membership Type","Payment","Trainer","Amount","Status"])
            for row_id in tree.get_children():
                writer.writerow(tree.item(row_id, "values"))
        show_notification(f"Data exported successfully to {os.path.basename(path)}", "success")
    except (IOError, PermissionError) as e:
        messagebox.showerror("Export Error", f"Failed to export data: {e}")

def backup_db():
    path = filedialog.asksaveasfilename(
        defaultextension=".db", 
        filetypes=[("SQLite DB","*.db")],
        title="Backup Database"
    )
    if not path:
        return
    try:
        shutil.copyfile(DB_NAME, path)
        show_notification(f"Database backed up to {os.path.basename(path)}", "success")
    except (IOError, PermissionError) as e:
        messagebox.showerror("Backup Error", f"Failed to backup database: {e}")

def restore_db():
    path = filedialog.askopenfilename(
        filetypes=[("SQLite DB","*.db")],
        title="Restore Database"
    )
    if not path:
        return
    if messagebox.askyesno("Confirm Restore","Restoring will overwrite current data. Continue?"):
        try:
            shutil.copyfile(path, DB_NAME)
            load_customers()
            update_dashboard()
            show_notification("Database restored successfully!", "success")
        except (IOError, PermissionError) as e:
            messagebox.showerror("Restore Error", f"Failed to restore database: {e}")

def update_dashboard():
    stats = get_statistics()
    total_label.config(text=str(stats["total"]))
    active_label.config(text=str(stats["active"]))
    expiring_label.config(text=str(stats["expiring"]))

# UI Setup
root = tk.Tk()
root.title("MuscleTone Fitness - Premium Gym Manager")
root.state("zoomed")
root.configure(bg=COLORS["light"])

title_font = font.Font(family="Segoe UI", size=24, weight="bold")
subtitle_font = font.Font(family="Segoe UI", size=12)
button_font = font.Font(family="Segoe UI", size=10, weight="bold")

header_frame = tk.Frame(root, bg=COLORS["primary"], height=100)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="MuscleTone Fitness", font=title_font, 
                      bg=COLORS["primary"], fg="white")
title_label.place(relx=0.5, rely=0.3, anchor="center")

subtitle_label = tk.Label(header_frame, text="Premium Gym Management System", font=subtitle_font, 
                         bg=COLORS["primary"], fg="white")
subtitle_label.place(relx=0.5, rely=0.7, anchor="center")

main_frame = tk.Frame(root, bg=COLORS["light"])
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

style = ttk.Style()
style.theme_use('clam')
style.configure('Custom.TNotebook', background=COLORS["light"], borderwidth=0)
style.configure('Custom.TNotebook.Tab', padding=[20, 12], font=button_font, 
               background=COLORS["white"], focuscolor='none')
style.map('Custom.TNotebook.Tab', background=[('selected', COLORS["primary"]), ('active', COLORS["hover"])],
         foreground=[('selected', 'white'), ('active', COLORS["dark"])])

notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
notebook.pack(fill="both", expand=True)

dashboard_tab = tk.Frame(notebook, bg=COLORS["light"])
notebook.add(dashboard_tab, text="Dashboard")

stats_frame = tk.Frame(dashboard_tab, bg=COLORS["light"])
stats_frame.pack(fill="x", padx=30, pady=30)

stats = get_statistics()
_, total_label = create_stats_card(stats_frame, "Total Members", stats["total"], COLORS["primary"])
_, active_label = create_stats_card(stats_frame, "Active Members", stats["active"], COLORS["success"])
_, expiring_label = create_stats_card(stats_frame, "Expiring Soon", stats["expiring"], COLORS["warning"])

actions_frame = tk.LabelFrame(dashboard_tab, text="Quick Actions", font=button_font, bg=COLORS["white"], fg=COLORS["dark"])
actions_frame.pack(fill="x", padx=30, pady=(0, 30))

quick_actions = tk.Frame(actions_frame, bg=COLORS["white"])
quick_actions.pack(pady=20)

create_modern_button(quick_actions, "Add New Member", lambda: notebook.select(1), COLORS["success"]).pack(side="left", padx=10)
create_modern_button(quick_actions, "View All Members", lambda: notebook.select(2), COLORS["primary"]).pack(side="left", padx=10)
create_modern_button(quick_actions, "Export Data", export_to_csv, COLORS["secondary"]).pack(side="left", padx=10)
create_modern_button(quick_actions, "Backup Database", backup_db, COLORS["warning"]).pack(side="left", padx=10)

tab1 = tk.Frame(notebook, bg=COLORS["light"])
notebook.add(tab1, text="Add/Edit Member")

name_var = tk.StringVar()
phone_var = tk.StringVar()
email_var = tk.StringVar()
start_var = tk.StringVar()
end_var = tk.StringVar()
membership_var = tk.StringVar()
payment_var = tk.StringVar()
trainer_var = tk.StringVar()
amount_var = tk.StringVar()

membership_types = ["Premium Monthly","Gold (3-Month)","Silver (6-Month)","Bronze (Yearly)","Basic Monthly"]
payment_statuses = ["Paid","Unpaid","Partial"]

today = datetime.today().date()
start_var.set(today.strftime("%Y-%m-%d"))
end_var.set((today+timedelta(days=30)).strftime("%Y-%m-%d"))
membership_var.set(membership_types[0])
payment_var.set(payment_statuses[0])

canvas = tk.Canvas(tab1, bg=COLORS["light"])
scrollbar = ttk.Scrollbar(tab1, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=COLORS["light"])

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def bind_mousewheel(widget):
    widget.bind("<MouseWheel>", on_mousewheel)
    for child in widget.winfo_children():
        bind_mousewheel(child)

canvas.bind("<MouseWheel>", on_mousewheel)
scrollable_frame.bind("<MouseWheel>", on_mousewheel)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

form_frame = tk.LabelFrame(scrollable_frame, text="Member Information", padx=30, pady=30, 
                          bg=COLORS["white"], fg=COLORS["dark"], font=("Segoe UI", 14, "bold"))
form_frame.pack(fill="both", expand=True, padx=30, pady=30)

form_frame.bind("<MouseWheel>", on_mousewheel)

for i in range(10):
    form_frame.grid_rowconfigure(i, weight=0, pad=5)
form_frame.grid_columnconfigure(0, weight=0, minsize=200)
form_frame.grid_columnconfigure(1, weight=1, minsize=400)

labels = ["Full Name *","Phone Number","Email Address","Start Date *","End Date *","Membership Type","Payment Status","Personal Trainer","Amount","Notes"]

def create_modern_entry(parent, textvariable, width=45):
    entry = tk.Entry(parent, textvariable=textvariable, width=width, font=("Segoe UI", 11),
                    relief="solid", bd=1, highlightthickness=1, highlightcolor=COLORS["primary"],
                    insertbackground=COLORS["dark"], bg=COLORS["white"], fg=COLORS["dark"])
    return entry

widgets = [
    create_modern_entry(form_frame, name_var),
    create_modern_entry(form_frame, phone_var),
    create_modern_entry(form_frame, email_var),
    create_modern_entry(form_frame, start_var),
    create_modern_entry(form_frame, end_var),
    ttk.Combobox(form_frame, textvariable=membership_var, values=membership_types, state="readonly", width=43, font=("Segoe UI", 11)),
    ttk.Combobox(form_frame, textvariable=payment_var, values=payment_statuses, state="readonly", width=43, font=("Segoe UI", 11)),
    create_modern_entry(form_frame, trainer_var),
    create_modern_entry(form_frame, amount_var),
    None
]

for i, label in enumerate(labels):
    label_widget = tk.Label(form_frame, text=label, font=("Segoe UI", 12, "bold"), 
                           bg=COLORS["white"], fg=COLORS["dark"], anchor="w")
    label_widget.grid(row=i, column=0, sticky="w", padx=(20, 15), pady=12)
    
    if widgets[i]:
        widgets[i].grid(row=i, column=1, sticky="ew", padx=(15, 20), pady=10, ipady=5)

notes_text = tk.Text(form_frame, height=4, width=50, font=("Segoe UI", 11), 
                    relief="solid", bd=2, highlightthickness=2, highlightcolor=COLORS["primary"],
                    bg=COLORS["white"], fg=COLORS["dark"], insertbackground=COLORS["dark"])
notes_text.grid(row=9, column=1, sticky="ew", padx=(15, 20), pady=10, ipady=5)

bind_mousewheel(form_frame)

btn_frame = tk.Frame(form_frame, bg=COLORS["white"])
btn_frame.grid(row=10, column=0, columnspan=2, pady=30, sticky="ew")
btn_frame.grid_columnconfigure(0, weight=1)

button_container = tk.Frame(btn_frame, bg=COLORS["white"])
button_container.pack(expand=True)

add_btn = create_modern_button(button_container, "Add Member", add_or_update_customer, COLORS["success"], width=18)
add_btn.pack(side="left", padx=15)

create_modern_button(button_container, "Update Plan", update_plan, COLORS["secondary"], width=15).pack(side="left", padx=15)
create_modern_button(button_container, "Clear Form", clear_form, COLORS["gray"], width=15).pack(side="left", padx=15)
create_modern_button(button_container, "Export CSV", export_to_csv, COLORS["primary"], width=15).pack(side="left", padx=15)
create_modern_button(button_container, "Backup", backup_db, COLORS["warning"], width=12).pack(side="left", padx=15)
create_modern_button(button_container, "Restore", restore_db, COLORS["danger"], width=12).pack(side="left", padx=15)

tab2 = tk.Frame(notebook, bg=COLORS["light"])
notebook.add(tab2, text="Members List")

search_frame = tk.Frame(tab2, bg=COLORS["white"], relief="flat", bd=0)
search_frame.pack(fill="x", pady=15, padx=20)

search_inner = tk.Frame(search_frame, bg=COLORS["white"])
search_inner.pack(fill="x", padx=10, pady=10)

tk.Label(search_inner, text="Search:", font=("Segoe UI", 12, "bold"), bg=COLORS["white"]).pack(side="left", padx=(0, 10))

search_var = tk.StringVar()
search_entry = tk.Entry(search_inner, textvariable=search_var, width=80, font=("Segoe UI", 12),
                       relief="solid", bd=1, highlightthickness=1, highlightcolor=COLORS["primary"],
                       bg=COLORS["white"], fg=COLORS["dark"], insertbackground=COLORS["primary"])
search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

search_btn = create_modern_button(search_inner, "Search", lambda: load_customers(search_var.get()), COLORS["primary"], width=10)
search_btn.pack(side="left")

placeholder_text = "Search by name, phone, email, membership type..."
search_entry.insert(0, placeholder_text)
search_entry.config(fg="gray")

def on_search_focus_in(event):
    if search_entry.get() == placeholder_text:
        search_entry.delete(0, tk.END)
        search_entry.config(fg="black")

def on_search_focus_out(event):
    if not search_entry.get():
        search_entry.insert(0, placeholder_text)
        search_entry.config(fg="gray")

search_entry.bind("<FocusIn>", on_search_focus_in)
search_entry.bind("<FocusOut>", on_search_focus_out)

def on_search(*args):
    load_customers(search_var.get())

search_var.trace("w", on_search)

table_frame = tk.Frame(tab2, bg=COLORS["white"], relief="flat", bd=0)
table_frame.pack(fill="both", expand=True, padx=20, pady=10)

COLUMN_WIDTHS = {
    "ID": 80, "Name": 200, "Phone": 130, "Email": 220, 
    "Start": 110, "End": 110, "Type": 160, "Payment": 120, 
    "Trainer": 140, "Amount": 100, "Status": 180
}

cols = ("ID","Name","Phone","Email","Start","End","Type","Payment","Trainer","Amount","Status")
tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse", height=15)

style.configure("Treeview", background=COLORS["white"], foreground=COLORS["dark"], 
               fieldbackground=COLORS["white"], borderwidth=0)
style.configure("Treeview.Heading", background=COLORS["primary"], foreground="white", 
               font=("Segoe UI", 10, "bold"), borderwidth=1, relief="flat")
style.map("Treeview", background=[('selected', COLORS["primary"])])

for col in cols:
    tree.heading(col, text=col)
    tree.column(col, width=COLUMN_WIDTHS.get(col, 120), anchor="w")

vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")

table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

tree.bind("<Double-1>", on_row_select)

action_frame = tk.Frame(tab2, bg=COLORS["light"])
action_frame.pack(pady=15)

create_modern_button(action_frame, "Delete Selected", delete_customer, COLORS["danger"]).pack(side="left", padx=10)
create_modern_button(action_frame, "Edit Selected", lambda: on_row_select(None), COLORS["primary"]).pack(side="left", padx=10)
create_modern_button(action_frame, "Update Plan", update_plan, COLORS["secondary"]).pack(side="left", padx=10)
create_modern_button(action_frame, "Refresh List", lambda: load_customers(), COLORS["secondary"]).pack(side="left", padx=10)

init_db()
configure_tree_tags()
load_customers()
update_dashboard()

root.mainloop()