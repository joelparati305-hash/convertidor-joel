from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
# IMPORTANTE: Esta librería leerá el Word real que subas
from docx import Document 
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pdf2image import convert_from_path

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

    format_type = request.form.get('format', 'pdf')

    if file and (file.filename.endswith('.docx') or file.filename.endswith('.doc')):
        filename = secure_filename(file.filename)
        base_name = filename.rsplit('.', 1)[0]
        
        # Guardamos temporalmente el archivo Word que subió el usuario
        input_word_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_word_path)
        
        pdf_filename = base_name + '.pdf'
        output_pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        try:
            # 1. Leemos el contenido REAL del archivo Word subido
            doc_word = Document(input_word_path)
            lineas_texto = []
            for paragraph in doc_word.paragraphs:
                if paragraph.text.strip():  # Solo agregamos líneas que no estén vacías
                    lineas_texto.append(paragraph.text.strip())
            
            # Si el Word estaba completamente vacío, ponemos un texto por defecto
            if not lineas_texto:
                lineas_texto = ["El archivo de Word original no contenía texto."]

            # 2. Creamos el PDF base estructurado con el texto extraído
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilo estándar para los párrafos del documento
            text_style = ParagraphStyle(
                'DocText', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10
            )
            
            # Recorremos el texto real del Word y lo metemos al PDF
            for line in lineas_texto:
                # Si parece un enlace, lo pintamos de azul, si no, texto normal
                if line.startswith("http://") or line.startswith("https://"):
                    link_style = ParagraphStyle(
                        'DocLink', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#3b82f6'), spaceAfter=8
                    )
                    story.append(Paragraph(f"<u>{line}</u>", link_style))
                else:
                    story.append(Paragraph(line, text_style))
            
            doc.build(story)
            
            # 3. Borramos el archivo Word temporal para no llenar el servidor de basura
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            
            # 4. Lógica de entrega según la elección del usuario (PDF o JPG)
            if format_type == 'jpg' or format_type == 'image':
                images = convert_from_path(output_pdf_path)
                if images:
                    jpg_filename = base_name + '.jpg'
                    output_jpg_path = os.path.join(OUTPUT_FOLDER, jpg_filename)
                    images[0].save(output_jpg_path, 'JPEG')
                    return send_file(output_jpg_path, as_attachment=True, download_name=jpg_filename)
            
            return send_file(output_pdf_path, as_attachment=True, download_name=pdf_filename)
            
        except Exception as e:
            # Si algo falla, intentamos limpiar el archivo temporal de todos modos
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True)