import pytesseract
from PIL import Image, ImageOps
from decimal import Decimal, ROUND_HALF_UP
import re
from tkinter import Tk, filedialog
from tabulate import tabulate

# Ruta de Tesseract en tu PC
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\denis\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# ---------- Utilidades ----------
NUM_REGEX = r'[-+]?(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2})?'

def quant2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def parse_number(s: str) -> Decimal:
    s = s.strip().replace(" ", "")
    for sym in ("€", "$", "USD", "EUR", "Bs", "S/"):
        s = s.replace(sym, "")
    if "," in s and "." in s:
        last_sep = max(s.rfind(","), s.rfind("."))
        dec_sep = s[last_sep]
        thou_sep = "." if dec_sep == "," else ","
        s = s.replace(thou_sep, "")
        s = s.replace(dec_sep, ".")
    elif "," in s:
        part = s.split(",")[-1]
        if len(part) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        return quant2(Decimal(s))
    except:
        return Decimal("0.00")

def clean_text(ocr: str) -> str:
    t = ocr
    t = re.sub(r'(?i)\b1VA', 'IVA', t)
    t = re.sub(r'(?i)\blVA', 'IVA', t)
    t = re.sub(r'(?i)IVA(\d)', r'IVA \1', t)
    t = re.sub(r'\bWA\b', 'IVA', t, flags=re.IGNORECASE)
    t = re.sub(r'\bTOTAI\b', 'TOTAL', t, flags=re.IGNORECASE)
    return t

def preprocess_image(path: str) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    return img

# ---------- OCR ----------
def extract_text(image_path: str) -> str:
    img = preprocess_image(image_path)
    config = "--oem 3 --psm 6"
    try:
        return pytesseract.image_to_string(img, config=config, lang="spa+eng")
    except:
        return pytesseract.image_to_string(img, config=config)

# ---------- Parser ----------
def parse_invoice(ocr_text: str) -> dict:
    data = {}
    text = clean_text(ocr_text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    net_labels = {"subtotal", "base imponible", "neto"}
    vat_labels = {"iva", "vat", "tax", "impuestos", "igv"}
    total_labels = {"total", "importe total", "grand total", "amount due"}

    for i, ln in enumerate(lines):
        low = ln.lower()

        if "net" not in data and any(lbl in low for lbl in net_labels):
            nums = re.findall(NUM_REGEX, ln)
            if nums:
                data["net"] = parse_number(nums[-1])
            elif i+1 < len(lines):
                nums = re.findall(NUM_REGEX, lines[i+1])
                if nums:
                    data["net"] = parse_number(nums[-1])

        if "vat" not in data and any(lbl in low for lbl in vat_labels):
            nums = re.findall(NUM_REGEX, ln)
            if len(nums) > 1:
                data["vat"] = parse_number(nums[-1])
            elif nums:
                data["vat"] = parse_number(nums[-1])
            elif i+1 < len(lines):
                nums = re.findall(NUM_REGEX, lines[i+1])
                if nums:
                    data["vat"] = parse_number(nums[-1])

        if any(lbl in low for lbl in total_labels):
            nums = re.findall(NUM_REGEX, ln)
            if nums:
                data["gross"] = parse_number(nums[-1])
            elif i+1 < len(lines):
                nums = re.findall(NUM_REGEX, lines[i+1])
                if nums:
                    data["gross"] = parse_number(nums[-1])

    return data

# ---------- Validación ----------
def validate_invoice(data: dict, tolerance: Decimal = Decimal("0.01")):
    if all(k in data for k in ("net", "vat", "gross")):
        expected = quant2(data["net"] + data["vat"])
        detected = data["gross"]

        if data["net"] > data["gross"] * 5:
            print("\n⚠️ Posible error OCR: Subtotal demasiado alto.")
            net_str = str(data["net"])
            if len(net_str) > 4:
                try:
                    fixed = Decimal(net_str[1:])
                    print(f"   Intentando corregir Subtotal {data['net']} → {fixed}")
                    data["net"] = fixed
                except:
                    pass

        expected = quant2(data["net"] + data["vat"])
        diff = abs(expected - detected)
        ok = diff <= tolerance
        return ok, expected, detected, diff

    return False, Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

# ---------- Main ----------
if __name__ == "__main__":
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        title="Selecciona una factura",
        filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp")]
    )

    if not file_path:
        print("No seleccionaste ninguna imagen.")
    else:
        ocr_text = extract_text(file_path)

        if not ocr_text.strip():
            print("⚠️ No se detectó texto en la imagen. Verifica que esté clara y en formato PNG/JPG.")
        else:
            print("Texto extraído:\n", ocr_text)

            data = parse_invoice(ocr_text)
            ok, expected, detected, diff = validate_invoice(data)

            rows = [
                ["Subtotal / Base (NET)", data.get("net", "No detectado")],
                ["Impuesto IVA / TAX (VAT)", data.get("vat", "No detectado")],
                ["TOTAL / Importe total (GROSS)", data.get("gross", "No detectado")],
            ]
            print("\n📊 Resultados detectados (ya corregidos si hizo falta):\n")
            print(tabulate(rows, headers=["Campo", "Valor"], tablefmt="pretty"))

            if ok:
                print(f"\n✅ Cálculo correcto. Esperado={expected}  Detectado={detected}  Diferencia={diff}")
            else:
                if all(k in data for k in ("net", "vat", "gross")):
                    print("\n❌ Cálculo INCORRECTO.")
                    print(f"   Esperado (NET+VAT) = {expected}")
                    print(f"   Detectado (TOTAL)  = {detected}")
                    print(f"   Diferencia         = {diff} (tolerancia ≤ 0.01)")
                else:
                    faltan = [k for k in ("net", "vat", "gross") if k not in data]
                    print(f"\n⚠️ No se pudieron detectar todos los valores: faltan {', '.join(faltan)}.")
