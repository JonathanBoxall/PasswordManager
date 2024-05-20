import cv2
import face_recognition as fr
import firebase_admin.db

# Load saved face encodings from Firebase Realtime Database
def load_face_encodings_from_firebase():
    db_ref = firebase_admin.db.reference()
    face_encodings = db_ref.child("face_encodings").get()
    
    encodings_dict = {}
    for name, encoding_parts in face_encodings.items():
        encoding = [float(val) for val in encoding_parts]
        encodings_dict[name] = encoding
    
    return encodings_dict

# Capture a single frame from webcam and encode the face
def capture_and_encode_face():
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = fr.face_locations(rgb_frame)

        if face_locations:
            face_encoding = fr.face_encodings(rgb_frame, [face_locations[0]])[0]
            video_capture.release()
            cv2.destroyAllWindows()
            return face_encoding

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return None

# Function to compare the captured face encoding with the encodings stored in the Firebase Realtime Database
def compare_face_encodings(captured_encoding, stored_encodings):
    for name, stored_encoding in stored_encodings.items():
        match = fr.compare_faces([stored_encoding], captured_encoding)
        if match[0]:
            print(f"Hello {name}, you have been authorised.")
            return name
    print("No match found. The captured face does not match any stored encoding, please seek admin support or try again.")
    return None

