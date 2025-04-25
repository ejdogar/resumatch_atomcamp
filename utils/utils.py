from fpdf import FPDF
import os

def export_pdf(text: str, filename: str) -> str:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    content = text.content if hasattr(text, 'content') else text
    
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    pdf.output(filename)
    return filename

