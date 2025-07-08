import os
import ftplib
import sys
import getpass
from datetime import datetime
import colorama
from colorama import Fore, Style

# Renkli konsol çıktısı için colorama kullandım bu sayede terminalde renkli görüyoruz
colorama.init()

class FTPClient:
    def __init__(self):
        self.connection = None
        self.host = None
        self.port = None
        self.username = None
        self.connected = False
        self.current_local_dir = os.getcwd()
    
    def connect(self, host="127.0.0.1", port=2121):
        """FTP sunucusuna bağlanma kısmıı"""
        try:
            self.host = host
            self.port = port
            self.connection = ftplib.FTP()
            self.connection.connect(host, port)
            print(f"{Fore.GREEN}Sunucuya bağlanıldı: {host}:{port}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Bağlantı hatası: {str(e)}{Style.RESET_ALL}")
            return False
    
    def login(self, username, password):
        """Kullanıcı girişi yapıyor"""
        try:
            self.connection.login(username, password)
            self.username = username
            self.connected = True
            print(f"{Fore.GREEN}Giriş başarılı! Hoş geldiniz, {username}.{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Giriş hatası: {str(e)}{Style.RESET_ALL}")
            return False
    
    def disconnect(self):
        """Sunucudan bağlantıyı kesme kısmı"""
        if self.connection:
            try:
                self.connection.quit()
                self.connected = False
                print(f"{Fore.YELLOW}Sunucu bağlantısı kesildi.{Style.RESET_ALL}")
            except:
                self.connection.close()
                self.connected = False
                print(f"{Fore.YELLOW}Sunucu bağlantısı kapatıldı.{Style.RESET_ALL}")
    
    def list_remote_files(self):
        """Uzak dizindeki dosyaları listelemek için"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            print(f"{Fore.CYAN}Uzak dizin içeriği: {self.connection.pwd()}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'İsim':<30} {'Boyut':<10} {'Tarih':<20}{Style.RESET_ALL}")
            print("-" * 60)
            
            # Dosya listesini al
            file_list = []
            self.connection.dir(lambda x: file_list.append(x))
            
            for line in file_list:
                print(line)
        except Exception as e:
            print(f"{Fore.RED}Listeleme hatası: {str(e)}{Style.RESET_ALL}")
    
    def list_local_files(self):
        """Yerel dizindeki dosyaları listelemek için"""
        try:
            print(f"{Fore.CYAN}Yerel dizin içeriği: {self.current_local_dir}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'İsim':<30} {'Boyut':<10} {'Tarih':<20}{Style.RESET_ALL}")
            print("-" * 60)
            
            for item in os.listdir(self.current_local_dir):
                item_path = os.path.join(self.current_local_dir, item)
                stats = os.stat(item_path)
                size = stats.st_size
                modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                if os.path.isdir(item_path):
                    print(f"{Fore.BLUE}{'[DIR] ' + item:<30} {size:<10} {modified:<20}{Style.RESET_ALL}")
                else:
                    print(f"{item:<30} {size:<10} {modified:<20}")
        except Exception as e:
            print(f"{Fore.RED}Yerel listeleme hatası: {str(e)}{Style.RESET_ALL}")
    
    def change_remote_dir(self, path):
        """Uzak dizini değiştirmek için"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            self.connection.cwd(path)
            print(f"{Fore.GREEN}Uzak dizin değiştirildi: {self.connection.pwd()}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Dizin değiştirme hatası: {str(e)}{Style.RESET_ALL}")
    
    def change_local_dir(self, path):
        """Yerel dizini değiştirmek için"""
        try:
            if path == "..":
                path = os.path.dirname(self.current_local_dir)
            elif not os.path.isabs(path):
                path = os.path.join(self.current_local_dir, path)
            
            os.chdir(path)
            self.current_local_dir = os.getcwd()
            print(f"{Fore.GREEN}Yerel dizin değiştirildi: {self.current_local_dir}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Yerel dizin değiştirme hatası: {str(e)}{Style.RESET_ALL}")
    
    def upload_file(self, local_file, remote_file=None):
        """Dosya yüklemek için"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        if not remote_file:
            remote_file = os.path.basename(local_file)
        
        try:
            local_path = os.path.join(self.current_local_dir, local_file)
            
            if not os.path.exists(local_path):
                print(f"{Fore.RED}Yerel dosya bulunamadı: {local_path}{Style.RESET_ALL}")
                return
            
            with open(local_path, 'rb') as file:
                print(f"{Fore.YELLOW}Yükleniyor: {local_file} -> {remote_file}{Style.RESET_ALL}")
                self.connection.storbinary(f'STOR {remote_file}', file)
                print(f"{Fore.GREEN}Dosya başarıyla yüklendi!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Yükleme hatası: {str(e)}{Style.RESET_ALL}")
    
    def download_file(self, remote_file, local_file=None):
        """Dosya indirmek için"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        if not local_file:
            local_file = os.path.basename(remote_file)
        
        try:
            local_path = os.path.join(self.current_local_dir, local_file)
            
            print(f"{Fore.YELLOW}İndiriliyor: {remote_file} -> {local_path}{Style.RESET_ALL}")
            with open(local_path, 'wb') as file:
                self.connection.retrbinary(f'RETR {remote_file}', file.write)
                print(f"{Fore.GREEN}Dosya başarıyla indirildi!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}İndirme hatası: {str(e)}{Style.RESET_ALL}")
            # Hata durumunda oluşturulan eksik dosyayı sil
            if os.path.exists(local_path):
                os.remove(local_path)
    
    def create_remote_dir(self, dirname):
        """Uzak dizinde klasör oluşturmak için"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            self.connection.mkd(dirname)
            print(f"{Fore.GREEN}Uzak dizin oluşturuldu: {dirname}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Dizin oluşturma hatası: {str(e)}{Style.RESET_ALL}")
    
    def create_local_dir(self, dirname):
        """Yerel dizinde klasör oluşturma kısmı"""
        try:
            path = os.path.join(self.current_local_dir, dirname)
            os.makedirs(path, exist_ok=True)
            print(f"{Fore.GREEN}Yerel dizin oluşturuldu: {dirname}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Yerel dizin oluşturma hatası: {str(e)}{Style.RESET_ALL}")
    
    def delete_remote_file(self, filename):
        """Uzak dizindeki dosyayı silme kısmı"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            self.connection.delete(filename)
            print(f"{Fore.GREEN}Uzak dosya silindi: {filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Dosya silme hatası: {str(e)}{Style.RESET_ALL}")
    
    def delete_remote_dir(self, dirname):
        """Uzak dizindeki klasörü silme kısmı"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            self.connection.rmd(dirname)
            print(f"{Fore.GREEN}Uzak dizin silindi: {dirname}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Dizin silme hatası: {str(e)}{Style.RESET_ALL}")
    
    def rename_remote_file(self, old_name, new_name):
        """Uzak dizindeki dosya veya klasörün adını değiştirir"""
        if not self.connected:
            print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
            return
        
        try:
            self.connection.rename(old_name, new_name)
            print(f"{Fore.GREEN}Dosya/Dizin adı değiştirildi: {old_name} -> {new_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Yeniden adlandırma hatası: {str(e)}{Style.RESET_ALL}")

def print_menu():
    """Ana menü"""
    print(f"\n{Fore.CYAN}===== FTP Menüsü ====={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Sunucuya Bağlan")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Giriş Yap")
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Uzak Dosyaları Listele")
    print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Yerel Dosyaları Listele")
    print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Uzak Dizin Değiştir")
    print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Yerel Dizin Değiştir")
    print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Dosya Yükle")
    print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Dosya İndir")
    print(f"{Fore.YELLOW}9.{Style.RESET_ALL} Uzak Dizin Oluştur")
    print(f"{Fore.YELLOW}10.{Style.RESET_ALL} Yerel Dizin Oluştur")
    print(f"{Fore.YELLOW}11.{Style.RESET_ALL} Uzak Dosya Sil")
    print(f"{Fore.YELLOW}12.{Style.RESET_ALL} Uzak Dizin Sil")
    print(f"{Fore.YELLOW}13.{Style.RESET_ALL} Dosya/Dizin Adı Değiştir")
    print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Çıkış")
    print(f"{Fore.CYAN}============================{Style.RESET_ALL}")

def main():
    """Ana program döngüsü"""
    client = FTPClient()
    
    while True:
        print_menu()
        choice = input(f"{Fore.GREEN}Seçiminiz (0-13): {Style.RESET_ALL}")
        
        if choice == "0":
            if client.connected:
                client.disconnect()
            print(f"{Fore.YELLOW}Program sonlandırılıyor...{Style.RESET_ALL}")
            sys.exit(0)
        
        elif choice == "1":
            host = input("Sunucu adresi [127.0.0.1]: ") or "127.0.0.1"
            port = input("Port [2121]: ") or "2121"
            client.connect(host, int(port))
        
        elif choice == "2":
            if not client.connection:
                print(f"{Fore.RED}Önce sunucuya bağlanın.{Style.RESET_ALL}")
                continue
                
            username = input("Kullanıcı adı: ")
            password = getpass.getpass("Şifre: ")
            client.login(username, password)
        
        elif choice == "3":
            client.list_remote_files()
        
        elif choice == "4":
            client.list_local_files()
        
        elif choice == "5":
            path = input("Uzak dizin yolu: ")
            client.change_remote_dir(path)
        
        elif choice == "6":
            path = input("Yerel dizin yolu: ")
            client.change_local_dir(path)
        
        elif choice == "7":
            local_file = input("Yüklenecek yerel dosya: ")
            remote_file = input("Uzak dosya adı [aynı ad]: ") or None
            client.upload_file(local_file, remote_file)
        
        elif choice == "8":
            remote_file = input("İndirilecek uzak dosya: ")
            local_file = input("Yerel dosya adı [aynı ad]: ") or None
            client.download_file(remote_file, local_file)
        
        elif choice == "9":
            dirname = input("Oluşturulacak uzak dizin adı: ")
            client.create_remote_dir(dirname)
        
        elif choice == "10":
            dirname = input("Oluşturulacak yerel dizin adı: ")
            client.create_local_dir(dirname)
        
        elif choice == "11":
            filename = input("Silinecek uzak dosya adı: ")
            client.delete_remote_file(filename)
        
        elif choice == "12":
            dirname = input("Silinecek uzak dizin adı: ")
            client.delete_remote_dir(dirname)
        
        elif choice == "13":
            old_name = input("Eski dosya/dizin adı: ")
            new_name = input("Yeni dosya/dizin adı: ")
            client.rename_remote_file(old_name, new_name)
        
        else:
            print(f"{Fore.RED}Geçersiz seçim. Tekrar deneyin.{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Devam etmek için Enter tuşuna basın...{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program sonlandırılıyor...{Style.RESET_ALL}")
        sys.exit(0)