from flask import Flask, render_template, request, send_file, jsonify
import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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
            
            # Reconstrucción ligera del documento usando ReportLab (A prueba de fallos de RAM)
            doc = Document(input_word_path)
            pdf = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            style_normal.alignment = 4 # Texto Justificado
            
            story = []
            
            # 1. Procesar Párrafos y Textos
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text = paragraph.text.encode('latin-1', 'replace').decode('latin-1')
                    story.append(Paragraph(text, style_normal))
                    story.append(Spacer(1, 8))
            
            # 2. Extractor seguro de imágenes integradas en el Word
            try:
                for rel in doc.part.relations.values():
                    if "image" in rel.target_ref:
                        img_data = rel.target_part.blob
                        img_name = os.path.basename(rel.target_ref)
                        temp_img_path = os.path.join(OUTPUT_FOLDER, img_name)
                        with open(temp_img_path, "wb") as f:
                            f.write(img_data)
                        
                        story.append(Image(temp_img_path, width=250, height=180))
                        story.append(Spacer(1, 10))
            except:
                pass # Si una imagen tiene error, continúa para que la web no se caiga
                
            # 3. Compilar el PDF final en varias páginas dinámicas
            pdf.build(story)
            
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
                
            return send_file(output_pdf_path, mimetype='application/pdf')
            
        except Exception as e:
            if os.path.exists(input_word_path):
                os.remove(input_word_path)
            return jsonify({'error': f'Error de procesamiento ligero: {str(e)}'}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
