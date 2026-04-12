import qrcode
import json

def qr_code_generator(data):
    """Generates a QR code from the given data.
    Args:        data (str): The data to encode in the QR code.
    Returns:
        PIL.Image: The generated QR code as an image.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# Load data from JSON file
with open('data\submissions.json', 'r') as f:
    data = json.load(f)
    
    
qr_code_generator(data)
