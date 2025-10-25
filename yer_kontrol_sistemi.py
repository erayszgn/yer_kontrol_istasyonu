import time
import threading
import cv2 as cv
import iha_simulator
import socket
import json
import numpy

class YerKontrolIstasyonu:
    def __init__(self, ip='127.0.0.1', telemetri_port=5001, video_port=5002):
        self.ip = ip
        self.telemetri_port = telemetri_port
        self.video_port = video_port
        self.telemetri_soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.telemetri_soket.bind((self.ip, self.telemetri_port))
        self.video_soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_soket.bind((self.ip, self.video_port))
        self.durdurma = threading.Event()
        self.pil = None

    def _telemetri_al(self):
        ilk_yazma = True
        while not self.durdurma.is_set():
            try:
                data, addr = self.telemetri_soket.recvfrom(1024)
                telemetri_str = data.decode('utf-8')
                telemetri_veri = json.loads(telemetri_str)

                if ilk_yazma:
                    print("--- YER KONTROL İSTASYONU ---")
                    print("Bağlantı Durumu: BAĞLANDI")
                    print("-----------------------------\n\n\n")
                    print("-----------------------------")
                    ilk_yazma = False

                print("\033[5F", end="")

                print(f"Konum (X,Y,Z):   {telemetri_veri['konum']['x']:.2f}, {telemetri_veri['konum']['y']:.2f}, {telemetri_veri['konum']['z']:.2f}\033[K")
                print(f"İrtifa:          {telemetri_veri['irtifa']:.2f} m\033[K")
                print(f"Hız:             {telemetri_veri['hiz']:.2f} m/s\033[K")
                print(f"Pil Durumu:      %{telemetri_veri['pil']}\033[K")
                self.pil = telemetri_veri['pil']

                print("\033[1E", end="")

            except Exception as e:
                print(f"Telemetri verisi alınırken hata meydana geldi: {e}")
                break

        self.telemetri_soket.close()

    def _video_al(self):
        while not self.durdurma.is_set():
            try:
                data, addr = self.video_soket.recvfrom(65535)
                numpy_dizi = numpy.frombuffer(data, dtype=numpy.uint8)
                capture = cv.imdecode(numpy_dizi, cv.IMREAD_COLOR)

                if capture is not None:
                    cv.imshow("Sanal IHA", capture)

                if cv.waitKey(1) & 0xFF == ord('q') or self.pil == 0:
                    self.durdurma.set()
                    break

            except Exception as e:
                print(f"Video görüntüsü alınırken hata meydana geldi: {e}")
                break

        cv.destroyAllWindows()
        self.video_soket.close()

    def baslat(self):
        thread1 = threading.Thread(target=self._telemetri_al)
        thread2 = threading.Thread(target=self._video_al)
        thread1.start()
        thread2.start()
        
        try:
            while not self.durdurma.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.durdurma.set()

        thread1.join()
        thread2.join()

if __name__ == "__main__":
    yerKontrolIstasyonu = YerKontrolIstasyonu()
    yerKontrolIstasyonu.baslat()