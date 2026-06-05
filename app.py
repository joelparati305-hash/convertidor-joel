from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
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
        
        # Guardamos el archivo Word real que subió el usuario
        input_word_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_word_path)
        
        pdf_filename = base_name + '.pdf'
        output_pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        try:
            # 1. Leemos TODO el contenido del Word línea por línea
            doc_word = Document(input_word_path)
            lineas_texto = []
            for paragraph in doc_word.paragraphs:
                if paragraph.text.strip():  # Guardamos solo líneas con contenido
                    lineas_texto.append(paragraph.text.strip())
            
            # Si el Word viene completamente vacío
            if not lineas_texto:
                lineas_texto = ["El archivo de Word original no contenía texto."]

            # 2. Creamos el PDF estructurado
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilos limpios para el documento
            title_style = ParagraphStyle(
                'DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, spaceAfter=15
            )
            text_style = ParagraphStyle(
                'DocText', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, spaceAfter=10
            )
            link_style = ParagraphStyle(
                'DocLink', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#3b82f6'), spaceAfter=10
            )
            
            # La primera línea la ponemos como título en negrita
            story.append(Paragraph(lineas_texto[0], title_style))
            
            # El resto de líneas se procesan de forma limpia y automática
            for line in lineas_texto[1:]:
                # Si la línea es un enlace web, la pintamos de azul con subrayado
                if line.startswith("http://") or line.startswith("https://"):
                    story.append(Paragraph(f"<u>{line}</u>", link_style))
                else:
                    # Texto normal del documento
                    story.append(Paragraph(line, text_style))
            
            doc.build(story)
            
            # 3. Limpieza inmediata del archivo Word del servidor
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            
            # 4. Entrega final del archivo procesado
            if format_type == 'jpg' or format_type == 'image':
                images = convert_from_path(output_pdf_path)
                if images:
                    jpg_filename = base_name + '.jpg'
                    output_jpg_path = os.path.join(OUTPUT_FOLDER, jpg_filename)
                    images[0].save(output_jpg_path, 'JPEG')
                    return send_file(output_jpg_path, as_attachment=True, download_name=jpg_filename)
            
            return send_file(output_pdf_path, as_attachment=True, download_name=pdf_filename)
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True)
