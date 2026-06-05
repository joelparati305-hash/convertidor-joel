from flask import Flask, render_template, request, send_file, jsonify
import os
from docx2pdf import convert
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Usamos la carpeta /tmp de Render que permite lectura y escritura libre
OUTPUT_FOLDER = '/tmp/converted'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if file and (file.filename.endswith('.docx') or file.filename.endswith('.doc')):
        filename = secure_filename(file.filename)
        base_name = filename.rsplit('.', 1)[0]
        
        input_word_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_word_path)
        
        try:
            output_pdf_path = os.path.join(OUTPUT_FOLDER, base_name + '.pdf')
            
            # Conversión nativa directa. No usa comandos externos, es ultra ligera.
            convert(input_word_path, output_pdf_path)
            
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            return send_file(output_pdf_path, mimetype='application/pdf')
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': f'Error en procesamiento directo: {str(e)}'}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
