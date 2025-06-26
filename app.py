import os
from flask import Flask, render_template, request, send_file
import qrcode
from PIL import Image
import base64
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'qr_vcard_web/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def create_vcard(data, photo_b64=None):
    vcard = "BEGIN:VCARD\nVERSION:3.0\n"
    vcard += f"N:{data.get('last_name', '')};{data['first_name']}\n"
    vcard += f"FN:{data['first_name']} {data.get('last_name', '')}\n"
    vcard += f"TEL:{data['phone']}\n"
    vcard += f"EMAIL:{data['email']}\n"
    vcard += f"ORG:{data['org']}\n"

    if data.get('title'):
        vcard += f"TITLE:{data['title']}\n"
    if data.get('address'):
        vcard += f"ADR:{data['address']}\n"
    if data.get('website'):
        vcard += f"URL:{data['website']}\n"
    if photo_b64:
        vcard += f"PHOTO;ENCODING=b;TYPE=JPEG:{photo_b64}\n"

    vcard += "END:VCARD"
    return vcard

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form = request.form
        first_name = form.get('first_name', '').strip()
        phone = form.get('phone', '').strip()
        email = form.get('email', '').strip()
        org = form.get('org', '').strip()

        # Kiểm tra bắt buộc
        if not all([first_name, phone, email, org]):
            return "Các trường bắt buộc không được để trống", 400

        # Xử lý ảnh nếu có
        photo_file = request.files.get('photo')
        photo_b64 = None
        if photo_file and photo_file.filename:
            image = Image.open(photo_file)
            image = image.convert("RGB")
            image.thumbnail((300, 300))
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            photo_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Tạo vCard
        vcard = create_vcard(form, photo_b64)
        filename_base = secure_filename(first_name.lower().replace(" ", "_"))

        # Lưu file vCard
        vcf_filename = f"{filename_base}.vcf"
        vcf_path = os.path.join(app.config['UPLOAD_FOLDER'], vcf_filename)
        with open(vcf_path, "w", encoding="utf-8") as f:
            f.write(vcard)

        # Tạo QR
        qr = qrcode.make(vcard)
        qr_filename = f"{filename_base}_qr.png"
        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        qr.save(qr_path)

        return render_template("index.html",
                               qr_generated=True,
                               qr_path=f"/static/{qr_filename}",
                               qr_filename=qr_filename,
                               vcf_filename=vcf_filename)

    return render_template("index.html", qr_generated=False)

@app.route("/download")
def download_qr():
    filename = request.args.get("filename")
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route("/download-vcf")
def download_vcf():
    filename = request.args.get("filename")
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)