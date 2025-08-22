
# Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi

Bu proje, bir görüntü klasörünü veya canlı bir video akışını (yerel kamera veya RTSP) işleyerek kırmızı üçgenleri ve mavi altıgenleri tespit eden modüler bir bilgisayarlı görü sistemidir. Sistem, tespit edilen nesnelerin GPS koordinatlarını hesaplayabilir (görüntü dosyaları için) veya sonuçları canlı olarak ekranda gösterebilir (video akışı için).

## Temel Özellikler

- **İki Farklı Çalışma Modu**:
  1.  **Klasör İzleme (`folder`)**: Belirtilen bir klasöre eklenen yeni görüntüleri otomatik olarak işler. Görüntüdeki EXIF meta verilerinden GPS bilgilerini okur, tespit edilen şekillerin gerçek dünya koordinatlarını hesaplar ve sonuçları bir CSV dosyasına kaydeder.
  2.  **Canlı Video (`webcam`)**: Yerel bir USB kameradan veya bir ağ RTSP akışından (drone kamerası gibi) gelen video görüntülerini gerçek zamanlı olarak analiz eder ve tespit edilen şekilleri ekranda görselleştirir.
- **Modüler ve Genişletilebilir Mimari**: Proje, her biri belirli bir göreve odaklanmış (yapılandırma, GPS işlemleri, şekil tespiti, dosya izleme, video işleme) ayrı Python paketlerine bölünmüştür. Bu, kodun bakımını ve yeni özellikler eklenmesini kolaylaştırır.
- **Sağlam Video Yakalama**: Özellikle Linux tabanlı sistemlerde (Raspberry Pi dahil) kararlı çalışması için GStreamer altyapısını kullanır.
- **Detaylı Yapılandırma**: Tüm önemli parametreler (dosya yolları, renk aralıkları, kamera ayarları vb.) `config.py` dosyasından kolayca yönetilebilir.

---

## Proje Yapısı

Proje, aşağıdaki gibi modüler bir yapıda organize edilmiştir:

```
duzenenmisSerbest/
├── main.py                 # Ana başlatıcı betik, komut satırı argümanlarını yönetir.
├── config.py               # Tüm global ayarlar ve sabitler.
├── video_processor.py      # Canlı video akışını (GStreamer ile) işleyen modül.
│
├── file_watcher/
│   ├── __init__.py
│   └── watcher.py          # Klasör izleme ve arka plan işleme (threading) mantığı.
│
├── gps/
│   ├── __init__.py
│   ├── exif.py             # Görüntülerden EXIF ve GPS verilerini okur.
│   └── calculator.py       # Piksel koordinatlarını GPS koordinatlarına çevirir.
│
└── shape_detector/
    ├── __init__.py
    └── detector.py         # Renk ve şekil tespiti yapan ana sınıfı içerir.
```

---

## Kurulum ve Hazırlık

Sistemi çalıştırmadan önce aşağıdaki adımların tamamlanması gerekmektedir.

### 1. Sistem Bağımlılıkları (GStreamer)

Bu projenin video işleme yetenekleri, GStreamer ve eklentilerine bağlıdır. Özellikle RTSP akışları ve çeşitli video formatları için bu eklentilerin sistemde yüklü olması **zorunludur**.

Debian tabanlı bir sistemde (Debian, Ubuntu, Raspberry Pi OS) aşağıdaki komutla tüm gerekli GStreamer eklentilerini kurun:

```bash
sudo apt-get update
sudo apt-get install -y gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
```

### 2. Python Kütüphaneleri

Projenin ihtiyaç duyduğu Python kütüphanelerini `pip` kullanarak yükleyin:

```bash
pip install opencv-python numpy piexif
```

---

## Kullanım

Program, `main.py` betiği aracılığıyla komut satırından çalıştırılır ve `--mod` argümanı ile hangi modda çalışacağı belirtilir.

### Mod 1: Klasör İzleme (GPS Destekli)

Bu mod, `files/images` klasörüne eklenen, EXIF GPS verisi içeren görüntüleri işler.

**Çalıştırma Komutu:**
```bash
python3 main.py --mod folder
```

**İş Akışı:**
1.  Yukarıdaki komutu çalıştırdığınızda, program `files/images` klasörünü izlemeye başlar.
2.  Bu klasörün içine `.jpg` veya `.png` uzantılı bir veya daha fazla görüntü dosyası kopyalayın.
3.  Program yeni dosyaları algılar, arka planda işlemeye başlar.
4.  Tespit edilen her kırmızı üçgen ve mavi altıgen için GPS koordinatları hesaplanır.
5.  Tüm sonuçlar, `files/detections/detections.csv` dosyasına zaman damgasıyla birlikte kaydedilir.

### Mod 2: Canlı Video (Webcam veya RTSP)

Bu mod, bir video kaynağını gerçek zamanlı olarak işler.

#### a) Yerel USB Kamera ile Kullanım

Sisteminize bağlı bir USB kamerayı kullanmak için `--camera_index` argümanını kullanın. Genellikle bu `0`'dır.

**Çalıştırma Komutu:**
```bash
python3 main.py --mod webcam --camera_index 0
```

#### b) RTSP Ağ Akışı ile Kullanım (Drone Kamerası)

Bir ağ üzerinden yayın yapan RTSP akışına bağlanmak için `--rtsp_url` argümanını kullanın.

**Çalıştırma Komutu:**
```bash
python3 main.py --mod webcam --rtsp_url "rtsp://192.168.144.25:8554/main.264"
```
**Not:** RTSP URL'sini tırnak (`"`) içine almanız önemlidir.

---

## Sıkça Karşılaşılan Sorunlar ve Çözümleri

#### 1. Sorun: `[ERROR] Could not open video source...`
   - **Anlamı**: GStreamer, belirtilen video akışını (RTSP veya yerel kamera) başlatmak için gerekli eklentileri bulamıyor.
   - **Çözüm**: Kurulum bölümündeki **Sistem Bağımlılıkları (GStreamer)** adımını uyguladığınızdan ve tüm `gstreamer1.0-plugins-*` paketlerini kurduğunuzdan emin olun.

#### 2. Sorun: `apt-get update` komutu "Release file is not valid yet" hatası veriyor.
   - **Anlamı**: Sisteminizin (Raspberry Pi vb.) tarihi ve saati yanlış. Paket yöneticisi, gelecekteki bir tarihe sahip olduğu için yazılım listelerini geçersiz sayıyor.
   - **Çözüm**: Sistemin saatini doğru şekilde ayarlayın. En güvenilir yöntem aşağıdaki komuttur:
     ```bash
     sudo date -s "YYYY-MM-DD HH:MM:SS"
     # Örnek: sudo date -s "2025-08-21 22:30:00"
     ```
     Saati ayarladıktan sonra GStreamer kurulum komutunu tekrar çalıştırın.

#### 3. Sorun: Yerel kamera (`--camera_index`) ile çalıştırıldığında program tepki vermiyor veya `select() timeout` uyarısı veriyor.
   - **Anlamı**: OpenCV, belirtilen kamera indeksiyle iletişim kuramıyor.
   - **Çözüm**:
     1.  `ls /dev/video*` komutuyla sisteminizdeki mevcut tüm video aygıtlarını listeleyin.
     2.  Programı, bu listede gördüğünüz farklı numaraları (`--camera_index 19`, `--camera_index 20` vb.) deneyerek çalıştırın.
     3.  Sorun devam ederse, bu genellikle GStreamer eklentilerinin eksik olduğu anlamına gelir. 1. çözümü kontrol edin.
