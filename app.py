from flask import Flask, render_template, request, send_file, jsonify
import os
import mammoth
from xhtml2pdf import pisa
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
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(OUTPUT_FOLDER, filename)
    file.save(input_path)
    
    try:
        pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        # Convertimos el Word completo a HTML estructurado (Mammoth extrae las imágenes automáticamente en Base64)
        with open(input_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            
        # Le aplicamos estilos CSS profesionales para que respete los márgenes y escale bien las fotos
        full_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: letter;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    color: #333333;
                    line-height: 1.5;
                }}
                p {{ margin-bottom: 12pt; text-align: justify; }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 15pt auto;
                }}
                h1, h2, h3 {{ color: #111111; margin-top: 18pt; margin-bottom: 8pt; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Generamos el PDF final permitiendo que se creen dinámicamente las páginas que correspondan
        with open(pdf_path, "wbb") as pdf_file:
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
            
        if pisa_status.err:
            raise Exception("Error al estructurar las páginas del PDF")

        if os.path.exists(input_path):
            os.remove(input_path)
            
        return send_file(pdf_path, mimetype='application/pdf')
        
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
