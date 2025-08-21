# -*- coding: utf-8 -*-

"""
Bir klasörü sürekli olarak izleyen ve yeni eklenen görüntüleri
bir iş kuyruğuna ekleyerek arka planda işlenmesini sağlayan modül.
"""

import os
import time
import glob
import queue
import csv
import cv2
import sys

# Proje kök dizinini Python yoluna ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import IZLENECEK_KLASOR, CIKTI_CSV, EV_RAKIMI
from gps.exif import exif_verisi_al, enlem_boylam_rakim_al
from gps.calculator import piksel_to_gps
from shape_detector.detector import SekilTespitEdici

is_kuyrugu = queue.Queue()
islenen_dosyalar = set()

def resim_isleyici_worker():
    """
    Kuyruktan resim yollarını alır, şekil tespiti ve GPS hesaplaması yapar,
    ve sonuçları CSV dosyasına yazar.
    """
    sekil_tespit_edici = SekilTespitEdici()
    
    while True:
        resim_yolu = is_kuyrugu.get()
        if resim_yolu is None:
            break

        print(f"\n[İŞLENİYOR] Dosya: {os.path.basename(resim_yolu)}")
        
        try:
            exif_verisi = exif_verisi_al(resim_yolu)
            if not exif_verisi:
                print(f"[UYARI] EXIF verisi okunamadı veya format desteklenmiyor: {os.path.basename(resim_yolu)}")
                continue
            
            drone_enlem, drone_boylam, drone_rakim = enlem_boylam_rakim_al(exif_verisi)
            if drone_enlem is None or drone_boylam is None or drone_rakim is None:
                print(f"[UYARI] GPS verisi eksik veya okunamadı: {os.path.basename(resim_yolu)}")
                continue
            
            ucus_irtifasi = drone_rakim - EV_RAKIMI
            print(f"  -> GPS: ({drone_enlem:.6f}, {drone_boylam:.6f}), İrtifa: {ucus_irtifasi:.2f}m")

            resim = cv2.imread(resim_yolu)
            if resim is None:
                print(f"[HATA] Görüntü yüklenemedi: {resim_yolu}")
                continue
            
            resim_yuksekligi, resim_genisligi, _ = resim.shape

            kirmizi_ucgenler = sekil_tespit_edici.kirmizi_ucgenleri_bul(resim)
            mavi_altigenler = sekil_tespit_edici.mavi_altigenleri_bul(resim)
            tum_tespitler = kirmizi_ucgenler + mavi_altigenler
            
            if not tum_tespitler:
                print("  -> Herhangi bir şekil tespit edilemedi.")
                continue
            
            print(f"  -> Tespit edilenler: {len(tum_tespitler)} şekil")

            with open(CIKTI_CSV, "a", newline="", encoding='utf-8') as f:
                yazici = csv.writer(f)
                for tespit in tum_tespitler:
                    merkez_x, merkez_y = tespit['merkez']
                    
                    enlem, boylam = piksel_to_gps(
                        merkez_x, merkez_y, resim_genisligi, resim_yuksekligi,
                        drone_enlem, drone_boylam, ucus_irtifasi
                    )
                    
                    print(f"    -> {tespit['renk'].upper()} {tespit['sekil'].upper()} @ ({merkez_x},{merkez_y}) -> GPS: ({enlem:.7f}, {boylam:.7f})")
                    
                    yazici.writerow([
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        os.path.basename(resim_yolu),
                        tespit['sekil'],
                        tespit['renk'],
                        f"{enlem:.7f}",
                        f"{boylam:.7f}"
                    ])
        
        except Exception as e:
            print(f"[KRİTİK HATA] {os.path.basename(resim_yolu)} işlenirken beklenmedik bir hata oluştu: {e}")
        
        finally:
            is_kuyrugu.task_done()

def klasor_izleyici():
    """
    Belirtilen klasörü periyodik olarak yeni görüntüler için tarar.
    """
    print(f"[BAŞLATILDI] Klasör izleniyor: {os.path.abspath(IZLENECEK_KLASOR)}")
    if not os.path.isdir(IZLENECEK_KLASOR):
        print(f"[HATA] İzlenecek klasör bulunamadı: {IZLENECEK_KLASOR}")
        return

    while True:
        resim_dosyalari = glob.glob(os.path.join(IZLENECEK_KLASOR, "*.jpg")) + \
                           glob.glob(os.path.join(IZLENECEK_KLASOR, "*.jpeg")) + \
                           glob.glob(os.path.join(IZLENECEK_KLASOR, "*.png"))
        
        yeni_resimler = [f for f in resim_dosyalari if f not in islenen_dosyalar]

        if yeni_resimler:
            for resim_yolu in sorted(yeni_resimler):
                print(f"[BULUNDU] Yeni resim kuyruğa ekleniyor: {os.path.basename(resim_yolu)}")
                islenen_dosyalar.add(resim_yolu)
                is_kuyrugu.put(resim_yolu)
            
        time.sleep(5)
