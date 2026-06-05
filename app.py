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
            # Forzamos a LibreOffice a usar rutas locales amigables para evitar bloqueos en Render
            home_dir = os.getcwd()
            env = os.environ.copy()
            env['HOME'] = home_dir
            
            output_pdf_path = os.path.join(OUTPUT_FOLDER, base_name + '.pdf')
            
            # Comando ultra seguro con rutas absolutas
            cmd = [
                "libreoffice",
                "--headless",
                "-env:UserInstallation=file://" + os.path.join(home_dir, OUTPUT_FOLDER, ".config"),
                "--convert-to", "pdf",
                "--outdir", os.path.abspath(OUTPUT_FOLDER),
                os.path.abspath(input_word_path)
            ]
            
            subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            return send_file(os.path.abspath(output_pdf_path), mimetype='application/pdf')
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True)
