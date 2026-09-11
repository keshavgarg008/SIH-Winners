import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import json
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Face Security System",
    layout="centered"
)

# ============================================================
# FETCH FIREBASE LOGS LOGIC (For Dashboard)
# ============================================================
def fetch_firebase_logs():
    url = "https://firestore.googleapis.com/v1/projects/yatrisathi-4e0fb/databases/(default)/documents/permanent_logs"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            parsed_logs = []
            for doc in documents:
                fields = doc.get("fields", {})
                
                user_id = fields.get("userId", {}).get("stringValue", "Unknown")
                hotel_id = fields.get("hotelId", {}).get("stringValue", "Unknown")
                timestamp_str = fields.get("timestamp", {}).get("timestampValue", "")
                
                if timestamp_str:
                    try:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %I:%M %p")
                    except:
                        formatted_time = timestamp_str
                else:
                    formatted_time = "Unknown Time"

                parsed_logs.append({
                    "Citizen Name": user_id,
                    "Hotel ID": hotel_id,
                    "Check-In Time": formatted_time
                })
            
            return pd.DataFrame(parsed_logs)
    except Exception as e:
        st.error(f"Failed to fetch database: {e}")
    return pd.DataFrame()


# ============================================================
# TITLE & TABS
# ============================================================
st.title("Face Security System")

tab1, tab2 = st.tabs(["📷 Camera Kiosk", "🏛️ Gov Admin Dashboard"])

# ============================================================
# TAB 2: GOVERNMENT ADMIN DASHBOARD
# ============================================================
with tab2:
    st.header("Government Surveillance Dashboard")
    st.write("Live data pulled securely from Firebase.")
    
    if st.button("🔄 Refresh Live Data"):
        st.rerun()

    df_logs = fetch_firebase_logs()

    if df_logs.empty:
        st.info("No check-in records found in the database yet.")
    else:
        df_logs = df_logs.sort_values(by="Check-In Time", ascending=False)
        st.markdown("---")
        
        # FEATURE: VIEW BY HOTEL
        st.subheader("🏢 View Hotel Guest List")
        unique_hotels = df_logs["Hotel ID"].unique().tolist()
        selected_hotel_dash = st.selectbox("Select a Hotel:", ["-- Select Hotel --"] + unique_hotels)
        
        if selected_hotel_dash != "-- Select Hotel --":
            hotel_guests = df_logs[df_logs["Hotel ID"] == selected_hotel_dash]
            st.success(f"Found {len(hotel_guests)} records for {selected_hotel_dash}")
            st.dataframe(hotel_guests[["Citizen Name", "Check-In Time"]], use_container_width=True)

        st.markdown("---")

        # FEATURE: VIEW BY CITIZEN
        st.subheader("👤 Citizen Movement History")
        unique_citizens = df_logs["Citizen Name"].unique().tolist()
        selected_citizen = st.selectbox("Select a Citizen:", ["-- Select Citizen --"] + unique_citizens)
        
        if selected_citizen != "-- Select Citizen --":
            citizen_history = df_logs[df_logs["Citizen Name"] == selected_citizen]
            st.warning(f"Found {len(citizen_history)} travel records for {selected_citizen}")
            st.dataframe(citizen_history[["Hotel ID", "Check-In Time"]], use_container_width=True)


# ============================================================
# TAB 1: KIOSK FRONTEND
# ============================================================
with tab1:
    # ============================================================
    # EXISTING REGISTERED FACES
    # ============================================================
    faces_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "faces"
    )

    registered_faces = []

    if os.path.exists(faces_folder):
        for filename in os.listdir(faces_folder):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                filepath = os.path.join(faces_folder, filename)
                try:
                    with open(filepath, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    extension = filename.lower().split(".")[-1]
                    mime_type = "image/png" if extension == "png" else "image/jpeg"
                    registered_faces.append({
                        "name": os.path.splitext(filename)[0],
                        "image": f"data:{mime_type};base64,{image_data}"
                    })
                except Exception as e:
                    print("Error loading:", filename, e)

    registered_faces_json = json.dumps(registered_faces)

    # ============================================================
    # HTML + JAVASCRIPT
    # ============================================================
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>
    <style>
    body {{ font-family: Arial, sans-serif; }}
    .container {{ padding: 10px; }}
    video {{ width: 100%; max-width: 500px; border-radius: 12px; border: 2px solid #555; transform: scaleX(-1); }}
    button {{ padding: 12px 18px; margin: 6px 4px; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; }}
    .register {{ background: #2196F3; color: white; }}
    .verify {{ background: #4CAF50; color: white; }}
    .stop {{ background: #f44336; color: white; }}
    input {{ padding: 12px; width: 90%; max-width: 400px; border-radius: 7px; border: 1px solid #aaa; font-size: 15px; }}
    #status {{ margin-top: 15px; padding: 12px; border-radius: 8px; background: #eeeeee; }}
    #result {{ margin-top: 15px; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: bold; }}
    </style>
    </head>
    <body>
    <div class="container">
    <h2>Select Hotel</h2>
    <select id="hotelSelect" style="padding: 10px; font-size: 16px; border-radius: 5px;">
        <option value="HOTEL_001">Hotel Royal</option>
        <option value="HOTEL_002">Hotel Paradise</option>
    </select>
    <br><br>
    <h2>Camera</h2>
    <video id="video" autoplay muted playsinline></video>
    <br>
    <button class="verify" onclick="startCamera()">Start Camera</button>
    <button class="stop" onclick="stopCamera()">Stop Camera</button>
    <hr>
    <h2>Register New Person</h2>
    <input type="text" id="personName" placeholder="Enter person's name">
    <br>
    <button class="register" onclick="registerPerson()">Register Face</button>
    <hr>
    <h2>Verify Face</h2>
    <button class="verify" onclick="verifyPerson()">Verify Face</button>
    <div id="status">Loading face recognition models...</div>
    <div id="result"></div>
    </div>

    <script>
    const existingUsers = {registered_faces_json};
    const STORAGE_KEY = "face_security_users";
    let video = document.getElementById("video");
    let stream = null;
    const MODEL_URL = "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@0.22.2/weights";

    async function loadModels() {{
        try {{
            document.getElementById("status").innerText = "Loading face detection model...";
            await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
            document.getElementById("status").innerText = "Loading face landmark model...";
            await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
            document.getElementById("status").innerText = "Loading face recognition model...";
            await faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL);
            document.getElementById("status").innerText = "Models loaded successfully.";
        }} catch(error) {{
            console.error(error);
            document.getElementById("status").innerText = "Model loading failed. Check your internet connection.";
        }}
    }}

    function getSavedUsers() {{
        try {{
            const data = localStorage.getItem(STORAGE_KEY);
            if (!data) return [];
            return JSON.parse(data);
        }} catch(error) {{
            console.error(error);
            return [];
        }}
    }}

    function saveUsers(users) {{
        localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
    }}

    function getAllUsers() {{
        const savedUsers = getSavedUsers();
        const allUsers = [];
        for (const user of existingUsers) {{
            allUsers.push({{ name: user.name, image: user.image, descriptor: null, existing: true, hotelId: "HOTEL_001" }});
        }}
        for (const user of savedUsers) {{
            allUsers.push({{ name: user.name, image: null, descriptor: user.descriptor, existing: false, hotelId: user.hotelId || "HOTEL_001" }});
        }}
        return allUsers;
    }}

    function getSelectedHotel() {{
        return document.getElementById("hotelSelect").value;
    }}

    async function startCamera() {{
        try {{
            if (stream) return;
            stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
            video.srcObject = stream;
            document.getElementById("status").innerText = "Camera started for " + getSelectedHotel() + ". Look at the camera.";
        }} catch(error) {{
            console.error(error);
            document.getElementById("status").innerText = "Camera permission denied or camera unavailable.";
        }}
    }}

    function stopCamera() {{
        if (stream) {{
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            video.srcObject = null;
        }}
        document.getElementById("status").innerText = "Camera stopped.";
    }}

    async function getCameraDescriptor() {{
        if (!stream) {{
            await startCamera();
            await new Promise(resolve => setTimeout(resolve, 1500));
        }}
        const detection = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({{ inputSize: 320, scoreThreshold: 0.5 }}))
            .withFaceLandmarks().withFaceDescriptor();
        
        if (!detection) {{
            document.getElementById("result").innerHTML = "❌ No face detected.<br><br>Please look directly at the camera.";
            return null;
        }}
        return Array.from(detection.descriptor);
    }}

    async function registerPerson() {{
        const nameInput = document.getElementById("personName");
        const name = nameInput.value.trim();
        if (!name) {{
            document.getElementById("result").innerHTML = "❌ Please enter a name.";
            return;
        }}
        document.getElementById("status").innerText = "Capturing face...";
        const descriptor = await getCameraDescriptor();
        if (!descriptor) return;

        const allUsers = getAllUsers();
        const alreadyExists = allUsers.some(user => user.name.toLowerCase() === name.toLowerCase());
        if (alreadyExists) {{
            document.getElementById("result").innerHTML = "❌ This name is already registered.";
            return;
        }}

        const savedUsers = getSavedUsers();
        const selectedHotel = getSelectedHotel();
        savedUsers.push({{ name: name, descriptor: descriptor, hotelId: selectedHotel }});
        saveUsers(savedUsers);
        nameInput.value = "";
        
        document.getElementById("status").innerText = "Face saved. Backing up to government database...";

        // ========================================================
        // DIRECT FIRESTORE LOGGING: CLEAN CITIZEN ID
        // ========================================================
        const shortId = Math.floor(1000 + Math.random() * 9000);
        const safeName = name.replace(/[^a-zA-Z0-9]/g, '_');
        const customDocId = safeName + "_" + shortId;
        
        const citizenUrl = "https://firestore.googleapis.com/v1/projects/yatrisathi-4e0fb/databases/(default)/documents/government_citizens?documentId=" + customDocId;

        fetch(citizenUrl, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
                fields: {{
                    fullName: {{ stringValue: name }},
                    taxStatus: {{ stringValue: "Clear" }},
                    registeredAt: {{ timestampValue: new Date().toISOString() }}
                }}
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.name) {{
                document.getElementById("status").innerText = "✅ Citizen permanently registered in Government Vault.";
            }} else {{
                console.error("Firestore Error:", data);
                document.getElementById("status").innerText = "⚠️ Registered locally, but cloud backup failed.";
            }}
        }})
        .catch(err => {{
            console.error("Connection error:", err);
            document.getElementById("status").innerText = "⚠️ Network error while backing up citizen.";
        }});

        document.getElementById("result").innerHTML = "✅ <b>Registration Successful!</b><br><br>" + name + " has been registered for " + getSelectedHotel() + ".";
    }}

    function euclideanDistance(descriptor1, descriptor2) {{
        let sum = 0;
        for (let i = 0; i < descriptor1.length; i++) {{
            const difference = descriptor1[i] - descriptor2[i];
            sum += difference * difference;
        }}
        return Math.sqrt(sum);
    }}

    async function getImageDescriptor(imageSource) {{
        try {{
            const image = new Image();
            image.src = imageSource;
            await new Promise((resolve, reject) => {{ image.onload = resolve; image.onerror = reject; }});
            const detection = await faceapi.detectSingleFace(image, new faceapi.TinyFaceDetectorOptions({{ inputSize: 320, scoreThreshold: 0.5 }}))
                .withFaceLandmarks().withFaceDescriptor();
            if (!detection) return null;
            return Array.from(detection.descriptor);
        }} catch(error) {{
            console.error(error);
            return null;
        }}
    }}

    async function verifyPerson() {{
        document.getElementById("result").innerHTML = "";
        document.getElementById("status").innerText = "Checking face...";
        const cameraDescriptor = await getCameraDescriptor();
        if (!cameraDescriptor) return;

        const users = getAllUsers();
        const selectedHotel = getSelectedHotel();
        const hotelUsers = users.filter(user => user.hotelId === selectedHotel);

        if (hotelUsers.length === 0) {{
            document.getElementById("result").innerHTML = "❌ No registered faces found.";
            return;
        }}

        let bestMatch = null;
        let bestDistance = Infinity;

        for (const user of hotelUsers) {{
            let registeredDescriptor = null;
            if (!user.existing && user.descriptor) {{
                registeredDescriptor = new Float32Array(user.descriptor);
            }} else if (user.existing && user.image) {{
                registeredDescriptor = await getImageDescriptor(user.image);
            }}
            if (!registeredDescriptor) continue;

            const distance = euclideanDistance(cameraDescriptor, registeredDescriptor);
            console.log(user.name + " distance = " + distance);
            
            if (distance < bestDistance) {{
                bestDistance = distance;
                bestMatch = user.name;
            }}
        }}

        const MATCH_THRESHOLD = 0.50;

        if (bestMatch !== null && bestDistance <= MATCH_THRESHOLD) {{
            document.getElementById("status").innerText = "Recording check-in with government server...";
            document.getElementById("result").innerHTML = "✅ <b>ACCESS GRANTED</b><br><br>Welcome, " + bestMatch + "<br><br>Match distance: " + bestDistance.toFixed(3);

            // ========================================================
            // DIRECT FIRESTORE LOGGING: CLEAN LOG ID
            // ========================================================
            const safeMatchName = bestMatch.replace(/[^a-zA-Z0-9]/g, '_');
            const shortLogId = Math.floor(1000 + Math.random() * 9000);
            const customLogDocId = safeMatchName + "_Log_" + shortLogId;
            
            const firestoreUrl = "https://firestore.googleapis.com/v1/projects/yatrisathi-4e0fb/databases/(default)/documents/permanent_logs?documentId=" + customLogDocId;
            
            fetch(firestoreUrl, {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{
                    fields: {{
                        userId: {{ stringValue: bestMatch }},
                        hotelId: {{ stringValue: getSelectedHotel() }},
                        confidenceScore: {{ doubleValue: Number((1 - bestDistance).toFixed(2)) }},
                        timestamp: {{ timestampValue: new Date().toISOString() }}
                    }}
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.name) {{
                    document.getElementById("status").innerText = "✅ " + bestMatch + " officially verified & logged in government vault!";
                }} else {{
                    console.error("Firestore Error:", data);
                    document.getElementById("status").innerText = "⚠️ Face matched, but database logging failed.";
                }}
            }})
            .catch(err => {{
                console.error("Connection error:", err);
                document.getElementById("status").innerText = "⚠️ Network error while saving log.";
            }});
        }} else {{
            document.getElementById("status").innerText = "Face not recognized.";
            document.getElementById("result").innerHTML = "❌ <b>ACCESS DENIED</b><br><br>This face is not registered.";
        }}
    }}

    loadModels();
    </script>
    </body>
    </html>
    """

    # ============================================================
    # DISPLAY HTML
    # ============================================================
    components.html(
        html_code,
        height=800,
        scrolling=True
    )