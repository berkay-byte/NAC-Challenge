# api/seed.py

from database import SessionLocal
from models import RadCheck, RadUserGroup, RadGroupReply
import bcrypt

db = SessionLocal()

def seed_data():
    # 1. Test Kullanıcısı Ekleme
    test_user = "berkay_test"
    test_password = "password123"
    
    # Doğrudan bcrypt ile hashliyoruz (utf-8 byte'a çevirerek)
    hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    if not db.query(RadCheck).filter(RadCheck.username == test_user).first():
        new_user = RadCheck(username=test_user, attribute="Crypt-Password", op=":=", value=hashed_password)
        db.add(new_user)
        print(f"Kullanıcı eklendi: {test_user}")

    # 2. Kullanıcıyı Gruba Atama
    group_name = "employee"
    if not db.query(RadUserGroup).filter(RadUserGroup.username == test_user).first():
        new_group = RadUserGroup(username=test_user, groupname=group_name, priority=1)
        db.add(new_group)
        print(f"Kullanıcı '{group_name}' grubuna atandı.")

    # 3. Gruba VLAN (Policy) Atama
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == group_name).first():
        vlan_reply = RadGroupReply(groupname=group_name, attribute="Tunnel-Private-Group-Id", op="=", value="20")
        type_reply = RadGroupReply(groupname=group_name, attribute="Tunnel-Type", op="=", value="VLAN")
        db.add(vlan_reply)
        db.add(type_reply)
        print(f"'{group_name}' grubuna VLAN 20 politikası tanımlandı.")

    db.commit()
    db.close()
    print("Test verileri başarıyla oluşturuldu!")

if __name__ == "__main__":
    seed_data()
    