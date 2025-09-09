"""
Sample Data Generator for MuscleTone Fitness
Run this script to quickly populate your app with sample data for screenshots
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Database setup
DB_FOLDER = os.path.join(os.path.expanduser("~"), "MuscleToneFitness")
DB_NAME = os.path.join(DB_FOLDER, "gym_data.db")

# Sample members data
sample_members = [
    ("John Smith", "555-0101", "john.smith@email.com", "Premium Monthly", "Paid", "Trainer Mike", 2500, "Regular member, very dedicated"),
    ("Sarah Johnson", "555-0102", "sarah.johnson@email.com", "Gold (3-Month)", "Unpaid", "Trainer Lisa", 6000, "New member, needs guidance"),
    ("Mike Wilson", "555-0103", "mike.wilson@email.com", "Silver (6-Month)", "Partial", "Trainer David", 8000, "Experienced lifter"),
    ("Lisa Brown", "555-0104", "lisa.brown@email.com", "Bronze (Yearly)", "Paid", "Trainer Sarah", 15000, "VIP member, personal training"),
    ("David Lee", "555-0105", "david.lee@email.com", "Basic Monthly", "Unpaid", "Trainer John", 1500, "Student discount applied"),
    ("Emma Davis", "555-0106", "emma.davis@email.com", "Premium Monthly", "Paid", "Trainer Mike", 2500, "Yoga enthusiast"),
    ("Chris Taylor", "555-0107", "chris.taylor@email.com", "Gold (3-Month)", "Paid", "Trainer Lisa", 6000, "Weight loss program"),
    ("Anna Martinez", "555-0108", "anna.martinez@email.com", "Silver (6-Month)", "Unpaid", "Trainer David", 8000, "Crossfit training"),
    ("Robert Kim", "555-0109", "robert.kim@email.com", "Bronze (Yearly)", "Partial", "Trainer Sarah", 15000, "Bodybuilding competitor"),
    ("Jennifer White", "555-0110", "jennifer.white@email.com", "Basic Monthly", "Paid", "Trainer John", 1500, "Beginner, needs basic training"),
    ("Michael Garcia", "555-0111", "michael.garcia@email.com", "Premium Monthly", "Unpaid", "Trainer Mike", 2500, "Cardio focused"),
    ("Amanda Clark", "555-0112", "amanda.clark@email.com", "Gold (3-Month)", "Paid", "Trainer Lisa", 6000, "Prenatal fitness"),
]

def add_sample_data():
    """Add sample data to the database"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            
            # Clear existing data
            c.execute("DELETE FROM customers")
            print("🗑️ Cleared existing data")
            
            # Add sample members with varied dates
            today = datetime.today().date()
            
            for i, (name, phone, email, mtype, payment, trainer, amount, notes) in enumerate(sample_members):
                # Create varied start and end dates
                if i < 3:  # First 3 members - active, not expiring soon
                    start_date = (today - timedelta(days=15)).isoformat()
                    end_date = (today + timedelta(days=45)).isoformat()
                elif i < 6:  # Next 3 members - expiring soon
                    start_date = (today - timedelta(days=25)).isoformat()
                    end_date = (today + timedelta(days=5)).isoformat()
                elif i < 9:  # Next 3 members - expired
                    start_date = (today - timedelta(days=60)).isoformat()
                    end_date = (today - timedelta(days=10)).isoformat()
                else:  # Last 3 members - long-term active
                    start_date = (today - timedelta(days=10)).isoformat()
                    end_date = (today + timedelta(days=80)).isoformat()
                
                c.execute("""INSERT INTO customers
                    (name, phone, email, start_date, end_date, membership_type, payment_status, trainer, amount, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (name, phone, email, start_date, end_date, mtype, payment, trainer, amount, notes))
            
            print(f"✅ Added {len(sample_members)} sample members")
            print("📊 Sample data includes:")
            print("   - 3 Active members (not expiring soon)")
            print("   - 3 Members expiring soon")
            print("   - 3 Expired members")
            print("   - 3 Long-term active members")
            print("   - Various membership types and payment statuses")
            print("\n🏋️ Now run your app to see the populated data!")
            print("   Command: python maingym.py")
            
    except sqlite3.Error as e:
        print(f"❌ Error adding sample data: {e}")

def clear_sample_data():
    """Clear all data from the database"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM customers")
            print("🗑️ All data cleared from database")
    except sqlite3.Error as e:
        print(f"❌ Error clearing data: {e}")

if __name__ == "__main__":
    print("🏋️ MuscleTone Fitness - Sample Data Generator")
    print("=" * 50)
    
    choice = input("Choose an option:\n1. Add sample data\n2. Clear all data\n3. Exit\n\nEnter choice (1-3): ")
    
    if choice == "1":
        add_sample_data()
    elif choice == "2":
        clear_sample_data()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice. Please run the script again.")
