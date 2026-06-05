from flask import Flask, render_template, request, send_file, jsonify
import os
import mammoth
from xhtml2pdf import pisa
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
            
            # Mammoth extrae de forma nativa tablas, textos, estilos e imágenes integradas del Word
            with open(input_word_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value  # Aquí ya viene la estructura con tus fotos en Base64
            
            # Le aplicamos una plantilla de estilos profesionales para respetar el diseño de Word
            full_html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @page {{
                        size: letter;
                        margin: 1.5cm;
                        @bottom-right {{
                            content: counter(page);
                            font-size: 9pt;
                        }}
                    }}
                    body {{
                        font-family: 'Helvetica', 'Arial', sans-serif;
                        color: #222222;
                        line-height: 1.6;
                        font-size: 11pt;
                    }}
                    h1, h2, h3 {{ color: #111111; margin-top: 14pt; margin-bottom: 6pt; font-weight: bold; }}
                    p {{ margin-bottom: 10pt; text-align: justify; }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 12pt;
                        margin-bottom: 12pt;
                    }}
                    table, th, td {{
                        border: 1px solid #cccccc;
                    }}
                    th, td {{
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{ background-color: #f5f5f5; }}
                    ul, ol {{ margin-left: 20pt; margin-bottom: 10pt; }}
                    li {{ margin-bottom: 4pt; }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        display: block;
                        margin: 12pt auto;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Convertimos el HTML estructurado a un PDF real directamente en la memoria de Python
            with open(output_pdf_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
            
            if pisa_status.err:
                raise Exception("El procesador interno no pudo estructurar el diseño.")

            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            return send_file(output_pdf_path, mimetype='application/pdf')
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': f'Error en el procesador interno: {str(e)}'}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
