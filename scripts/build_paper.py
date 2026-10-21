"""Render the editable technical-report source and stored aggregate metrics."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image

ROOT = Path(__file__).resolve().parents[1]
TEAL = colors.HexColor('#153f48')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BodyReport', fontName='Times-Roman', fontSize=10.2, leading=13.5, spaceAfter=8))
styles.add(ParagraphStyle('TitleReport', fontName='Helvetica-Bold', fontSize=23, leading=27, textColor=TEAL, spaceAfter=15))
styles.add(ParagraphStyle('H1Report', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=TEAL, spaceBefore=7, spaceAfter=10))
styles.add(ParagraphStyle('H2Report', fontName='Helvetica-Bold', fontSize=10.7, leading=14, textColor=TEAL, spaceBefore=5, spaceAfter=6))
styles.add(ParagraphStyle('CaptionReport', fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor('#45545d'), spaceAfter=10))
styles.add(ParagraphStyle('CellReport', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_LEFT))

def table(rows, widths, padding=7):
    cells = [[Paragraph(escape(str(c)), styles['CellReport']) for c in row] for row in rows]
    result = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0),colors.HexColor('#e6eff1')),
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6), ('TOPPADDING',(0,0),(-1,-1),padding),
        ('BOTTOMPADDING',(0,0),(-1,-1),padding),
        ('LINEBELOW',(0,0),(-1,0),0.7,TEAL),
        ('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d7e1e4'))]))
    return result

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TEAL)
    canvas.line(48, 756, 564, 756)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEAL)
    canvas.drawString(48, 766, 'NEUROVOLUME  |  TECHNICAL REPORT v0.2')
    canvas.setFillColor(colors.HexColor('#52636b'))
    canvas.drawString(48, 27, 'Text revised October 21, 2026  |  Not peer reviewed')
    canvas.drawRightString(564, 27, str(doc.page))
    canvas.restoreState()

def main():
    results = json.loads((ROOT / 'reports/results.json').read_text())
    story = []
    for page_index, page in enumerate((ROOT / 'paper/NeuroVolume.md').read_text().split('\n---page---\n')):
        if page_index: story.append(PageBreak())
        for block in page.strip().split('\n\n'):
            if block.startswith('[Table 1:'):
                rows = [['Predictors', 'Test AUC (95% interval)', 'Accuracy', 'Brier']]
                for r in results['results']:
                    if r['algorithm'] != 'logistic': continue
                    v=r['test']; ci=r['auc_ci']
                    rows.append([r['label'], f"{v['auc']:.3f} ({ci[0]:.3f}-{ci[1]:.3f})", f"{v['accuracy']*100:.1f}%", f"{v['brier']:.3f}"])
                story.extend([table(rows,[179,166,82,89]),Spacer(1,8)])
            elif block.startswith('[Table A1:'):
                rows = [['Set', 'Algorithm', 'AUC', 'Accuracy', 'Sensitivity', 'Specificity', 'Brier']]
                names={'demographics':'D','mri':'D+M','cognition':'D+C','combined':'D+M+C'}
                for r in results['results']:
                    v=r['test']
                    rows.append([names[r['family']],r['algorithm'],f"{v['auc']:.3f}",f"{v['accuracy']*100:.1f}%",f"{v['sensitivity']*100:.1f}%",f"{v['specificity']*100:.1f}%",f"{v['brier']:.3f}"])
                story.extend([table(rows,[51,75,52,76,88,88,86],padding=4),Spacer(1,8)])
            elif block.startswith('![Figure 1:'):
                path=ROOT / 'reports/model-comparison.png'
                width,height=ImageReader(str(path)).getSize()
                story.extend([Image(str(path),width=490,height=490*height/width),Spacer(1,7)])
            else:
                text=block.replace('\n',' ')
                style='BodyReport'
                for prefix, selected in [('### ','H2Report'),('## ','H1Report'),('# ','TitleReport')]:
                    if text.startswith(prefix): text=text[len(prefix):];style=selected;break
                if text.startswith(('Table ','Figure ')): style='CaptionReport'
                story.append(Paragraph(escape(text),styles[style]))
    out=ROOT / 'paper/NeuroVolume.pdf'
    doc=SimpleDocTemplate(str(out),pagesize=(612,792),leftMargin=48,rightMargin=48,topMargin=51,bottomMargin=48,
                          title='NeuroVolume: Evaluating the Incremental Value of MRI-Derived Brain Measurements',
                          author='NeuroVolume project; project lead Arjun Mathane')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(out)

if __name__ == '__main__': main()
