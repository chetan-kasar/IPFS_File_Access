import requests
import mimetypes
from flask import Flask, render_template, redirect, request, session, send_file
from cryptography.fernet import Fernet
from io import BytesIO
app = Flask(__name__)

key = Fernet.generate_key()

with open('filekey.key', 'wb') as filekey:
    filekey.write(key)

with open('filekey.key', 'rb') as filekey:
    key = filekey.read()

fernet = Fernet(key)

encryption_keys = []

@app.route("/getFile/<filehash>")
def getfile(filehash):
    mimeType = ""
    for i in encryption_keys:
        if i[1] == filehash:
            mimeType = i[2]

    ipfs_file = requests.get(f"http://localhost:8291/api/v0/cat/{filehash}")

    decrypted = fernet.decrypt(ipfs_file.content)
    decrypted_image = BytesIO(decrypted)
    decrypted_image.seek(0)

    return send_file(decrypted_image, mimetype=mimeType)


@app.route("/showfiles")
def showfiles():
    return render_template("ShowFiles.html",lst=encryption_keys)

@app.route("/download")
def download():
    mimeType = ""
    filehash = request.args.get("filehash")
    for i in encryption_keys:
        if i[1] == filehash:
            mimeType = i[2]

    ipfs_file = requests.get(f"http://localhost:8291/api/v0/cat/{filehash}")

    decrypted = fernet.decrypt(ipfs_file.content)
    decrypted_image = BytesIO(decrypted)
    decrypted_image.seek(0)

    return send_file(decrypted_image,as_attachment=True, download_name="downloaded_file", mimetype= mimeType)

@app.route("/ipfs_access" , methods = ["POST"])
def access():
    filehash = request.form.get("filehash")
    mimeType = ""

    for i in encryption_keys:
        if i[1] == filehash:
            mimeType = i[2]

    ipfs_file = requests.get(f"http://localhost:8291/api/v0/cat/{filehash}")

    decrypted = fernet.decrypt(ipfs_file.content)
    decrypted_image = BytesIO(decrypted)
    decrypted_image.seek(0)

    if request.form.get("btn") == "download":
        return send_file(decrypted_image, as_attachment=True, download_name="downloaded_file", mimetype= mimeType)

    return send_file(decrypted_image, mimetype=mimeType)

@app.route("/")
def index():
    return render_template("access.html")

@app.route("/upload")
def index2():
    return render_template("upload.html")

@app.route('/uploadmeth', methods=['POST'])
def upload_image():

    uploaded_image = request.files['image']
    print(uploaded_image.filename)

    myfile = uploaded_image.read()
    encrypted = fernet.encrypt(myfile)

    image_mime_type = uploaded_image.mimetype

    if uploaded_image:
        try:
            # Prepare the IPFS request
            response = requests.post('http://localhost:5001/api/v0/add', files={'filename': encrypted})

            if response.status_code == 200:
                ipfs_hash = response.json()['Hash']
                encryption_keys.append([uploaded_image.filename, ipfs_hash, image_mime_type])
                print(encryption_keys)
                return render_template("access.html")
            else:
                return 'Failed to upload image to IPFS'
        except Exception as e:
            return str(e)


if __name__ == "__main__":
    app.run(debug=True)
