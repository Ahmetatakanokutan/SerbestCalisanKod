# -*- coding: utf-8 -*-

"""
This module contains helper functions for reading EXIF metadata from image files.
It uses the 'piexif' library to extract GPS data.
"""

import piexif

def get_exif_data(image_path):
    """
    Extracts EXIF data from an image file.
    Args:
        image_path (str): The path to the image file.
    Returns:
        dict: A dictionary containing the EXIF data, or None on error.
    """
    try:
        exif_dict = piexif.load(image_path)
        return exif_dict
    except Exception:
        return None

def get_lat_lon_alt(exif_dict):
    """
    Parses GPS latitude, longitude, and altitude from an EXIF dictionary.
    Args:
        exif_dict (dict): The EXIF dictionary returned by piexif.
    Returns:
        tuple: (latitude, longitude, altitude) or (None, None, None) if not found.
    """
    if not exif_dict or 'GPS' not in exif_dict:
        return None, None, None

    gps_ifd = exif_dict.get('GPS', {})
    
    def exif_gps_to_dec(gps_coords, gps_ref):
        """Converts EXIF GPS format to decimal degrees."""
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

    latitude = exif_gps_to_dec(
        gps_ifd.get(piexif.GPSIFD.GPSLatitude), 
        gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
    )
    longitude = exif_gps_to_dec(
        gps_ifd.get(piexif.GPSIFD.GPSLongitude), 
        gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)
    )
    
    altitude_data = gps_ifd.get(piexif.GPSIFD.GPSAltitude)
    altitude = (altitude_data[0] / altitude_data[1]) if altitude_data and altitude_data[1] != 0 else None
    
    return latitude, longitude, altitude