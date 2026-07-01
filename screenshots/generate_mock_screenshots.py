from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
RAW = ROOT.parent / 'data' / 'raw'

customers = pd.read_csv(RAW / 'customers.csv')
products = pd.read_csv(RAW / 'products.csv')
transactions = pd.read_csv(RAW / 'sales_transactions.csv')

regions = customers['region'].value_counts().sort_index().index.tolist()
segments = customers['segment'].value_counts().sort_index().index.tolist()
categories = products['category'].value_counts().sort_index().index.tolist()
sample_products = products.head(5)[['product_name', 'category', 'brand']].copy()

ACCENT_BLUE = '#0F6CBD'
ACCENT_GREEN = '#2E8B57'
ACCENT_ORANGE = '#D97706'
ACCENT_PURPLE = '#7C3AED'
BG = '#F5F7FA'
CARD = '#FFFFFF'
TEXT = '#243447'
MUTED = '#667085'
OUTLINE = '#D9E2EC'

font = ImageFont.load_default()
font_bold = ImageFont.load_default()


def draw_header(draw, title, subtitle, accent):
    draw.rectangle([0, 0, 1600, 90], fill=accent)
    draw.text((40, 24), title, fill='white', font=font)
    draw.text((40, 56), subtitle, fill='#EAF4FF', font=font)


def rounded_box(draw, x0, y0, x1, y1, fill=CARD, outline=OUTLINE, radius=16):
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline)


def metric_card(draw, x, y, label, value, color):
    rounded_box(draw, x, y, x + 230, y + 110)
    draw.text((x + 18, y + 18), label, fill=MUTED, font=font)
    draw.text((x + 18, y + 48), value, fill=TEXT, font=font_bold)
    draw.rectangle([x + 18, y + 86, x + 86, y + 92], fill=color)


def create_executive_mockup(path):
    img = Image.new('RGB', (1600, 900), BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 'Executive Dashboard Mockup', f'Synthetic retail dataset • {len(customers):,} customers • {len(transactions):,} transactions', ACCENT_BLUE)

    metric_card(draw, 40, 120, 'Customers', f"{len(customers):,}", ACCENT_BLUE)
    metric_card(draw, 290, 120, 'Regions', f"{len(regions)}", ACCENT_GREEN)
    metric_card(draw, 540, 120, 'Segments', f"{len(segments)}", ACCENT_ORANGE)
    metric_card(draw, 790, 120, 'Top Category', categories[0], ACCENT_PURPLE)

    rounded_box(draw, 40, 260, 960, 620)
    draw.text((70, 285), 'Monthly Revenue and Gross Profit', fill=TEXT, font=font_bold)
    draw.text((70, 315), 'Layout aligned to the documented executive dashboard specification', fill=MUTED, font=font)
    for i in range(12):
        x = 100 + i * 65
        y = 540 - ((i % 6) + 1) * 25
        draw.rectangle([x, y, x + 28, 560], fill=ACCENT_BLUE)

    rounded_box(draw, 1000, 260, 1560, 620)
    draw.text((1030, 285), 'Regional Revenue Focus', fill=TEXT, font=font_bold)
    for i, region in enumerate(regions):
        y = 330 + i * 45
        draw.rectangle([1030, y, 1060, y + 20], fill=ACCENT_GREEN)
        draw.text((1080, y - 2), region, fill=TEXT, font=font)

    rounded_box(draw, 40, 660, 760, 840)
    draw.text((70, 685), 'Category Mix', fill=TEXT, font=font_bold)
    for i, category in enumerate(categories[:4]):
        x = 80 + i * 160
        draw.pieslice([x, 700, x + 90, 790], start=0, end=220 + i * 40, fill=[ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE][i])
        draw.text((x + 10, 770), category[:10], fill=MUTED, font=font)

    rounded_box(draw, 800, 660, 1560, 840)
    draw.text((830, 685), 'Top Products from the generated product catalog', fill=TEXT, font=font_bold)
    for i, row in enumerate(sample_products.itertuples(index=False)):
        y = 720 + i * 28
        draw.text((830, y), f"• {row.product_name}", fill=TEXT, font=font)
        draw.text((1320, y), row.category, fill=ACCENT_BLUE, font=font)

    img.save(path)


def create_customer_mockup(path):
    img = Image.new('RGB', (1600, 900), BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 'Customer RFM Mockup', f'Customer segmentation view • {len(segments)} segments represented • {len(customers):,} customers', ACCENT_ORANGE)

    rounded_box(draw, 90, 150, 1510, 770)
    draw.text((120, 185), 'RFM view based on the generated customer records', fill=TEXT, font=font_bold)

    draw.line([(240, 690), (1420, 690)], fill=TEXT, width=3)
    draw.line([(240, 220), (240, 690)], fill=TEXT, width=3)
    for tick in range(1, 6):
        x = 240 + tick * 240 - 120
        draw.line([(x, 690), (x, 700)], fill=MUTED, width=2)
        draw.text((x - 8, 704), str(tick), fill=MUTED, font=font)

    points = [
        ('Consumer', 420, 390, 70, ACCENT_BLUE),
        ('Corporate', 760, 470, 60, ACCENT_GREEN),
        ('Home Office', 1100, 360, 50, ACCENT_PURPLE),
    ]
    for label, x, y, size, color in points:
        draw.ellipse((x - size, y - size, x + size, y + size), fill=color)
        draw.text((x - 28, y + size + 10), label, fill=TEXT, font=font)

    draw.text((120, 780), f"Segments present in customers.csv: {', '.join(segments)}", fill=MUTED, font=font)
    img.save(path)


def create_athena_mockup(path):
    img = Image.new('RGB', (1600, 900), BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 'Athena Query Mockup', 'Query and result layout matching the documented analytics workflow', ACCENT_PURPLE)
    rounded_box(draw, 90, 150, 1510, 770)
    draw.rounded_rectangle([110, 220, 1490, 280], fill='#112D43', radius=8)
    draw.text((130, 234), 'SELECT region, SUM(net_revenue) AS revenue FROM sales_transactions GROUP BY region ORDER BY revenue DESC', fill='white', font=font)
    headers = ['Region', 'Revenue', 'Orders', 'Margin %']
    for idx, header in enumerate(headers):
        x = 120 + idx * 320
        rounded_box(draw, x, 320, x + 280, 390, fill='#F3F6FA', outline=OUTLINE)
        draw.text((x + 16, 340), header, fill=TEXT, font=font_bold)
    rows = [(regions[0], f"{len(transactions):,}", f"{len(customers):,}", '38%')]
    for idx, row in enumerate(rows):
        y = 410 + idx * 70
        for c_idx, value in enumerate(row):
            x = 120 + c_idx * 320
            rounded_box(draw, x, y, x + 280, y + 46, fill='#FFFFFF', outline=OUTLINE)
            draw.text((x + 16, y + 14), value, fill=TEXT, font=font)
    img.save(path)


if __name__ == '__main__':
    create_executive_mockup(ROOT / 'executive_dashboard_mockup.png')
    create_customer_mockup(ROOT / 'customer_rfm_mockup.png')
    create_athena_mockup(ROOT / 'athena_query_mockup.png')
    print('Generated files:')
    for path in sorted(ROOT.glob('*.png')):
        print(path.name)
