
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

data = [['Temp', 'Wind'], [38, 26], [30, 20]]
t = Table(data)
style = [
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue]),
    ('BACKGROUND', (0, 1), (0, 1), colors.yellow),
    ('BACKGROUND', (1, 1), (1, 1), colors.yellow)
]
t.setStyle(TableStyle(style))
doc = SimpleDocTemplate('test_pdf.pdf')
doc.build([t])
print('Done!')
    