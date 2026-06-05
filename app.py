from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
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
            # LibreOffice clona el Word manteniendo el formato, imágenes, links y diseño intactos
            cmd = f"libreoffice --headless --convert-to pdf --outdir {OUTPUT_FOLDER} {input_word_path}"
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            pdf_filename = base_name + '.pdf'
            output_pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
            
            # Limpiamos el Word de inmediato para dejar solo el PDF listo
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            # Enviamos el PDF real (servirá tanto para descargarlo como para verlo en pantalla)
            return send_file(output_pdf_path, as_attachment=False, download_name=pdf_filename, mimetype='application/pdf')
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': 'Error en la conversión del sistema: ' + str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True)
