import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, db
import pyrebase_config as pbc
from gui import PasswordManagerApp

# Initialize Pyrebase
config = pbc.config
firebase = pyrebase.initialize_app(config)
auth_pyrebase = firebase.auth()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("certificate.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://facerecproj-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Authenticate user with email and password
email = pbc.email
password = pbc.password
try:
    user = auth_pyrebase.sign_in_with_email_and_password(email, password)
    id_token = user['idToken']
    print('Successfully authenticated user')
except Exception as e:
    print('Authentication failed:', e)
    exit()

# Verify ID token and get user UID
def verify_id_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        print('Successfully verified ID token:', uid)
        return uid
    except Exception as e:
        print('Error verifying ID token:', e)
    return None

authenticated_user_uid = verify_id_token(id_token)
if authenticated_user_uid is None:
    print("ID token verification failed!")
    exit()

# Start the GUI application
app = PasswordManagerApp()
app.run()
