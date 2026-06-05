from flask import Flask, render_template, request, send_file, jsonify
import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
        
        # Leemos el Word de forma interna
        doc = Document(input_path)
        pdf = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        
        story = []
        
        # Procesamos el texto y extraemos las imágenes ocultas si las hay
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                story.append(Paragraph(paragraph.text, normal_style))
                story.append(Spacer(1, 10))
        
        # Intentar leer imágenes nativas del Word para meterlas al PDF
        try:
            for rel in doc.part.relations.values():
                if "image" in rel.target_ref:
                    img_data = rel.target_part.blob
                    img_name = os.path.basename(rel.target_ref)
                    temp_img_path = os.path.join(OUTPUT_FOLDER, img_name)
                    with open(temp_img_path, "wb") as f:
                        f.write(img_data)
                    story.append(Image(temp_img_path, width=200, height=150))
                    story.append(Spacer(1, 12))
        except:
            pass # Si no hay imágenes accesibles, continúa con el texto para no romper el flujo
            
        pdf.build(story)
        
        if os.path.exists(input_path):
            os.remove(input_path)
            
        return send_file(pdf_path, mimetype='application/pdf')
        
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
