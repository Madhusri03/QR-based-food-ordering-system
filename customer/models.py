import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models

class Table(models.Model):
    table_number = models.CharField(max_length=50, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_occupied = models.BooleanField(default=False, db_index=True)
    occupied_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Table {self.table_number}"

    def save(self, *args, **kwargs):
        # Determine URL for QR code
        # In a real-world app, this would use the actual domain.
        # For development and presentation, we default to localhost:8000
        qr_data = f"http://127.0.0.1:8000/table/{self.table_number}/"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        filename = f"table_{self.table_number}_qr.png"
        
        # Save the generated image to the image field
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)
