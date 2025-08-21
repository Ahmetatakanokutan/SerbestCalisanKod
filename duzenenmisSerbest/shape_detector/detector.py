
# -*- coding: utf-8 -*-

"""
Görüntüler üzerinde renk tabanlı şekil tespiti yapan sınıfları içerir.
- Kırmızı üçgenleri ve mavi altıgenleri bulur.
"""

import cv2
import numpy as np
import sys
import os

# config.py dosyasının bulunduğu dizini Python yoluna ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    KIRMIZI_ALT_1, KIRMIZI_UST_1, KIRMIZI_ALT_2, KIRMIZI_UST_2,
    MAVI_ALT, MAVI_UST, MORFOLOJIK_CEKIRDEK,
    MIN_UCGEN_ALANI, MIN_ALTIGEN_ALANI,
    UCGEN_EPSILON_FAKTORU, ALTIGEN_EPSILON_FAKTORU
)

class SekilTespitEdici:
    """
    Görüntülerde belirli renklerdeki geometrik şekilleri tespit etmek için
    metotlar içeren ana sınıf.
    """

    def _renk_maskesi_olustur(self, resim, renk):
        """
        Belirtilen renk için bir HSV maskesi oluşturur ve morfolojik
        operasyonlarla gürültüyü temizler.
        """
        hsv = cv2.cvtColor(resim, cv2.COLOR_BGR2HSV)
        
        if renk == 'kirmizi':
            mask1 = cv2.inRange(hsv, KIRMIZI_ALT_1, KIRMIZI_UST_1)
            mask2 = cv2.inRange(hsv, KIRMIZI_ALT_2, KIRMIZI_UST_2)
            maske = cv2.bitwise_or(mask1, mask2)
        elif renk == 'mavi':
            maske = cv2.inRange(hsv, MAVI_ALT, MAVI_UST)
        else:
            return np.zeros(resim.shape[:2], dtype="uint8")
        
        maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, MORFOLOJIK_CEKIRDEK)
        maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, MORFOLOJIK_CEKIRDEK)
        return maske

    def kirmizi_ucgenleri_bul(self, resim):
        """
        Verilen bir görüntüdeki kırmızı üçgenleri tespit eder.
        """
        maske = self._renk_maskesi_olustur(resim, 'kirmizi')
        konturlar, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tespit_edilen_ucgenler = []
        for kontur in konturlar:
            if cv2.contourArea(kontur) < MIN_UCGEN_ALANI:
                continue
            
            epsilon = UCGEN_EPSILON_FAKTORU * cv2.arcLength(kontur, True)
            yaklasik_kontur = cv2.approxPolyDP(kontur, epsilon, True)

            if len(yaklasik_kontur) == 3:
                M = cv2.moments(kontur)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    tespit_edilen_ucgenler.append({
                        'sekil': 'ucgen', 
                        'renk': 'kirmizi', 
                        'merkez': (cx, cy)
                    })
        
        return tespit_edilen_ucgenler

    def mavi_altigenleri_bul(self, resim):
        """
        Verilen bir görüntüdeki mavi altıgenleri tespit eder.
        """
        maske = self._renk_maskesi_olustur(resim, 'mavi')
        konturlar, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tespit_edilen_altigenler = []
        for kontur in konturlar:
            if cv2.contourArea(kontur) < MIN_ALTIGEN_ALANI:
                continue

            epsilon = ALTIGEN_EPSILON_FAKTORU * cv2.arcLength(kontur, True)
            yaklasik_kontur = cv2.approxPolyDP(kontur, epsilon, True)

            if len(yaklasik_kontur) == 6:
                M = cv2.moments(kontur)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    tespit_edilen_altigenler.append({
                        'sekil': 'altigen', 
                        'renk': 'mavi', 
                        'merkez': (cx, cy)
                    })

        return tespit_edilen_altigenler
