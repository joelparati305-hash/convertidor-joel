from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
# Importamos la librería para convertir el PDF final a imagen
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

    # Detectamos qué formato pidió el usuario desde la página web
    # Si la página no envía nada, por defecto se descargará como PDF
    format_type = request.form.get('format', 'pdf')

    if file and (file.filename.endswith('.docx') or file.filename.endswith('.doc')):
        filename = secure_filename(file.filename)
        base_name = filename.rsplit('.', 1)[0]
        pdf_filename = base_name + '.pdf'
        output_pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        
        try:
            # 1. Creamos el PDF base estructurado
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=16, spaceAfter=15
            )
            link_style = ParagraphStyle(
                'DocLink', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#3b82f6'), spaceAfter=8
            )
            
            lineas_texto = [
                "SEGUIR EL ORDEN DE LA INSTALACIÓN QUE SE MENCIONÓ EN CLASE",
                "SketchUp Plugins | PluginStore | JHS PowerBar",
                "https://sketchucation.com/pluginstore?pln=V-Ray_for_SketchUp",
                "https://sketchucation.com/pluginstore?pln=Curviloft",
                "https://sketchucation.com/pluginstore?pln=JointPushPull",
                "https://sketchucation.com/pluginstore?pln=FredoTools"
            ]
            
            story.append(Paragraph(lineas_texto[0], title_style))
            for line in lineas_texto[1:]:
                story.append(Paragraph(f"<u>{line}</u>", link_style))
            
            doc.build(story)
            
            # 2. Lógica de entrega según la elección del usuario
            if format_type == 'jpg' or format_type == 'image':
                # Convertimos la primera página del PDF generado a una imagen JPEG
                images = convert_from_path(output_pdf_path)
                if images:
                    jpg_filename = base_name + '.jpg'
                    output_jpg_path = os.path.join(OUTPUT_FOLDER, jpg_filename)
                    # Guardamos la imagen en la carpeta converted
                    images[0].save(output_jpg_path, 'JPEG')
                    # Enviamos la foto directamente al navegador del usuario
                    return send_file(output_jpg_path, as_attachment=True, download_name=jpg_filename)
            
            # Si el usuario no eligió imagen, le entregamos el PDF clásico
            return send_file(output_pdf_path, as_attachment=True, download_name=pdf_filename)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Formato no permitido'}), 400

if __name__ == '__main__':
    app.run(debug=True)