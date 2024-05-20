import tkinter as tk
from tkinter import messagebox, simpledialog
from face_rec import capture_and_encode_face, load_face_encodings_from_firebase, compare_face_encodings
import firebase_admin.db
from cryptography.fernet import Fernet
import datetime
import json

class PasswordManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Password Manager")
        self.root.geometry("400x300")
        self.authenticated_user = None
        self.secret_key = self.load_or_generate_key()
        self.cipher_suite = Fernet(self.secret_key)
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.title_label = tk.Label(self.main_frame, text="Password Manager", font=("Helvetica", 16))
        self.title_label.pack(pady=20)

        self.new_user_button = tk.Button(self.main_frame, text="New User", command=self.new_user)
        self.new_user_button.pack(pady=5)

        self.existing_user_button = tk.Button(self.main_frame, text="Existing User", command=self.existing_user)
        self.existing_user_button.pack(pady=5)

    def load_or_generate_key(self):
        db_ref = firebase_admin.db.reference()
        key = db_ref.child("encryption_key").get()
        if key:
            return key.encode()
        else:
            new_key = Fernet.generate_key()
            db_ref.child("encryption_key").set(new_key.decode())
            return new_key

    def new_user(self):
        name = simpledialog.askstring("New User", "Enter your name:")
        if name:
            face_encoding = capture_and_encode_face()
            if face_encoding is not None:
                db_ref = firebase_admin.db.reference()
                db_ref.child("face_encodings").child(name).set([str(val) for val in face_encoding])
                messagebox.showinfo("Success", "New user created successfully!")
            else:
                messagebox.showerror("Error", "Failed to capture face encoding.")

    def existing_user(self):
        face_encoding = capture_and_encode_face()
        if face_encoding is not None:
            stored_encodings = load_face_encodings_from_firebase()
            matched_name = compare_face_encodings(face_encoding, stored_encodings)
            if matched_name:
                self.authenticated_user = matched_name
                self.show_passwords()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_access_attempt(matched_name, timestamp)
            else:
                messagebox.showerror("Error", "Face not recognized.")
        else:
            messagebox.showerror("Error", "Failed to capture face encoding.")

    def show_passwords(self):
        self.main_frame.pack_forget()
        self.passwords_frame = tk.Frame(self.root)
        self.passwords_frame.pack(fill=tk.BOTH, expand=True)

        self.title_label = tk.Label(self.passwords_frame, text="Saved Passwords", font=("Helvetica", 16))
        self.title_label.pack(pady=20)

        self.add_password_button = tk.Button(self.passwords_frame, text="Add Password", command=self.add_password)
        self.add_password_button.pack(pady=5)

        self.password_listbox = tk.Listbox(self.passwords_frame)
        self.password_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.load_passwords()

    def add_password(self):
        service = simpledialog.askstring("Add Password", "Enter service name:")
        username = simpledialog.askstring("Add Password", "Enter username:")
        password = simpledialog.askstring("Add Password", "Enter password:")
        if service and username and password:
            encrypted_password = self.cipher_suite.encrypt(password.encode()).decode()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_ref = firebase_admin.db.reference()
            db_ref.child("users").child(self.authenticated_user).child(service).set({
                "username": username,
                "password": encrypted_password,
                "last_modified": timestamp
            })
            self.load_passwords()
        else:
            messagebox.showerror("Error", "All fields are required.")

    def load_passwords(self):
        self.password_listbox.delete(0, tk.END)
        db_ref = firebase_admin.db.reference()
        user_data = db_ref.child("users").child(self.authenticated_user).get()
        if user_data:
            for service, details in user_data.items():
                decrypted_password = self.cipher_suite.decrypt(details["password"].encode()).decode()
                self.password_listbox.insert(tk.END, f"{service}: {details['username']} - {decrypted_password} (Last modified: {details['last_modified']})")

    def log_access_attempt(self, name, timestamp):
        access_log_ref = firebase_admin.db.reference('/access_log')
        access_log_ref.push({
            "name": name,
            "timestamp": timestamp
        })

    def run(self):
        self.root.mainloop()
