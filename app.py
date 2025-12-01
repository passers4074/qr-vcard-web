
from flask import Flask, render_template, request, send_file
import qrcode
from io import BytesIO
import urllib.parse
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# QRcode-Vcard (Tên bắt buộc)
@app.route("/qrcode-vcard", methods=["GET", "POST"])
def qrcode_vcard():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("qrcode_vcard.html", error="Tên là bắt buộc")

        phone = request.form.get("phone", "")
        email = request.form.get("email", "")
        company = request.form.get("company", "")
        lastname = request.form.get("lastname", "")
        title = request.form.get("title", "")
        address = request.form.get("address", "")
        website = request.form.get("website", "")
        photo = request.files.get("photo")

        vcard = "BEGIN:VCARD\nVERSION:3.0\n"
        vcard += f"N:{lastname};{name};;;\n"
        vcard += f"FN:{name}\n"
        if phone: vcard += f"TEL;TYPE=CELL:{phone}\n"
        if email: vcard += f"EMAIL:{email}\n"
        if company: vcard += f"ORG:{company}\n"
        if title: vcard += f"TITLE:{title}\n"
        if address: vcard += f"ADR:{address}\n"
        if website: vcard += f"URL:{website}\n"

        photo_path = None
        if photo:
            photo_path = os.path.join("static", photo.filename)
            full_path = os.path.join(app.root_path, photo_path)
            photo.save(full_path)
            vcard += f"PHOTO;VALUE=URI:{photo_path}\n"

        vcard += "END:VCARD"

        vcf_path = os.path.join(static, f"{name}.vcf")
        full_vcf = os.path.join(app.root_path, vcf_path)
        with open(full_vcf, "w", encoding="utf-8") as f:
            f.write(vcard)

        qr_img = qrcode.make(f"https://your-domain.com/{vcf_path}")
        buf = BytesIO()
        qr_img.save(buf, "PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png", download_name="qrcode_vcard.png")

    return render_template("qrcode_vcard.html", error=None)

# QRcode-Link
@app.route("/qrcode-link", methods=["GET", "POST"])
def qrcode_link():
    if request.method == "POST":
        link = request.form.get("link", "").strip()
        info = request.form.get("info", "").strip()
        if not link:
            return render_template("qrcode_link.html", error="Đường link là bắt buộc")

        qr_text = link if not info else f"{info}: {link}"
        qr_img = qrcode.make(qr_text)
        buf = BytesIO()
        qr_img.save(buf, "PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png", download_name="qrcode_link.png")

    return render_template("qrcode_link.html", error=None)

# QRcode-Email
@app.route("/qrcode-email", methods=["GET", "POST"])
def qrcode_email():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        info = request.form.get("info", "").strip()

        if not email:
            return render_template("qrcode_email.html", error="Email là bắt buộc")

        if info:
            subject = urllib.parse.quote("Thông tin từ QR")
            body = urllib.parse.quote(info)
            mailto = f"mailto:{email}?subject={subject}&body={body}"
        else:
            mailto = f"mailto:{email}"

        qr_img = qrcode.make(mailto)
        buf = BytesIO()
        qr_img.save(buf, "PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png", download_name="qrcode_email.png")

    return render_template("qrcode_email.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)
