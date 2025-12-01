import os
from flask import Flask, render_template, request, send_file
import qrcode
from PIL import Image
from io import BytesIO
import base64
import urllib.parse
from werkzeug.utils import secure_filename


app = Flask(__name__)
UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def create_vcard(data, photo_b64=None):
    vcard = "BEGIN:VCARD\nVERSION:3.0\n"
    vcard += f"N:{data.get('last_name', '')};{data['first_name']}\n"
    vcard += f"FN:{data['first_name']} {data.get('last_name', '')}\n"
    if data.get("phone"):
        vcard += f"TEL:{data['phone']}\n"
    if data.get("email"):
        vcard += f"EMAIL:{data['email']}\n"
    if data.get("org"):
        vcard += f"ORG:{data['org']}\n"
    if data.get("title"):
        vcard += f"TITLE:{data['title']}\n"
    if data.get("address"):
        vcard += f"ADR:{data['address']}\n"
    if data.get("website"):
        vcard += f"URL:{data['website']}\n"
    if photo_b64:
        vcard += f"PHOTO;ENCODING=b;TYPE=JPEG:{photo_b64}\n"
    vcard += "END:VCARD"
    return vcard

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/vcard", methods=["GET", "POST"])
def vcard():
    if request.method == "POST":
        form = request.form
        first_name = form.get("first_name", "").strip()
        if not first_name:
            return "Trường tên là bắt buộc.", 400

        photo_b64 = None
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            image = Image.open(photo_file)
            image = image.convert("RGB")
            image.thumbnail((300, 300))
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            photo_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        vcard_full = create_vcard(form, photo_b64)
        vcard_short = create_vcard(form)

        filename_base = secure_filename(first_name.lower().replace(" ", "_"))
        vcf_filename = f"{filename_base}.vcf"
        qr_filename = f"{filename_base}_qr.png"

        with open(os.path.join(UPLOAD_FOLDER, vcf_filename), "w", encoding="utf-8") as f:
            f.write(vcard_full)

        qr_img = qrcode.make(vcard_short)
        qr_img.save(os.path.join(UPLOAD_FOLDER, qr_filename))

        return render_template("vcard.html", qr_generated=True,
                               qr_path=f"/static/{qr_filename}",
                               qr_filename=qr_filename,
                               vcf_filename=vcf_filename)

    return render_template("vcard.html", qr_generated=False)

@app.route("/link", methods=["GET", "POST"])
def qr_link():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            return "Trường đường link là bắt buộc.", 400

        info = request.form.get("info", "").strip()
        filename_base = secure_filename((info or "qr_link").lower().replace(" ", "_"))
        qr_filename = f"{filename_base}_qr.png"
        qr_img = qrcode.make(url)
        qr_img.save(os.path.join(UPLOAD_FOLDER, qr_filename))

        return render_template("link.html", qr_generated=True,
                               qr_path=f"/static/{qr_filename}",
                               qr_filename=qr_filename)

    return render_template("link.html", qr_generated=False)

@app.route("/email", methods=["GET", "POST"])
def qrcode_email():
    if request.method == "POST":
        email = request.form.get("email")
        info = request.form.get("info") or ""

        if not email:
            return render_template("qrcode_email.html", error="Email là bắt buộc!")

        # Mã hoá tham số
        subject = urllib.parse.quote("Thông tin từ QR")
        body = urllib.parse.quote(info)

        # Tạo link mailto:
        if info:
            mailto_link = f"mailto:{email}?subject={subject}&body={body}"
        else:
            mailto_link = f"mailto:{email}"

        # Tạo QR Code
        qr = qrcode.make(mailto_link)
        img_io = BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)

        return send_file(img_io, mimetype="image/png")

    return render_template("qrcode_email.html")

@app.route("/download")
def download_qr():
    filename = request.args.get("filename")
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

@app.route("/download-vcf")
def download_vcf():
    filename = request.args.get("filename")
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
