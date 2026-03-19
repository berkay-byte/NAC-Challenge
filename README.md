🚀 Teknolojiler ve Versiyonlar

Sistem, belgedeki teknik gereksinimlere  uygun olarak şu stack ile kurgulanmıştır:

RADIUS Sunucusu: FreeRADIUS 3.2 

Policy Engine: Python 3.13 & FastAPI 

Veritabanı: PostgreSQL 18 (Alpine) 

Cache & Rate Limiting: Redis 8 (Alpine) 

Orkestrasyon: Docker Compose 

🏗️ Mimari Tasarım

Proje, mikroservis mimarisi üzerine kuruludur. FreeRADIUS, gelen istekleri rlm_rest modülü aracılığıyla FastAPI Policy Engine'e iletir. Policy Engine, PostgreSQL üzerindeki kullanıcı ve grup verilerini kontrol ederek erişim kararını verir ve aktif oturumları Redis üzerinde takip eder.

🛠️ Kurulum ve Çalıştırma

Sistemin çalışması için Docker ve Docker Compose yüklü olmalıdır.
Bash

    Depoyu Klonlayın: git clone https://github.com/berkay-byte/NAC-Challenge
    cd NAC-Challenge


Environment Ayarları:

.env.example dosyasını .env olarak kopyalayın ve şifreleri düzenleyin.
Bash

    cp .env.example .env

Sistemi Başlatın:
Tüm servisler healthcheck kontrolleriyle birlikte otomatik olarak ayağa kalkacaktır.

Bash

    docker compose up -d --build

## 🧪 Test Senaryoları

Sistemi test etmeden önce veritabanına geçerli bir bcrypt şifresiyle (şifre: `KENDİ_SİFRENİZ`) örnek bir kullanıcı eklememiz gerekmektedir.
KOD KISMINDAN 'KENDİ_SİFRENİZ' bölümünü güncelleyiniz.

### 0. Test Kullanıcısını Oluşturma
FastAPI konteyneri üzerinden veritabanına gerçek bir bcrypt şifresi eklemek için şu komutu çalıştırın:
Bash
    
    docker exec -it nac_api python -c "
    import bcrypt
    from database import engine
    from sqlalchemy.orm import sessionmaker
    from models import RadCheck

    db = sessionmaker(bind=engine)()
    hash_pw = bcrypt.hashpw(b'KENDİ_SİFRENİZ', bcrypt.gensalt()).decode()
    user = db.query(RadCheck).filter(RadCheck.username=='test_user').first()

    if not user:
        db.add(RadCheck(username='test_user', attribute='Password', op=':=', value=hash_pw))
    else:
        user.value = hash_pw
    db.commit()
    print('✅ Test kullanicisi (test_user) basariyla eklendi/guncellendi!')
    "

1. PAP Authentication (Şifre Tabanlı)
Bash

       echo "User-Name=test_user, User-Password=s3m_pass_123" | \
       docker exec -i nac_radius radclient -x localhost:1812 auth s3m_test_secret_key

(Başarılı olduğunda Access-Accept yanıtı dönecektir.)

2. MAB Authentication (MAC Tabanlı)
Mac Adresini Veritabanına Ekleme
Bash

       docker exec -it nac_db psql -U s3m_admin -d nacdb -c "INSERT INTO radcheck (username, attribute, op, value) VALUES ('AA:BB:CC:DD:EE:FF', 'Auth-Type', ':=', 'Accept');"
Bash

       echo "User-Name=AA:BB:CC:DD:EE:FF, Calling-Station-Id=AA:BB:CC:DD:EE:FF" | \
       docker exec -i nac_radius radclient -x localhost:1812 auth s3m_test_secret_key

4. Accounting (Kayıt Takibi)
Bash

# Oturum Başlatma
    echo "User-Name=test_user, Acct-Status-Type=Start, Acct-Session-Id=S3M-123" | \
    docker exec -i nac_radius radclient -x localhost:1813 acct s3m_test_secret_key
Aktif Oturumu Veritabanında Gör

Bash

    docker exec -it nac_db psql -U s3m_admin -d nacdb -c "SELECT username, acctsessionid, acctstarttime, acctstoptime FROM radacct;"

2. Oturumu Kapat (Stop Paketi Gönder)
   
Bash

    echo "User-Name=test_user, Acct-Status-Type=Stop, Acct-Session-Id=S3M-123, Acct-Session-Time=3600" | \
    docker exec -i nac_radius radclient -x localhost:1813 acct s3m_test_secret_key

(Bu komuttan da Accounting-Response almalısın).
3. Oturumun Kapandığını ve Süreyi Doğrula

Son olarak veritabanına tekrar bakıyoruz. API'miz, gelen Stop paketini aldı ve o boş olan çıkış saatini ve içeride kalınan süreyi tabloya işledi:
Bash

    docker exec -it nac_db psql -U s3m_admin -d nacdb -c "SELECT username, acctstarttim


📂 Özellikler

Bcrypt Hashing: Kullanıcı şifreleri PostgreSQL'de düz metin olarak değil, güvenli hashlenmiş olarak saklanır.

Dinamik Yetkilendirme: Kullanıcı grubuna göre (Admin, Employee, Guest) dinamik VLAN atamaları (Tunnel-Private-Group-Id) yapılır.

Session Management: Aktif oturumlar Redis üzerinde cache'lenerek anlık olarak sorgulanabilir.

Rate-Limiting: Başarısız giriş denemeleri Redis üzerinden takip edilerek brute-force saldırılarına karşı koruma sağlanır.

💡 Geliştirici Notu

Bu NAC sistemi, hem kurumsal ağlarda cihaz segmentasyonu hem de IoT ortamlarında MAC tabanlı erişim kontrolü senaryoları düşünülerek optimize edilmiştir.
