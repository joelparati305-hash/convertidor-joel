from flask import Flask, render_template, request, send_file, jsonify
import os
from docx2pdf import convert
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
        return jsonify({'error': 'No hay archivo'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    input_path = os.path.join(OUTPUT_FOLDER, filename)
    file.save(input_path)
    
    try:
        # Conversión simplificada y directa
        convert(input_path, OUTPUT_FOLDER)
        
        pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        return send_file(pdf_path, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
