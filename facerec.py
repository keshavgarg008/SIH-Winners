import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import json

st.set_page_config(
    page_title="Face Security",
    page_icon="🔐",
    layout="centered"
)

st.title("Face Recognition Security System")

# =========================================================
# 1. READ REGISTERED PHOTOS FROM faces FOLDER
# =========================================================

faces_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "faces"
)

registered_faces = []

if not os.path.exists(faces_folder):
    st.error("❌ 'faces' folder nahi mila.")
    st.code(faces_folder)
    st.stop()

for filename in os.listdir(faces_folder):

    if filename.lower().endswith((".jpg", ".jpeg", ".png")):

        filepath = os.path.join(faces_folder, filename)

        try:
            with open(filepath, "rb") as image_file:
                encoded_image = base64.b64encode(
                    image_file.read()
                ).decode("utf-8")

            if filename.lower().endswith(".png"):
                mime_type = "image/png"
            else:
                mime_type = "image/jpeg"

            name = os.path.splitext(filename)[0]

            registered_faces.append({
                "name": name,
                "image": f"data:{mime_type};base64,{encoded_image}"
            })

        except Exception as e:
            st.warning(f"{filename} load nahi hua: {e}")


# =========================================================
# 2. SHOW REGISTERED PEOPLE
# =========================================================

if len(registered_faces) == 0:

    st.error("❌ No registered faces found.")
    st.write("faces folder mein JPG/PNG photos rakho.")

    st.stop()

else:

    st.success(
        f"✅ {len(registered_faces)} registered face(s) found."
    )

    names = [person["name"] for person in registered_faces]

    st.write(
        "Registered users:",
        ", ".join(names)
    )


# =========================================================
# 3. SEND PHOTOS TO JAVASCRIPT
# =========================================================

registered_faces_json = json.dumps(
    registered_faces
)


# =========================================================
# 4. FACE RECOGNITION WEB APP
# =========================================================

html_code = f"""
<!DOCTYPE html>

<html>

<head>

<script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>

<style>

body {{
    font-family: Arial, sans-serif;
    text-align: center;
}}

video {{
    width: 90%;
    max-width: 500px;
    border-radius: 15px;
    margin: 15px;
}}

button {{
    padding: 12px 25px;
    margin: 8px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
}}

#startButton {{
    background: #333;
    color: white;
}}

#verifyButton {{
    background: #1877f2;
    color: white;
}}

#status {{
    font-size: 17px;
    margin: 15px;
}}

#result {{
    font-size: 25px;
    font-weight: bold;
    margin: 20px;
}}

</style>

</head>


<body>

<h2>📷 Security Camera</h2>

<button id="startButton">
Start Camera
</button>

<br>

<video
    id="video"
    autoplay
    muted
    playsinline>
</video>

<br>

<button id="verifyButton">
Verify Face
</button>

<div id="status">
Loading...
</div>

<div id="result">
</div>


<script>

// =========================================================
// REGISTERED PEOPLE FROM PYTHON
// =========================================================

const registeredPeople =
{registered_faces_json};


// =========================================================
// VARIABLES
// =========================================================

const video =
document.getElementById("video");

const status =
document.getElementById("status");

const result =
document.getElementById("result");

let registeredDescriptors = [];


// =========================================================
// MODEL LOCATION
// =========================================================

const MODEL_URL =
"https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@0.22.2/weights";


// =========================================================
// LOAD MODELS
// =========================================================

async function loadModels() {{

    try {{

        status.innerText =
        "Loading face recognition models...";


        await faceapi.nets.tinyFaceDetector.loadFromUri(
            MODEL_URL
        );


        await faceapi.nets.faceLandmark68Net.loadFromUri(
            MODEL_URL
        );


        await faceapi.nets.faceRecognitionNet.loadFromUri(
            MODEL_URL
        );


        status.innerText =
        "Loading registered faces...";


        await loadRegisteredFaces();


        status.innerText =
        "✅ Ready. Start camera.";

    }}

    catch(error) {{

        console.error(error);

        status.innerText =
        "❌ Model loading failed.";

    }}

}}


// =========================================================
// LOAD ALL REGISTERED FACES
// =========================================================

async function loadRegisteredFaces() {{

    registeredDescriptors = [];


    for (
        const person of registeredPeople
    ) {{

        try {{

            const image =
            new Image();


            image.src =
            person.image;


            await new Promise(
                (resolve, reject) => {{

                    image.onload = resolve;

                    image.onerror = reject;

                }}
            );


            const detection =
            await faceapi
            .detectSingleFace(
                image,
                new faceapi.TinyFaceDetectorOptions()
            )
            .withFaceLandmarks()
            .withFaceDescriptor();


            if (detection) {{

                registeredDescriptors.push({{

                    name: person.name,

                    descriptor:
                    detection.descriptor

                }});

                console.log(
                    "Registered:",
                    person.name
                );

            }}

            else {{

                console.log(
                    "No face found in:",
                    person.name
                );

            }}

        }}

        catch(error) {{

            console.error(
                "Error loading:",
                person.name,
                error
            );

        }}

    }}


    console.log(
        "Total registered faces:",
        registeredDescriptors.length
    );

}}


// =========================================================
// START CAMERA
// =========================================================

document
.getElementById("startButton")
.addEventListener(
    "click",
    async function() {{

        try {{

            const stream =
            await navigator.mediaDevices.getUserMedia({{

                video: {{
                    facingMode: "user"
                }},

                audio: false

            }});


            video.srcObject =
            stream;


            status.innerText =
            "📷 Camera started. Look at the camera.";

        }}

        catch(error) {{

            console.error(error);

            status.innerText =
            "❌ Camera permission denied.";

        }}

    }}
);


// =========================================================
// VERIFY FACE
// =========================================================

document
.getElementById("verifyButton")
.addEventListener(
    "click",
    async function() {{

        result.innerText = "";


        if (!video.srcObject) {{

            result.innerText =
            "⚠️ Start camera first.";

            return;

        }}


        if (
            registeredDescriptors.length === 0
        ) {{

            result.innerText =
            "❌ No registered faces found.";

            return;

        }}


        status.innerText =
        "🔍 Checking face...";


        try {{

            const detection =
            await faceapi
            .detectSingleFace(
                video,
                new faceapi.TinyFaceDetectorOptions()
            )
            .withFaceLandmarks()
            .withFaceDescriptor();


            if (!detection) {{

                result.innerText =
                "❌ No face detected.";

                status.innerText =
                "Please look directly at the camera.";

                return;

            }}


            let bestMatch =
            null;

            let smallestDistance =
            Infinity;


            // Compare camera face
            // with EVERY registered face

            for (
                const person of registeredDescriptors
            ) {{

                const distance =
                faceapi.euclideanDistance(
                    detection.descriptor,
                    person.descriptor
                );


                console.log(
                    person.name,
                    "Distance:",
                    distance
                );


                if (
                    distance < smallestDistance
                ) {{

                    smallestDistance =
                    distance;

                    bestMatch =
                    person.name;

                }}

            }}


            // Recognition threshold

            const threshold =
            0.50;


            console.log(
                "Best match:",
                bestMatch
            );

            console.log(
                "Distance:",
                smallestDistance
            );


            if (
                smallestDistance < threshold
            ) {{

                result.innerText =
                "✅ ACCESS GRANTED";

                result.style.color =
                "green";


                status.innerText =
                "Welcome " + bestMatch + "!";

            }}

            else {{

                result.innerText =
                "❌ ACCESS DENIED";

                result.style.color =
                "red";


                status.innerText =
                "Face not recognized.";

            }}

        }}

        catch(error) {{

            console.error(error);

            result.innerText =
            "❌ Error while checking face.";

            status.innerText =
            "Please try again.";

        }}

    }}
);


// =========================================================
// START
// =========================================================

loadModels();

</script>

</body>

</html>
"""


components.html(
    html_code,
    height=800,
    scrolling=True
)