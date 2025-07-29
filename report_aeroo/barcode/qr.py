# © Numigi (tm) and all its contributors (https://numigi.com/r/home)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def make_qr_code(code):
    import qrcode

    qr = qrcode.QRCode(box_size=10)
    qr.add_data(code)
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white")
