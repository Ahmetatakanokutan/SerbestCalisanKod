
# -*- coding: utf-8 -*-

"""
Projenin tüm konfigürasyon parametreleri ve sabitleri bu dosyada yer alır.
"""

import numpy as np
import os

# ==== DOSYA YOLLARI ====
# Bu dosyanın bulunduğu dizini alarak başla
# duzenenmisSerbest/
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
# Projenin kök dizinine çık (SerbestCalisanKod/)
BASE_DIR = os.path.dirname(CONFIG_DIR)

IZLENECEK_KLASOR = os.path.join(BASE_DIR, "files", "images")
CIKTI_CSV = os.path.join(BASE_DIR, "files", "detections", "tespitler.csv")


# ==== KAMERA VE GPS PARAMETRELERİ ====
HFOV_DERECE = 78.0  # Yatay Görüş Açısı (Horizontal Field of View)
EV_RAKIMI = 72.0    # Drone'un kalktığı yerin deniz seviyesinden yüksekliği (metre)
YAW_DERECE = 0.0
PITCH_DERECE = 0.0
ROLL_DERECE = 0.0
DUNYA_YARICAPI = 6378137  # Metre

# ==== RENK TESPİT PARAMETRELERİ (HSV RENK UZAYI) ====
# Kırmızı için iki farklı aralık (HSV'de kırmızı hem 0 hem 180 etrafında bulunur)
KIRMIZI_ALT_1 = np.array([0, 120, 70])
KIRMIZI_UST_1 = np.array([10, 255, 255])
KIRMIZI_ALT_2 = np.array([170, 120, 70])
KIRMIZI_UST_2 = np.array([180, 255, 255])

# Mavi için aralık
MAVI_ALT = np.array([100, 150, 50])
MAVI_UST = np.array([140, 255, 255])

# ==== GÖRÜNTÜ İŞLEME PARAMETRELERİ ====
# Şekil tespiti için kontur alan eşikleri
MIN_UCGEN_ALANI = 100
MIN_ALTIGEN_ALANI = 150

# Kontur yaklaştırma (approximation) için epsilon değerleri
UCGEN_EPSILON_FAKTORU = 0.04
ALTIGEN_EPSILON_FAKTORU = 0.03

# Morfolojik operasyonlar için çekirdek (kernel) boyutu
MORFOLOJIK_CEKIRDEK = np.ones((5, 5), np.uint8)
