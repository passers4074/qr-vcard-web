from flask import Flask, render_template, request, send_file
import qrcode
import os
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
QR_PATH = os.path.join(UPLOAD_FOLDER, 'qr.png')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def image_to_base64(image_file):
    img = Image.open(image_file).convert('RGB')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        org = request.form['org']
        title = request.form['title']
        address = request.form['address']
        photo_file = request.files.get('photo')

        photo_b64 = ''
        if photo_file and photo_file.filename:
            try:
                photo_b64 = image_to_base64(photo_file)
            except:
                pass

        vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name};;;
FN:{first_name} {last_name}
ORG:{org}
TITLE:{title}
TEL;TYPE=CELL:{phone}
EMAIL:{email}
ADR;TYPE=WORK:;;{address}"""

        if photo_b64:
            vcard += f"\nPHOTO;ENCODING=b;TYPE=JPEG:{photo_b64}"

        vcard += "\nEND:VCARD"

        qr = qrcode.make(vcard)
        qr.save(QR_PATH)

        return render_template('index.html', qr_path=QR_PATH, qr_generated=True)

    return render_template('index.html', qr_generated=False)

@app.route('/download')
def download_qr():
    return send_file(QR_PATH, as_attachment=True, download_name="vcard_qr.png")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
