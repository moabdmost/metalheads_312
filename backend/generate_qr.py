import qrcode
import json
def qr_code_generator(data):
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


with open('data\submissions.json', 'r') as f:
    data = json.load(f)
    
    
qr_code_generator(data)
