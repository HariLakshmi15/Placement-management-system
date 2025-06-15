import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

class PlacementManagementSystem:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root123',
            database='placement_system'
        )
        self.cursor = self.conn.cursor()
        self.root = tk.Tk()
        self.root.title("Placement Management System")
        self.setup_main_window()
        self.root.mainloop()

    def setup_main_window(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack()
        ttk.Label(frame, text="Welcome to Placement Management System", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Button(frame, text="Register", command=self.open_register_page).pack(pady=5)
        ttk.Button(frame, text="Login", command=self.open_login_page).pack(pady=5)

    def open_register_page(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Register")
        entries = {}
        for field in ["Name", "Email", "Roll Number", "Password", "Branch", "CGPA"]:
            ttk.Label(reg_win, text=field).pack()
            ent = ttk.Entry(reg_win, show="*" if field == "Password" else None)
            ent.pack()
            entries[field] = ent
        def register():
            try:
                self.cursor.execute(
                    "INSERT INTO students (name, email, roll_number, password, branch, cgpa) VALUES (%s, %s, %s, %s, %s, %s)",
                    (entries["Name"].get(), entries["Email"].get(), entries["Roll Number"].get(),
                     entries["Password"].get(), entries["Branch"].get(), float(entries["CGPA"].get()))
                )
                self.conn.commit()
                messagebox.showinfo("Success", "Registration successful!")
                reg_win.destroy()
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Database error: {err}")
        ttk.Button(reg_win, text="Register", command=register).pack(pady=10)

    def open_login_page(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Login")
        ttk.Label(login_win, text="Email").pack()
        email_entry = ttk.Entry(login_win)
        email_entry.pack()
        ttk.Label(login_win, text="Password").pack()
        pass_entry = ttk.Entry(login_win, show="*")
        pass_entry.pack()
        def login():
            self.cursor.execute("SELECT * FROM students WHERE email=%s AND password=%s",
                                (email_entry.get(), pass_entry.get()))
            user = self.cursor.fetchone()
            if user:
                messagebox.showinfo("Success", f"Welcome, {user[1]}!")
                login_win.destroy()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        ttk.Button(login_win, text="Login", command=login).pack(pady=10)

if __name__ == "__main__":
    PlacementManagementSystem() 