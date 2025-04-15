from flask import Flask, request, jsonify
import cv2
import os
from paddleocr import PaddleOCR
import re

app = Flask(__name__)
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_mp=False, enable_mkldnn=False)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔍 Fungsi parsing hasil OCR menjadi JSON terstruktur
def parse_ktp_fields(lines):
    data = {
        'nik': '',
        'nama': '',
        'tempat_tanggal_lahir': '',
        'jenis_kelamin': '',
        'gol_darah': '',
        'alamat': '',
        'rt_rw': '',
        'kelurahan': '',
        'kecamatan': '',
        'agama': '',
        'status_perkawinan': '',
        'pekerjaan': '',
        'kewarganegaraan': '',
        'berlaku_hingga': '',
        'tanggal_cetak': ''
    }

    lines = [line.strip() for line in lines if line.strip()]

    def clean(text):
        return re.sub(r'[^\w\s\-/,.:]', '', text).strip().upper()

    def extract_by_keyword(keywords, allow_inline=True):
        for keyword in keywords:
            for i, line in enumerate(lines):
                norm_line = line.lower().replace(" ", "")
                norm_key = keyword.lower().replace(" ", "")
                if norm_key in norm_line:
                    # Format: Label: Value (inline)
                    if allow_inline:
                        match = re.search(rf"{keyword}[:\s]*([^\n]+)", line, re.IGNORECASE)
                        if match:
                            val = match.group(1).strip()
                            if val and not any(k.lower() in val.lower() for k in data.keys()):
                                return val
                    # Format: Label di baris ini, value di baris berikutnya
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not any(k.lower() in next_line.lower() for k in data.keys()):
                            return next_line
        return ""

    # Field utama
    data['nik'] = extract_by_keyword(['NIK'])
    data['nama'] = extract_by_keyword(['Nama'])
    data['tempat_tanggal_lahir'] = extract_by_keyword([
        'Tempat/Tgl Lahir', 'Tempat/Tg Lahir', 'Tempat/Tanggal Lahir'
    ])
    data['jenis_kelamin'] = extract_by_keyword(['Jenis kelamin'])
    data['gol_darah'] = extract_by_keyword(['Gol.Darah', 'Golongan Darah'], allow_inline=False)
    data['alamat'] = extract_by_keyword(['Alamat'])
    data['rt_rw'] = extract_by_keyword(['RT/RW', 'RT RW'])
    data['kelurahan'] = extract_by_keyword(['Kel/Desa', 'Kelurahan'])
    data['kecamatan'] = extract_by_keyword(['Kecamatan'])
    data['agama'] = extract_by_keyword(['Agama'])
    data['status_perkawinan'] = extract_by_keyword(['Status Perkawinan'])
    data['pekerjaan'] = extract_by_keyword(['Pekerjaan'])
    data['kewarganegaraan'] = extract_by_keyword(['Kewarganegaraan'])

    # Deteksi tanggal cetak otomatis (format DD-MM-YYYY)
    tanggal_regex = re.compile(r'\d{2}-\d{2}-\d{4}')
    for line in lines:
        match = tanggal_regex.search(line)
        if match:
            data['tanggal_cetak'] = match.group(0)
            break

    # Berlaku hingga
    data['berlaku_hingga'] = extract_by_keyword(['Berlaku Hingga'])

    # 🧠 Fallback tambahan untuk inline atau typo
    for line in lines:
        line_clean = line.upper().replace(":", "").strip()
        if "TEMPAT/TGL LAHIR" in line_clean and not data["tempat_tanggal_lahir"]:
            data["tempat_tanggal_lahir"] = line_clean.replace("TEMPAT/TGL LAHIR", "").strip()
        elif "TEMPAT/TG LAHIR" in line_clean and not data["tempat_tanggal_lahir"]:
            data["tempat_tanggal_lahir"] = line_clean.replace("TEMPAT/TG LAHIR", "").strip()
        elif "KEWARGANEGARAAN" in line_clean and not data["kewarganegaraan"]:
            data["kewarganegaraan"] = line_clean.replace("KEWARGANEGARAAN", "").strip()

    # Final cleaning untuk semua field
    for key in data:
        value = clean(data[key])
        if value in [k.upper() for k in data.keys()]:
            data[key] = ''
        else:
            data[key] = value

    return data


# 📥 Endpoint upload dan OCR
@app.route('/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image uploaded'}), 400

    file = request.files['image']
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(filepath)
        img = cv2.imread(filepath)

        if img is None:
            print("❌ Gagal membaca gambar dari file:", filepath)
            return jsonify({'success': False, 'message': 'Image cannot be decoded'}), 400

        result = ocr.ocr(img, cls=True)
        extracted = [line[1][0] for line in result[0]]

        # 🔄 Parsing ke data JSON terstruktur
        parsed = parse_ktp_fields(extracted)

        return jsonify({
            'success': True,
            'rawText': extracted,
            'parsedData': parsed
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 🚀 Jalankan server Flask di port 5001
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
