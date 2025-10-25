import threading
import time
import json
import socket
import random
import cv2 as cv
import keyboard

HOST_IP = '127.0.0.1'
TELEMETRI_PORT = 5001
VIDEO_PORT = 5002

class IHASimulator:
    def __init__(self):
        self.past = time.time()
        self.pil = 100
        self.konum = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.irtifa = self.konum['z']
        self.hiz = 0
        self.ip = HOST_IP
        self.telemetri_soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.telemetri_hedef = (self.ip, TELEMETRI_PORT)
        self.video_hedef = (self.ip, VIDEO_PORT)
        self.kamera = cv.VideoCapture(0)
        self.durdurma = threading.Event()
        
    def _telemetri_guncelleme(self):
        if self.pil <= 10: # Eğer pilin %10'dan az şarjı kaldıysa irtifayı ve İHA'nın hızını sıfırlıyorum.
            if self.konum['z'] < 1:
                self.konum['z'] = 0
            else:
                self.konum['z'] -= 0.5

            if self.hiz > 0.5:
                self.hiz -= 0.5
            else:
                self.hiz = 0

        elif self.konum['z'] <= 1.5: #İrtifa negatif olamayacağı için irtifanın her zaman pozitif kalmasını sağlıyorum.
            self.konum['z'] += 1.0

            if self.hiz >= 10:
                self.hiz -= 2.0
            else:
                self.hiz += random.uniform(-1.5, 1.5)

        else:
            self.konum['z'] += random.uniform(-1.0, 1.0)

            if self.hiz >= 40:
                self.hiz -= 2.0
            else:
                self.hiz += random.uniform(-1.5, 1.5)
        
        self.konum['x'] += random.uniform(-1.0, 1.0)
        self.konum['y'] += random.uniform(-1.0, 1.0)
        self.irtifa = self.konum['z']

        present = time.time() #Her saniye pilin şarjını 1 azaltıyorum.
        if present - self.past >= 1:
            if self.pil > 0:
                self.pil -= 1
                self.past = present

        gonderilecek_veri = {"konum": self.konum, "irtifa": self.irtifa, "hiz": self.hiz, "pil": self.pil}
        return gonderilecek_veri
    
    def _telemetri_gonderme(self):
        while not self.durdurma.is_set():
            gonderilecek_veri = self._telemetri_guncelleme()
            gonderilecek_veri = json.dumps(gonderilecek_veri).encode('utf-8') #Telemetri verisini json formatına çeviriyorum.
            self.telemetri_soket.sendto(gonderilecek_veri, self.telemetri_hedef)
            time.sleep(0.1)

        self.telemetri_soket.close()

    def _video_gonderme(self):
        while not self.durdurma.is_set():
            isTrue, capture = self.kamera.read()

            if not isTrue:
                continue

            #Görüntü ağ üzerinden gönderilecek bir formata dönüştürüyorum ve sıkıştırıyorum.
            _, buffer = cv.imencode('.jpg', capture, [cv.IMWRITE_JPEG_QUALITY, 80]) 
            veri_bytes = buffer.tobytes()
            self.video_soket.sendto(veri_bytes, self.video_hedef)

        self.video_soket.close()
        self.kamera.release()

    def baslat(self):
        thread1 = threading.Thread(target=self._telemetri_gonderme)
        thread2 = threading.Thread(target=self._video_gonderme)

        thread1.start()
        thread2.start()

        while True:
            if keyboard.is_pressed('q') or self.pil == 0:
                self.durdurma.set()
                break
            time.sleep(0.1)
        
        thread1.join()
        thread2.join()

if __name__ == "__main__":
    iha_simulator = IHASimulator()
    iha_simulator.baslat()