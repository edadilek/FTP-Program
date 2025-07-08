from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os
import csv

# FTPHandler sınıfını genişletelim
class MyFTPHandler(FTPHandler):
    def ftp_SITE_ADDUSER(self, line):
        # Admin kontrolü yapıyorum ki bu işlemi sadece admin yapabilsin 
        if self.username != "admin":
            self.respond("550 İzin reddedildi. Bu işlem için admin yetkisi gerekiyor.")
            return
            
        # Parametreleri ayırıyorum
        args = line.split()
        if len(args) < 2:
            self.respond("501 Yetersiz parametre. Kullanım: SITE ADDUSER username password [permissions]")
            return
            
        username = args[0]
        password = args[1]
        permissions = args[2] if len(args) > 2 else "elr"
        
        # Sunucu uygulamasına erişim sağlıyoruz 
        server_app = self.server.server_app
        server_app.add_user(username, password, permissions)
        
        self.respond(f"200 Kullanıcı eklendi: {username}")
        
    def ftp_SITE_DELUSER(self, line):
        # Admin kontrolü yapıyoruz
        if self.username != "admin":
            self.respond("550 İzin reddedildi. Bu işlem için admin yetkisi gerekiyor.")
            return
            
        # Parametreleri ayırıyoruz
        username = line.strip()
        if not username:
            self.respond("501 Yetersiz parametre. Kullanım: SITE DELUSER username")
            return
            
        # Sunucu uygulamasına erişim yapıyoruz silmek için
        server_app = self.server.server_app
        server_app.remove_user(username)
        
        self.respond(f"200 Kullanıcı silindi: {username}")

class FTPServerApp:
    def __init__(self, host="127.0.0.1", port=2121, root_dir="./ftp_files"):
        self.host = host
        self.port = port
        self.root_dir = root_dir
        self.users_file = "ftp_users.csv"
        self.authorizer = DummyAuthorizer()
        
        # Kullanıcı dosyasını kontrol ediyoruz sunucu başladığında
        self._check_user_file()
        
        # Ana dizini oluştur
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
    
    def _check_user_file(self):
        """Kullanıcı dosyasını kontrol ediyoruz yoksa oluşturuyoruz"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password", "permissions"])
                # Varsayılan admin kullanıcısı ekledim tüm yetkilere sahip
                writer.writerow(["admin", "admin123", "elradfmwMT"])
    
    def load_users(self):
        """CSV dosyasından kullanıcıları yüklüyoruz burda"""
        with open(self.users_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Başlık satırını atladık
            for row in reader:
                if len(row) >= 3:
                    username, password, perm = row
                    user_dir = os.path.join(self.root_dir, username)
                    
                    # Kullanıcı dizini oluşturmak için
                    if not os.path.exists(user_dir):
                        os.makedirs(user_dir)
                    
                    # Kullanıcıyı authorizer'a eklemek için
                    self.authorizer.add_user(username, password, user_dir, perm=perm)
    
    def add_user(self, username, password, permissions="elr"):
        """Yeni kullanıcı ekleyip CSV dosyasına kaydediyoruz"""
        # CSV dosyasına kullanıcıyı ekleme kısmı
        with open(self.users_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, password, permissions])
        
        # Kullanıcı dizini oluşturma kısmı
        user_dir = os.path.join(self.root_dir, username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        # Kullanıcıyı authorizer'a ekleme kısmıe
        self.authorizer.add_user(username, password, user_dir, perm=permissions)
        print(f"Kullanıcı eklendi: {username}")
    
    def remove_user(self, username):
        """Kullanıcıyı siler"""
        # CSV'den kullanıcıyı kaldırıyoruzz
        users = []
        with open(self.users_file, 'r') as file:
            reader = csv.reader(file)
            users.append(next(reader))  # Başlık satırını ekle
            for row in reader:
                if row[0] != username:
                    users.append(row)
        
        with open(self.users_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(users)
        
        # Authorizer'dan kullanıcıyı kaldırmak için
        try:
            self.authorizer.remove_user(username)
            print(f"Kullanıcı silindi: {username}")
        except KeyError:
            print(f"Kullanıcı bulunamadı: {username}")

    def change_user_permissions(self, username, permissions):
        """Kullanıcının izinlerini günceller"""
        # CSV dosyasından kullanıcıları okuyup güncelliyoruz
        users = []
        user_updated = False
        
        with open(self.users_file, 'r') as file:
            reader = csv.reader(file)
            users.append(next(reader))  # Başlık satırını ekle
            for row in reader:
                if row[0] == username:
                    row[2] = permissions  # İzinleri güncelliyoruz
                    user_updated = True
                users.append(row)
        
        if not user_updated:
            print(f"Kullanıcı bulunamadı: {username}")
            return False
        
        # Güncellenen kullanıcıları CSV'ye yazıyoruz
        with open(self.users_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(users)
        
        # Eğer kullanıcı şu anda yüklenmişse, authorizer'dan kaldırıp yeniden ekle
        try:
            user_dir = os.path.join(self.root_dir, username)
            password = None
            
            # Kullanıcının şifresini bulmak için
            for row in users:
                if row[0] == username:
                    password = row[1]
                    break
            
            if password:
                # Varolan kullanıcıyı kaldırmak için
                try:
                    self.authorizer.remove_user(username)
                except KeyError:
                    pass  # Kullanıcı henüz yüklenmemiş olabilir
                
                # Kullanıcıyı yeni izinlerle tekrar eklemek için
                self.authorizer.add_user(username, password, user_dir, perm=permissions)
                print(f"Kullanıcı izinleri güncellendi: {username} -> {permissions}")
                return True
        except Exception as e:
            print(f"İzin güncelleme hatası: {str(e)}")
        
        return False
    
    def start(self):
        """FTP sunucusunu başlatma"""
        # Kullanıcıları yüklemek için
        self.load_users()
        
        # Anonim erişimi devre dışı bırak
        # self.authorizer.add_anonymous(self.root_dir)
        
        # FTP handler ayarlama kısmı
        handler = MyFTPHandler  # Değişti: FTPHandler yerine kendi sınıfımı kullanıyorum
        handler.authorizer = self.authorizer
        
        # Karşılama mesajı
        handler.banner = "Hoş geldiniz - Python FTP Sunucusu hazır."
        
        # Sunucuyu başlat
        server = FTPServer((self.host, self.port), handler)
        server.server_app = self  # Handler'ın sunucu uygulamasına erişebilmesi için referans ekliyorum
        
        print(f"FTP sunucusu başlatıldı: {self.host}:{self.port}")
        print(f"Ana dizin: {self.root_dir}")
        print("Çıkmak için Ctrl+C tuşuna basın.")
        
        server.serve_forever()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FTP Server")
    parser.add_argument("--adduser", nargs=2, metavar=("USERNAME", "PASSWORD"), 
                        help="Add new user with specified username and password")
    parser.add_argument("--deluser", metavar="USERNAME", 
                        help="Remove user with specified username")
    parser.add_argument("--permissions", default="elr", 
                        help="User permissions (default: elr)")
    parser.add_argument("--start", action="store_true", 
                        help="Start the FTP server")
    parser.add_argument("--changeperms", nargs=2, metavar=("USERNAME", "PERMISSIONS"), 
                    help="Change permissions for the specified user")
    
    args = parser.parse_args()
    server = FTPServerApp()
    
    if args.adduser:
        username, password = args.adduser
        server.add_user(username, password, args.permissions)
        print(f"User added: {username}")
    
    elif args.deluser:
        server.remove_user(args.deluser)
    
    elif args.changeperms:
        username, permissions = args.changeperms
        if server.change_user_permissions(username, permissions):
            print(f"Permissions changed for user: {username} to {permissions}")
        else:
            print(f"Failed to change permissions for user: {username}")

    elif args.start:
        server.start()
    
    else:
        parser.print_help()