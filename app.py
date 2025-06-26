from flask import Flask, render_template, request, send_file
import qrcode
from qrcode.constants import ERROR_CORRECT_M
import os
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def image_to_base64(image_file, max_width=240, max_height=240):
    img = Image.open(image_file).convert('RGB')
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    buffered = BytesIO()
    img.save(buffered, format="JPEG", optimize=True, quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def generate_vcard(first_name, last_name, phone, email, org, title, address, photo_b64=None, for_qr=False):
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name};;;
FN:{first_name} {last_name}
ORG:{org}
TITLE:{title}
TEL;TYPE=CELL:{phone}
EMAIL:{email}
ADR;TYPE=WORK:;;{address}"""
    if photo_b64 and not for_qr:
        vcard += f"\nPHOTO;ENCODING=b;TYPE=JPEG:{photo_b64}"
    vcard += "\nEND:VCARD"
    return vcard

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
            except Exception as e:
                return f"Lỗi xử lý ảnh: {e}"

        full_name = f"{first_name}_{last_name}".replace(" ", "_")
        qr_filename = f"{full_name}_qr.png"
        vcf_filename = f"{full_name}.vcf"

        qr_path = os.path.join(UPLOAD_FOLDER, qr_filename)
        vcf_path = os.path.join(UPLOAD_FOLDER, vcf_filename)

        # QR không chứa ảnh
        vcard_for_qr = generate_vcard(first_name, last_name, phone, email, org, title, address, None, for_qr=True)
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(vcard_for_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)

        # VCF có ảnh đầy đủ
        vcard_with_photo = generate_vcard(first_name, last_name, phone, email, org, title, address, photo_b64)
        with open(vcf_path, 'w', encoding='utf-8') as f:
            f.write(vcard_with_photo.replace("\n", "\r\n"))

        return render_template('index.html', qr_path=qr_path, vcf_path=vcf_path, qr_generated=True,
                               qr_filename=qr_filename, vcf_filename=vcf_filename)

    return render_template('index.html', qr_generated=False)

@app.route('/download')
def download_qr():
    filename = request.args.get("filename", "qr.png")
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True, download_name=filename)

@app.route('/download-vcf')
def download_vcf():
    filename = request.args.get("filename", "contact.vcf")
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
