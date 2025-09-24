# 🧾 OCR Facturas con Python + Tesseract

Este proyecto permite **extraer información de facturas en imagen (PNG/JPG)** usando OCR, y valida que el cálculo sea correcto (Subtotal + IVA = Total).

---

## ⚙️ Requisitos

Antes de ejecutar el programa, necesitas instalar lo siguiente:

### 1. Python
- Descarga e instala [Python 3.10+](https://www.python.org/downloads/).
- Verifica la instalación:
  ```bash
  python --version
  
2. Tesseract OCR

Descarga el instalador desde: Tesseract at UB Mannheim
.

Instálalo en tu sistema (ejemplo en Windows):

C:\Users\denis\AppData\Local\Programs\Tesseract-OCR

3. Dependencias de Python

Instala las librerías necesarias:

pip install pytesseract pillow tabulate

▶️ Ejecución

Clona este repositorio:

git clone https://github.com/DenisHamil/Factura.git
cd Factura


Ejecuta el script:

python ocr_invoice.py


Se abrirá un diálogo para elegir una imagen de factura (.png, .jpg, .jpeg, etc.).

El programa:

Extraerá el texto con OCR.

Buscará Subtotal, IVA y Total.

Verificará si el cálculo es correcto.

Mostrará un resumen como este:

📊 Resultados detectados (ya corregidos si hizo falta):

+-------------------------------+--------+
| Campo                         | Valor  |
+-------------------------------+--------+
| Subtotal / Base (NET)         | 165.00 |
| Impuesto IVA / TAX (VAT)      | 34.65  |
| TOTAL / Importe total (GROSS) | 199.65 |
+-------------------------------+--------+

✅ Cálculo correcto. Esperado=199.65  Detectado=199.65  Diferencia=0.00
