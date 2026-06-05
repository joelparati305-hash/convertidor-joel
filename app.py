from flask import Flask, render_template, request, send_file, jsonify
import os
from docx import Document
from fpdf import FPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)
OUTPUT_FOLDER = 'converted'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    input_path = os.path.join(OUTPUT_FOLDER, filename)
    file.save(input_path)
    try:
        pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        doc = Document(input_path)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        for para in doc.paragraphs:
            # Codificación para evitar errores de caracteres especiales
            text = para.text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, text)
            
        pdf.output(pdf_path)
        if os.path.exists(input_path): os.remove(input_path)
        return send_file(pdf_path, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
