# -*- coding: utf-8 -*-

"""
Canlı video akışını (webcam veya video dosyası) işleyen modül.
Her bir karede kırmızı üçgen ve mavi altıgen tespiti yapar ve
sonuçları gerçek zamanlı olarak ekranda gösterir.
"""

import cv2
import sys
import os

# Proje kök dizinini Python yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shape_detector.detector import SekilTespitEdici

def sonuclari_gorsellestir(frame, tespitler):
    """
    Tespit edilen şekilleri video karesi üzerine çizer.
    """
    if not tespitler:
        return frame

    for tespit in tespitler:
        merkez = tespit['merkez']
        renk_str = tespit['renk']
        sekil_str = tespit['sekil']
        
        # Tespit edilen renge göre çizim rengi belirle (BGR formatında)
        cizim_rengi = (255, 0, 0) if renk_str == 'mavi' else (0, 0, 255)

        # Şeklin merkezine bir daire çiz
        cv2.circle(frame, merkez, 10, cizim_rengi, 2)
        
        # Bilgi metni ekle
        metin = f"{renk_str.upper()} {sekil_str.upper()}"
        cv2.putText(frame, metin, (merkez[0] - 40, merkez[1] - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, cizim_rengi, 2)
    
    return frame

def video_akisini_baslat(kaynak=0):
    """
    Belirtilen kaynaktan video akışını başlatır ve işlemeye başlar.
    
    Args:
        kaynak (int or str): Kamera indeksi (örn: 0) veya video dosyasının yolu.
    """
    cap = cv2.VideoCapture(kaynak)
    if not cap.isOpened():
        print(f"[HATA] Video kaynağı açılamadı: {kaynak}")
        print("Lütfen kamera bağlantınızı veya dosya yolunu kontrol edin.")
        return

    print("[BİLGİ] Video akışı başlatıldı. Çıkmak için 'q' tuşuna basın.")
    
    sekil_tespit_edici = SekilTespitEdici()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[BİLGİ] Video akışı sona erdi.")
            break

        # Şekilleri tespit et
        kirmizi_ucgenler = sekil_tespit_edici.kirmizi_ucgenleri_bul(frame)
        mavi_altigenler = sekil_tespit_edici.mavi_altigenleri_bul(frame)
        tum_tespitler = kirmizi_ucgenler + mavi_altigenler

        # Konsola anlık bilgi yazdır (isteğe bağlı)
        if tum_tespitler:
            print(f"\rTespit edilenler: {len(tum_tespitler)} adet", end="")

        # Sonuçları görselleştir
        gorsellestirilmis_frame = sonuclari_gorsellestir(frame, tum_tespitler)

        # İşlenmiş kareyi ekranda göster
        cv2.imshow("Canli Tespit Sistemi", gorsellestirilmis_frame)

        # 'q' tuşuna basıldığında döngüden çık
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Kaynakları serbest bırak
    cap.release()
    cv2.destroyAllWindows()
    print("\n[BİLGİ] Video akışı kapatıldı.")
