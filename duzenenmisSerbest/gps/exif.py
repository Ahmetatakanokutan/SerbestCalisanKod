
# -*- coding: utf-8 -*-

"""
Görüntü dosyalarından EXIF meta verilerini okumak için yardımcı fonksiyonlar.
Bu modül, GPS verilerini çıkarmak için 'piexif' kütüphanesini kullanır.
"""

import piexif

def exif_verisi_al(resim_yolu):
    """
    Bir resim dosyasından EXIF verilerini çeker.
    Args:
        resim_yolu (str): Görüntü dosyasının yolu.
    Returns:
        dict: EXIF verilerini içeren sözlük veya hata durumunda None.
    """
    try:
        exif_dict = piexif.load(resim_yolu)
        return exif_dict
    except Exception as e:
        # piexif'in bazen 'ValueError: Given data isn't JPEG.' hatası vermesi yaygındır.
        # Bu durumu ve diğer hataları yakalıyoruz.
        # print(f"[HATA] EXIF verisi okunamadı: {resim_yolu} - {e}")
        return None

def enlem_boylam_rakim_al(exif_dict):
    """
    EXIF sözlüğünden GPS enlem, boylam ve rakım bilgilerini ayrıştırır.
    Args:
        exif_dict (dict): piexif tarafından döndürülen EXIF sözlüğü.
    Returns:
        tuple: (enlem, boylam, rakım) veya veri yoksa (None, None, None).
    """
    if not exif_dict or 'GPS' not in exif_dict:
        return None, None, None

    gps_ifd = exif_dict.get('GPS', {})
    
    def exif_gps_to_dec(gps_coords, gps_ref):
        """EXIF GPS formatını ondalık dereceye çevirir."""
        if not gps_coords or not gps_ref:
            return None
        try:
            d, m, s = [val[0] / val[1] for val in gps_coords]
            dec = d + m / 60.0 + s / 3600.0
            ref = gps_ref.decode()
            if ref in ['S', 'W']:
                dec = -dec
            return dec
        except (ValueError, ZeroDivisionError, TypeError, IndexError):
            return None

    enlem = exif_gps_to_dec(
        gps_ifd.get(piexif.GPSIFD.GPSLatitude), 
        gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
    )
    boylam = exif_gps_to_dec(
        gps_ifd.get(piexif.GPSIFD.GPSLongitude), 
        gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)
    )
    
    rakim_verisi = gps_ifd.get(piexif.GPSIFD.GPSAltitude)
    rakim = (rakim_verisi[0] / rakim_verisi[1]) if rakim_verisi and rakim_verisi[1] != 0 else None
    
    return enlem, boylam, rakim
