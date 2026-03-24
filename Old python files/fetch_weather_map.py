import os
import math
import requests
import json
from datetime import datetime
from PIL import ImageDraw, ImageFont, Image as PLImage
from fpdf import FPDF
from io import BytesIO

# --- Load locations from config.json ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
LOCATIONS = config.get("locations", {})
API_KEY = config.get("api_key_openweathermap", "")

LAYER_NAMES = ["precipitation"]
UNITS = {'precipitation': 'mm'}
ZOOM = 6
TILE_RADIUS = 1

COLOR_SCALES = {
    'precipitation': {
        'min': 0,
        'max': 20,
        'colors': [
            (214, 236, 255),   # 0 mm - white (no rain)
            (0, 191, 255),
            (0, 255, 0),  # 4 mm - green
            (255, 255, 0),
            (255, 215, 0),    # 6 mm - yellow
            (255, 165, 0),
            (255, 69, 0),     # 8 mm - orange
            (255, 0, 0),
            (211, 0, 148),  # 10 mm - dark magenta
            (255, 0, 255),  # 12 mm - magenta
            (148, 0, 211),  # 16 mm - dark violet
        ]
    }
}


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def get_tile_url(layer, x, y, z):
    return f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={API_KEY}"


def fetch_base_tile(x, y, z):
    url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    headers = {"User-Agent": "WeatherLayerBot/1.0 (your_email@example.com)"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return PLImage.open(BytesIO(resp.content)).convert("RGB")
    else:
        raise Exception(f"Base tile error: HTTP {resp.status_code}")


def fetch_tile_grid(layer, x_center, y_center, z, radius=1):
    tile_size = 256
    grid_size = 2 * radius + 1
    stitched = PLImage.new(
        "RGB", (tile_size * grid_size, tile_size * grid_size))

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            xtile = x_center + dx
            ytile = y_center + dy

            try:
                base = fetch_base_tile(xtile, ytile, z)
            except Exception as e:
                print(f"Failed base tile ({xtile},{ytile}): {e}")
                base = PLImage.new("RGB", (tile_size, tile_size),
                                   color=(180, 180, 180))

            overlay_url = get_tile_url(layer, xtile, ytile, z)
            overlay_resp = requests.get(overlay_url)
            if overlay_resp.status_code == 200:
                overlay = PLImage.open(
                    BytesIO(overlay_resp.content)).convert("RGBA")
                base.paste(overlay, (0, 0), overlay)

            stitched.paste(base, ((dx + radius) * tile_size,
                           (dy + radius) * tile_size))

    return stitched


def mark_location(image, lat, lon, zoom, x_center, y_center, radius):
    tile_size = 256
    n = 2.0 ** zoom
    x_rel = (lon + 180.0) / 360.0 * n
    y_rel = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    px = int((x_rel - x_center + radius) * tile_size)
    py = int((y_rel - y_center + radius) * tile_size)

    draw = ImageDraw.Draw(image)
    draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill='red')
    return image


def annotate_image(img, layer_name, value, unit):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", size=24)
    except:
        font = ImageFont.load_default()

    text = f"{layer_name.title()}: {value:.1f} {unit}"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = 10
    y = img.height - h - 10
    draw.rectangle([x - 5, y - 5, x + w + 5, y + h + 5],
                   fill=(255, 255, 255, 220))
    draw.text((x, y), text, fill="black", font=font)
    return img


def draw_color_legend(layer, width=256, height=30):
    scale = COLOR_SCALES[layer]
    min_val, max_val, colors = scale['min'], scale['max'], scale['colors']
    gradient = PLImage.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(gradient)

    for x in range(width):
        t = x / (width - 1)
        index = int(t * (len(colors) - 1))
        t_local = (t * (len(colors) - 1)) - index
        c1, c2 = colors[index], colors[min(index + 1, len(colors) - 1)]
        blended = tuple(int(c1[i] + (c2[i] - c1[i]) * t_local)
                        for i in range(3))
        draw.line([(x, 0), (x, height)], fill=blended)

    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
    tick_n = 6
    for i in range(tick_n):
        val = min_val + i * (max_val - min_val) / (tick_n - 1)
        label = f"{val:.0f}"
        x_pos = int(i * (width - 1) / (tick_n - 1))
        draw.text((x_pos - 10, height - 12), label, font=font, fill="black")

    return gradient


def fetch_current_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def select_location():
    print("Available Locations:")
    loc_names = list(LOCATIONS.keys())
    for idx, name in enumerate(loc_names, 1):
        print(f"{idx}. {name}")
    while True:
        try:
            sel = int(input("Select a location by number: "))
            if 1 <= sel <= len(loc_names):
                return loc_names[sel - 1], LOCATIONS[loc_names[sel - 1]]
            else:
                print("Invalid selection. Try again.")
        except Exception:
            print("Please enter a valid number.")


def create_pdf_with_layers(images, values, timestamp_str, location_name, lat, lon):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cover Page
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 20, f"Weather Map Report", ln=True, align="C")
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"Location: {location_name}", ln=True, align="C")
    pdf.cell(0, 10, f"Coordinates: {lat:.4f}, {lon:.4f}", ln=True, align="C")
    pdf.cell(0, 10, f"Timestamp: {timestamp_str}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(
        0, 8, "This report shows weather layer maps with measured values and color scale legends for visual estimation.")

    for layer_name, image in images.items():
        img_path = f"{layer_name}.jpg"
        image.save(img_path)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"{layer_name.title()} Layer", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(
            0, 10, f"Measured: {values[layer_name]:.1f} {UNITS[layer_name]}", ln=True)
        pdf.image(img_path, x=15, y=30, w=180)
        os.remove(img_path)

    filename = f"weather_report_{location_name.replace(' ', '_').replace(',', '')}_{timestamp_str.replace(' ', '_').replace(':', '-')}.pdf"
    pdf.output(filename)
    print(f"✅ PDF generated: {filename}")


if __name__ == "__main__":
    try:
        # --- User selects location ---
        location_name, location_info = select_location()
        LAT, LON = location_info['coords']
        print(f"Selected: {location_name} (Lat: {LAT}, Lon: {LON})")

        TILE_X, TILE_Y = deg2num(LAT, LON, ZOOM)
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        data = fetch_current_weather(LAT, LON)

        values = {
            'precipitation': data.get('rain', {}).get('1h', 0)
        }

        weather_images = {}
        for layer in LAYER_NAMES:
            print(f"\n📥 Processing {layer}...")
            image = fetch_tile_grid(layer, TILE_X, TILE_Y, ZOOM, TILE_RADIUS)
            image = mark_location(image, LAT, LON, ZOOM,
                                  TILE_X, TILE_Y, TILE_RADIUS)
            image = annotate_image(image, layer, values[layer], UNITS[layer])
            legend = draw_color_legend(layer, width=image.width, height=30)
            combined = PLImage.new(
                "RGB", (image.width, image.height + legend.height), "white")
            combined.paste(image, (0, 0))
            combined.paste(legend, (0, image.height))
            weather_images[layer] = combined

        create_pdf_with_layers(weather_images, values,
                               timestamp_str, location_name, LAT, LON)

    except Exception as e:
        print(f"❌ Error: {e}")
