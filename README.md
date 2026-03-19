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

🧪 Test Senaryoları

Sistemin AAA bileşenleri şu komutlarla doğrulanabilir:

1. Kimlik Doğrulama (PAP/MAB)

PAP Testi:
    Bash 

    radtest test_user s3m_pass_123 localhost 0 testing123

MAB Testi:
Bash

    echo "User-Name=AA:BB:CC:DD:EE:FF, Calling-Station-Id=AA:BB:CC:DD:EE:FF" | \
    docker exec -i nac_radius radclient -x localhost:1812 auth testing123

2. Hesap Yönetimi (Accounting)

    Oturum Başlatma (Start):
    Bash

       echo "User-Name=test_user, Acct-Status-Type=Start, Acct-Session-Id=S3M-123" | \
       docker exec -i nac_radius radclient -x localhost:1813 acct testing123

Oturum Bitirme (Stop):
Bash

    echo "User-Name=test_user, Acct-Status-Type=Stop, Acct-Session-Id=S3M-123, Acct-Session-Time=60" | \
    docker exec -i nac_radius radclient -x localhost:1813 acct testing123

📂 Özellikler

Bcrypt Hashing: Kullanıcı şifreleri PostgreSQL'de düz metin olarak değil, güvenli hashlenmiş olarak saklanır.

Dinamik Yetkilendirme: Kullanıcı grubuna göre (Admin, Employee, Guest) dinamik VLAN atamaları (Tunnel-Private-Group-Id) yapılır.

Session Management: Aktif oturumlar Redis üzerinde cache'lenerek anlık olarak sorgulanabilir.

Rate-Limiting: Başarısız giriş denemeleri Redis üzerinden takip edilerek brute-force saldırılarına karşı koruma sağlanır.

💡 Geliştirici Notu

Bu NAC sistemi, hem kurumsal ağlarda cihaz segmentasyonu hem de IoT ortamlarında MAC tabanlı erişim kontrolü senaryoları düşünülerek optimize edilmiştir.
