
# -*- coding: utf-8 -*-

"""
Piksel koordinatlarını GPS koordinatlarına dönüştüren matematiksel fonksiyonlar.
"""

import numpy as np
import cv2
from math import tan, radians, cos, pi

# Proje config dosyasından gerekli sabitleri import et
from config import (
    HFOV_DERECE, PITCH_DERECE, ROLL_DERECE, YAW_DERECE, DUNYA_YARICAPI
)

def piksel_to_gps(x, y, resim_genisligi, resim_yuksekligi, drone_enlem, drone_boylam, ucus_irtifasi):
    """
    Görüntüdeki bir pikselin koordinatını gerçek dünya GPS koordinatına çevirir.
    
    Args:
        x (int): Pikselin x koordinatı.
        y (int): Pikselin y koordinatı.
        resim_genisligi (int): Görüntünün toplam genişliği.
        resim_yuksekligi (int): Görüntünün toplam yüksekliği.
        drone_enlem (float): Drone'un anlık enlemi (ondalık derece).
        drone_boylam (float): Drone'un anlık boylamı (ondalık derece).
        ucus_irtifasi (float): Drone'un yerden yüksekliği (metre).

    Returns:
        tuple: Hesaplanan (enlem, boylam) veya hata durumunda orijinal (drone_enlem, drone_boylam).
    """
    # Kamera içsel parametrelerini hesapla
    hfov = radians(HFOV_DERECE)
    vfov = hfov * (resim_yuksekligi / resim_genisligi)

    fx = resim_genisligi / (2 * tan(hfov / 2))
    fy = resim_yuksekligi / (2 * tan(vfov / 2))
    cx = resim_genisligi / 2
    cy = resim_yuksekligi / 2

    # İçsel parametre matrisinin tersi (K_inv)
    K_inv = np.linalg.inv(np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]]))
    
    # 2D piksel noktasını 3D ışına dönüştür
    piksel_vektoru = np.array([x, y, 1.0])
    kamera_koordinatinda_isin = K_inv @ piksel_vektoru
    kamera_koordinatinda_isin /= np.linalg.norm(kamera_koordinatinda_isin)

    # Dışsal parametreler: Drone'un yönelimi (Euler açıları)
    R_matrix = cv2.Rodrigues(np.array([radians(PITCH_DERECE), radians(ROLL_DERECE), radians(YAW_DERECE)]))[0]
    
    # Işını kamera koordinat sisteminden dünya koordinat sistemine dönüştür
    dunya_koordinatinda_isin = R_matrix @ kamera_koordinatinda_isin
    
    if dunya_koordinatinda_isin[2] <= 1e-6:
        return drone_enlem, drone_boylam

    olcek = ucus_irtifasi / dunya_koordinatinda_isin[2]
    yer_noktasi = dunya_koordinatinda_isin * olcek

    offset_kuzey = yer_noktasi[1]
    offset_dogu = yer_noktasi[0]

    dlat = offset_kuzey / DUNYA_YARICAPI * (180 / pi)
    dlon = offset_dogu / (DUNYA_YARICAPI * cos(radians(drone_enlem))) * (180 / pi)

    yeni_enlem = drone_enlem + dlat
    yeni_boylam = drone_boylam + dlon

    return yeni_enlem, yeni_boylam
