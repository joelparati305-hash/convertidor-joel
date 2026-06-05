from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Usamos la carpeta tmp que es donde Render nos deja escribir sin problemas
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
        # Guardamos el nombre seguro del archivo
        filename = secure_filename(file.filename)
        base_name = filename.rsplit('.', 1)[0]
        
        input_word_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_word_path)
        
        try:
            # Comando oficial de LibreOffice para convertir a PDF manteniendo formato e imágenes
            # Usamos '/tmp' para guardar el PDF para evitar problemas de permisos
            cmd = f"libreoffice --headless --convert-to pdf --outdir {OUTPUT_FOLDER} {input_word_path}"
            
            # Ejecutamos el comando en el sistema
            subprocess.run(cmd, shell=True, check=True)
            
            pdf_filename = base_name + '.pdf'
            output_pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
            
            # Limpiamos el Word original para no ocupar espacio innecesario
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            return send_file(output_pdf_path, as_attachment=True, download_name=pdf_filename)
            
        except subprocess.CalledProcessError as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': 'Error interno al convertir con el sistema: ' + str(e)}), 500
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': 'Error al procesar el archivo: ' + str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    # Usamos el puerto por defecto de Render para que no haya que configurarlo
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
