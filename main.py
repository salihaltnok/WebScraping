import time
import csv
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def tarayici_baslat():
    secenekler = Options()
    secenekler.add_argument("--start-maximized")  #tarayıcıyı tam ekran başlatma
    secenekler.add_argument("--disable-notifications")  #bildirimleri kapatma

    tarayici = webdriver.Chrome(options=secenekler)
    return tarayici

def urunleri_topla(tarayici, url, sayfa_limiti=3):
    tarayici.get(url)
    time.sleep(3)  #sayfa yüklenene kadar bekleme

    try:
        cerez_butonu = tarayici.find_element(By.ID, "onetrust-accept-btn-handler") #cerezleri kabul etme
        cerez_butonu.click()
        time.sleep(1)
    except:
        print("Çerez uyarısı bulunamadı veya zaten kabul edildi.")

    urunler = []
    mevcut_sayfa = 1

    while mevcut_sayfa <= sayfa_limiti:
        print(f"Sayfa {mevcut_sayfa} taranıyor...")
        time.sleep(2)
        urun_kartlari = tarayici.find_elements(By.CSS_SELECTOR, "div.p-card-wrppr")
        print(f"{len(urun_kartlari)} ürün kartı bulundu.")

        for kart in urun_kartlari:
            try:
                try:
                    urun_adi = kart.find_element(By.CSS_SELECTOR, "div.prdct-desc-cntnr-name").text
                except:
                    try:
                        urun_adi = kart.find_element(By.CSS_SELECTOR, "span.prdct-desc-cntnr-name").text
                    except:
                        urun_adi = "Ürün adı alınamadı"
                try:
                    fiyat = kart.find_element(By.CSS_SELECTOR, "div.prc-box-dscntd").text
                except:
                    try:
                        fiyat = kart.find_element(By.CSS_SELECTOR, "div.prc-box-sllng").text
                    except:
                        fiyat = "Fiyat bulunamadı"
                try:
                    fiyat_temiz = fiyat.replace("TL", "").replace(".", "").replace(",", ".").strip()
                    fiyat_sayisal = float(fiyat_temiz)
                except:
                    fiyat_sayisal = 0.0
                try:
                    satici = kart.find_element(By.CSS_SELECTOR, "span.prdct-desc-cntnr-ttl").text
                except:
                    satici = "Belirtilmemiş"
                try:
                    degerlendirme = kart.find_element(By.CSS_SELECTOR, "div.ratings").get_attribute("title")
                except:
                    degerlendirme = "Değerlendirilmemiş"
                try:
                    urun_linki = kart.find_element(By.TAG_NAME, "a").get_attribute("href")
                except:
                    urun_linki = "Link bulunamadı"

                urunler.append({
                    "Ürün Adı": urun_adi,
                    "Fiyat": fiyat,
                    "Fiyat (Sayısal)": fiyat_sayisal,
                    "Satıcı": satici,
                    "Değerlendirme": degerlendirme,
                    "Ürün Linki": urun_linki
                })

                print(f"Ürün eklendi: {urun_adi[:30]}... - {fiyat}")
            except Exception as e:
                print(f"Ürün çekilirken hata: {e}")

        if mevcut_sayfa < sayfa_limiti:
            try:
                sonraki_sayfa = tarayici.find_element(By.CSS_SELECTOR, "a.next-sibling")
                tarayici.execute_script("arguments[0].scrollIntoView();", sonraki_sayfa)
                time.sleep(1)
                sonraki_sayfa.click()
                time.sleep(3)
                mevcut_sayfa += 1
            except:
                mevcut_sayfa += 1
                sonraki_url = url + f"&pi={mevcut_sayfa}"
                tarayici.get(sonraki_url)
                time.sleep(3)
        else:
            break
    return urunler

def verileri_kaydet(urunler, dosya_adi="trendyol_urunler.csv"):
    if not urunler:
        print("Kaydedilecek ürün bulunamadı!")
        return

    with open(dosya_adi, 'w', newline='', encoding='utf-8') as csvfile:
        alanlar = ["Ürün Adı", "Fiyat", "Fiyat (Sayısal)", "Satıcı", "Değerlendirme", "Ürün Linki"]
        yazici = csv.DictWriter(csvfile, fieldnames=alanlar)

        yazici.writeheader()
        for urun in urunler:
            yazici.writerow(urun)

    print(f"Ürün verileri {dosya_adi} dosyasına kaydedildi.")

def urun_detaylarini_cek(tarayici, urun_linki):
    tarayici.get(urun_linki)
    time.sleep(3)  #sayfa yüklenene kadar bekle

    detaylar = {}

    try:
        baslik = tarayici.find_element(By.CSS_SELECTOR, "h1.pr-new-br").text
        detaylar["Ürün Başlığı"] = baslik
    except:
        detaylar["Ürün Başlığı"] = "Alınamadı"
    try:
        marka = tarayici.find_element(By.CSS_SELECTOR, "h1.pr-new-br a").text
        detaylar["Marka"] = marka
    except:
        detaylar["Marka"] = "Alınamadı"
    try:
        fiyat = tarayici.find_element(By.CSS_SELECTOR, "span.prc-dsc").text
        detaylar["Güncel Fiyat"] = fiyat
    except:
        detaylar["Güncel Fiyat"] = "Alınamadı"
    try:
        satici = tarayici.find_element(By.CSS_SELECTOR, "a.merchant-title").text
        detaylar["Satıcı"] = satici
    except:
        try:
            merchant_id = re.search(r'merchantId=(\d+)', urun_linki)
            if merchant_id:
                satici_id = merchant_id.group(1)
                if satici_id == "968":
                    detaylar["Satıcı"] = "Trendyol"
                else:
                    detaylar["Satıcı"] = f"Satıcı ID: {satici_id}"
            else:
                detaylar["Satıcı"] = "Alınamadı"
        except:
            detaylar["Satıcı"] = "Alınamadı"

    try:
        puan = tarayici.find_element(By.CSS_SELECTOR, "div.pr-rnr-sm-p").text
        detaylar["Ürün Puanı"] = puan
    except:
        detaylar["Ürün Puanı"] = "Alınamadı"
    detaylar["Teknik Özellikler"] = {}

    try:

        tarayici.execute_script("window.scrollBy(0, 500);")#sayfayı aşağı kaydır
        time.sleep(1)
        detay_buton = tarayici.find_element(By.CSS_SELECTOR, "button.detail-button, button.pr-tab:nth-child(2)")
        tarayici.execute_script("arguments[0].scrollIntoView();", detay_buton)
        detay_buton.click()
        time.sleep(2)
        ozellik_listesi = tarayici.find_elements(By.CSS_SELECTOR, "div.detail-attr-container")

        for ozellik in ozellik_listesi:
            try:
                ozellik_adi = ozellik.find_element(By.CSS_SELECTOR, "div.detail-attr-name").text
                ozellik_degeri = ozellik.find_element(By.CSS_SELECTOR, "div.detail-attr-value").text
                detaylar["Teknik Özellikler"][ozellik_adi] = ozellik_degeri
            except:
                continue
    except:
        if "İşlemci" not in detaylar["Teknik Özellikler"]:
            if "intel" in urun_linki.lower() or "i5" in urun_linki.lower():
                detaylar["Teknik Özellikler"]["İşlemci"] = "intel"
            elif "ryzen" in urun_linki.lower():
                detaylar["Teknik Özellikler"]["İşlemci"] = "ryzen"
            elif "mediatek" in urun_linki.lower():
                detaylar["Teknik Özellikler"]["İşlemci"] = "mediatek"

        if "Ekran" not in detaylar["Teknik Özellikler"]:
            ekran_bul = re.search(r'(\d+[.,]\d+)["\'"]', detaylar.get("Ürün Başlığı", ""))
            if ekran_bul:
                detaylar["Teknik Özellikler"]["Ekran"] = ekran_bul.group(1)

    return detaylar

def tum_urun_detaylarini_cek(giris_csv="trendyol_urunler.csv", cikis_csv="trendyol_detayli_urunler.csv"):
    try:
        df = pd.read_csv(giris_csv)
    except:
        print(f"{giris_csv} dosyası bulunamadı!")
        return
    linkler = df["Ürün Linki"].tolist()
    print(f"Toplam {len(linkler)} ürün detayı çekilecek.")
    tarayici = tarayici_baslat()

    tum_detaylar = []

    for i, link in enumerate(linkler, 1):
        print(f"{i}/{len(linkler)} - Ürün detayları çekiliyor: {link}")

        detaylar = urun_detaylarini_cek(tarayici, link)
        urun_bilgisi = df[df["Ürün Linki"] == link].iloc[0].to_dict()
        birlesik_bilgi = {**urun_bilgisi, **detaylar}
        tum_detaylar.append(birlesik_bilgi)
        time.sleep(2)

    tarayici.quit()

    if tum_detaylar:
        for urun in tum_detaylar:
            if "Teknik Özellikler" in urun and isinstance(urun["Teknik Özellikler"], dict):
                for ozellik_adi, ozellik_degeri in urun["Teknik Özellikler"].items():
                    urun[f"Özellik: {ozellik_adi}"] = ozellik_degeri
                del urun["Teknik Özellikler"]

        tum_sutunlar = set()
        for urun in tum_detaylar:
            for anahtar in urun.keys():
                tum_sutunlar.add(anahtar)

        with open(cikis_csv, 'w', newline='', encoding='utf-8') as csvfile:
            yazici = csv.DictWriter(csvfile, fieldnames=list(tum_sutunlar))
            yazici.writeheader()
            for urun in tum_detaylar:
                yazici.writerow(urun)
        print(f"Detaylı ürün verileri {cikis_csv} dosyasına kaydedildi.")
    else:
        print("Kaydedilecek detaylı ürün verisi bulunamadı!")


def verileri_analiz_et(dosya_adi="trendyol_detayli_urunler.csv"):
    try:
        df = pd.read_csv(dosya_adi)
    except:
        print(f"{dosya_adi} dosyası bulunamadı!")
        return

    df["Fiyat Sayısal"] = 0.0

    for i, satir in df.iterrows():
        fiyat_metni = satir.get("Güncel Fiyat", satir.get("Fiyat", ""))
        try:
            fiyat_temiz = re.sub(r'[^0-9.,]', '', str(fiyat_metni))
            fiyat_temiz = fiyat_temiz.replace(".", "").replace(",", ".")
            df.at[i, "Fiyat Sayısal"] = float(fiyat_temiz)
        except:
            pass

    for i, satir in df.iterrows():
        fiyat = satir["Fiyat Sayısal"]
        if 0 < fiyat < 100:  # Çok düşük fiyat
            df.at[i, "Fiyat Sayısal"] = fiyat * 1000

    en_ucuz = df[df["Fiyat Sayısal"] > 0].sort_values(by="Fiyat Sayısal")[:5]
    en_pahali = df[df["Fiyat Sayısal"] > 0].sort_values(by="Fiyat Sayısal", ascending=False)[:5]

    print("\n=== EN UCUZ 5 ÜRÜN ===")
    for i, (_, urun) in enumerate(en_ucuz.iterrows(), 1):
        print(
            f"{i}. {urun.get('Ürün Adı', 'Bilinmeyen')} - {urun.get('Güncel Fiyat', urun.get('Fiyat', 'Bilinmeyen'))} - Satıcı: {urun.get('Satıcı', 'Bilinmeyen')}")

    print("\n=== EN PAHALI 5 ÜRÜN ===")
    for i, (_, urun) in enumerate(en_pahali.iterrows(), 1):
        print(
            f"{i}. {urun.get('Ürün Adı', 'Bilinmeyen')} - {urun.get('Güncel Fiyat', urun.get('Fiyat', 'Bilinmeyen'))} - Satıcı: {urun.get('Satıcı', 'Bilinmeyen')}")

    satici_df = df[(df["Satıcı"] != "Alınamadı") & (df["Fiyat Sayısal"] > 0)]

    if not satici_df.empty:
        satici_ort = satici_df.groupby("Satıcı")["Fiyat Sayısal"].mean().sort_values(ascending=False)

        print("\n=== SATICILARA GÖRE ORTALAMA FİYAT ===")
        for satici, ort_fiyat in satici_ort.items():
            print(f"{satici}: {ort_fiyat:.2f} TL")
    else:
        print("\n=== SATICILARA GÖRE ORTALAMA FİYAT ===")
        print("Yeterli satıcı bilgisi bulunamadı.")

    print("\n=== İSTATİSTİKSEL ÖZET ===")
    print(f"Toplam Ürün Sayısı: {len(df)}")

    gecerli_fiyatlar = df[df["Fiyat Sayısal"] > 0]["Fiyat Sayısal"]
    if not gecerli_fiyatlar.empty:
        print(f"Ortalama Fiyat: {gecerli_fiyatlar.mean():.2f} TL")
        print(f"Medyan Fiyat: {gecerli_fiyatlar.median():.2f} TL")
        print(f"En Düşük Fiyat: {gecerli_fiyatlar.min():.2f} TL")
        print(f"En Yüksek Fiyat: {gecerli_fiyatlar.max():.2f} TL")

    print("\n=== AYNI ÜRÜNÜ SATAN FARKLI SATICILAR ===")

    df["Temiz Ürün Adı"] = df["Ürün Adı"].str.lower()
    ayni_urunler = df[df.duplicated(subset=["Temiz Ürün Adı"], keep=False)]

    if not ayni_urunler.empty:
        for isim, grup in ayni_urunler.groupby("Temiz Ürün Adı"):
            if len(grup) > 1:  # Birden fazla satıcı varsa
                print(f"\nÜrün: {grup.iloc[0]['Ürün Adı']}")
                for _, satir in grup.iterrows():
                    print(
                        f"  Satıcı: {satir.get('Satıcı', 'Bilinmeyen')} - Fiyat: {satir.get('Güncel Fiyat', satir.get('Fiyat', 'Bilinmeyen'))} - Değerlendirme: {satir.get('Ürün Puanı', satir.get('Değerlendirme', 'Bilinmeyen'))}")
    else:
        print("Aynı ürünü satan farklı satıcı bulunamadı.")

    print("\n=== ÜRÜNLERİN TEKNİK ÖZELLİKLERİNE GÖRE KARŞILAŞTIRMASI ===")

    ozellik_sutunlari = [sutun for sutun in df.columns if sutun.startswith("Özellik:")]

    if ozellik_sutunlari:
        yaygin_ozellikler = {}
        for sutun in ozellik_sutunlari:
            dolu_sayisi = df[sutun].notna().sum()
            if dolu_sayisi > 0:
                yaygin_ozellikler[sutun] = dolu_sayisi

        if yaygin_ozellikler:
            en_yaygin = sorted(yaygin_ozellikler.items(), key=lambda x: x[1], reverse=True)[:5]

            for ozellik_adi, sayi in en_yaygin:
                print(f"\n{ozellik_adi.replace('Özellik: ', '')} özelliğine göre ürünler:")
                degerler = df[df[ozellik_adi].notna()][ozellik_adi].value_counts()

                sayac = 0
                for deger, adet in degerler.items():
                    print(f"  {deger}: {adet} ürün")
                    sayac += 1
                    if sayac >= 5:
                        break
        else:
            print("Karşılaştırılabilir teknik özellik bulunamadı.")
    else:
        print("Teknik özellik bilgisi bulunamadı.")

def main():
    print("Trendyol Ürün Analiz Programı")
    print("-----------------------------")

    while True:
        print("\nYapmak istediğiniz işlemi seçin:")
        print("1. Kategoriden ürün listesi topla")
        print("2. Mevcut ürün listesinden detaylı bilgi topla")
        print("3. Detaylı ürün analizini görüntüle")
        print("4. Çıkış")

        secim = input("\nSeçiminiz (1-4): ")

        if secim == "1":
            url = input(
                "Trendyol kategori URL'sini girin (varsayılan: https://www.trendyol.com/sr?wc=106084,103108,103665): ")
            if not url:
                url = "https://www.trendyol.com/sr?wc=106084,103108,103665"

            sayfa_limiti = input("Kaç sayfa taranacak? (varsayılan: 3): ")
            if not sayfa_limiti.isdigit():
                sayfa_limiti = 3
            else:
                sayfa_limiti = int(sayfa_limiti)

            tarayici = tarayici_baslat()
            try:
                print("Veri kazıma işlemi başlatılıyor...")
                urunler = urunleri_topla(tarayici, url, sayfa_limiti=sayfa_limiti)

                print(f"Toplam {len(urunler)} ürün toplandı.")

                if urunler:
                    verileri_kaydet(urunler, "trendyol_urunler.csv")
                else:
                    print("Ürün verisi bulunamadı!")
            finally:
                tarayici.quit()

        elif secim == "2":
            giris_dosyasi = input("Ürün listesi CSV dosyasının adını girin (varsayılan: trendyol_urunler.csv): ")
            if not giris_dosyasi:
                giris_dosyasi = "trendyol_urunler.csv"

            cikis_dosyasi = input(
                "Detaylı ürün bilgilerinin kaydedileceği CSV dosyasının adını girin (varsayılan: trendyol_detayli_urunler.csv): ")
            if not cikis_dosyasi:
                cikis_dosyasi = "trendyol_detayli_urunler.csv"

            print("Detaylı ürün bilgileri toplanıyor...")
            tum_urun_detaylarini_cek(giris_dosyasi, cikis_dosyasi)

        elif secim == "3":
            dosya_adi = input("Analiz edilecek CSV dosyasının adını girin (varsayılan: trendyol_detayli_urunler.csv): ")
            if not dosya_adi:
                dosya_adi = "trendyol_detayli_urunler.csv"

            verileri_analiz_et(dosya_adi)

        elif secim == "4":
            print("Program sonlandırılıyor...")
            break

        else:
            print("Geçersiz seçim! Lütfen 1-4 arasında bir değer girin.")

if __name__ == "__main__":
    main()