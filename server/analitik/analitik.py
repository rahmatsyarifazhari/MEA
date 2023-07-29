# import the necessary packages
from datetime import datetime, timedelta
from threading import Thread
import time
import cv2
import numpy as np

from collections import deque
configPath = "model/yolov4_cpp.cfg"
weightsPath = "model/yolov4_cpp_last.weights"
dataset = "model/obj_cpp.names"
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class WebStreaming:

    def __init__(self, stream, socketio, deque_size = 1):
        #  init analitik
        # init cv to set weights and config also cuda
        self.net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
        try:
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            print("[INFO set to cuda]")
        except:
            print("[INFO set to CPU] Failed to using GPU")
        self.ln = self.net.getLayerNames()
        self.ln = [self.ln[i - 1]
                   for i in self.net.getUnconnectedOutLayers()]
        self.LABELS = open(dataset).read().strip().split("\n")
        print(self.LABELS)

        self.MIN_CONF = 0.00001
        self.NMS_THRESH = 0.001  
        self.dumping_area = [(319,397), (319, 502), (461, 502), (461, 397)]
        self.safeArea_person = [(156,384), (156, 526), (283, 526), (283, 384)]

        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)
        self.camera_stream_link = stream
        self.socket = socketio

        # Flag to check if camera is valid/working
        self.online = False
        self.capture = None
        self.video_frame = None
        self.exit = False

        self.load_network_stream()
        
        # Start background frame grabbing
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

        print('Started camera: {}'.format(self.camera_stream_link))

    def load_network_stream(self):
        """Verifies stream link and open new stream if valid"""
        
        def load_network_stream_thread():
            if self.verify_network_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
                print('loaded:', self.camera_stream_link)
        self.load_stream_thread = Thread(target=load_network_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()
        self.load_stream_thread.join()
        print('thread loaded', self.camera_stream_link)

    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            return False
        cap.release()
        print("verify", self.camera_stream_link)
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""
        fpsLimit = 1
        prev = 0
        count = 0
        while True:
            try:
                # self.get_memory_usage()
                if self.exit:
                    break
                if self.capture is None or not self.capture.isOpened():
                    self.load_network_stream()
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    time_elapsed = time.time() - prev
                    status, frame = self.capture.read()
                    if status:
                        if time_elapsed > 1/fpsLimit:
                            prev = time.time()
                            self.deque.append(frame)
                            self.set_frame()
                            count+=int(self.capture.get(5)) # menambah variabel `count` dengan nilai properti `5`th dari objek VideoCapture `vs`. Properti ke-5 dari objek VideoCapture adalah nomor frame
                            print("frame ke " + str(count))
                            self.capture.set(cv2.CAP_PROP_POS_FRAMES, count) 
                            # self.video_frame = self.analitik(frame)
                    else:
                        self.capture.release()
                        self.online = False
                        print('status offline', self.camera_stream_link)
                else:
                    # Attempt to reconnect
                    print('attempting to reconnect', self.camera_stream_link)
                    self.load_network_stream()
                    self.spin(2)
                self.spin(.001)
            except AttributeError:
                # print('AttributeError', self.camera_stream_link)
                # print("ERROR GET FRAME")
                pass

    def spin(self, seconds):
        time.sleep(seconds)

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if not self.online:
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            try:
                frame = self.deque[-1]
                frame = cv2.resize(frame,(1280,720),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)

                self.frame = self.analitik(frame)
                # self.frame = frame

                # Add timestamp to cameras
                # cv2.rectangle(self.frame, (self.screen_width-190,0), (self.screen_width,50), color=(0,0,0), thickness=-1)
                # cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

                self.video_frame = self.frame
            except:
                print("ERROR SET FRAME")
                pass

    def get_video_frame(self):
        return self.video_frame

    
    def generate_frame(self):
        while True:
            try:
                frame = self.get_video_frame()
                (flag, encodedImage) = cv2.imencode(".jpg", frame)
            except:
                frame = np.zeros((720, 1280, 3), np.uint8)
                frame = cv2.putText(frame, "Camera Offline", (1050//2, 720//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                (flag, encodedImage) = cv2.imencode(".jpg", frame)
            finally:
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                            bytearray(encodedImage) + b'\r\n')
    
    def reload(self):
        import threading

        if self.capture is None or not self.capture.isOpened():
            self.capture.release()
            self.load_network_stream()

        time.sleep(2)
        # self.online = False
        
        print("start process thread get frame")
        try:
            self.exit = True
            time.sleep(5)
            self.get_frame_thread.join()
            self.exit = False
        except:
            print("error terminate thread")
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()
        print("end process thread get frame")

    def detect_person(self, frame, net, ln, Idx=0):
    	# grab the dimensions of the frame and  initialize the list of
        # results
        (H, W) = frame.shape[:2] # membuat variabel H dan W untuk mengambil dimensi baris dan kolom dari frame (menggunakan fungsi shape) sedangkan frame merupakan parameter dari model
        results = [] # menginisialisasi variabel hasil

        # construct a blob from the input frame and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes
        # and associated probabilities
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (480, 480), # menggunakan fungsi blobFromImage dari library OpenCV untuk membuat blob dari input bingkai, blob = piksel yang terhubung dalam citra biner.
            swapRB=True, crop=False) # Dalam hal ini, faktor skala diatur ke 1/255.0, ukuran blob diatur ke (480, 480), dan saluran R dan B ditukar.
        net.setInput(blob) # menyetel blob input ke jaringan detektor objek YOLO, jaringan YOLO mengambil blob sebagai input dan mengeluarkan satu set kotak pembatas dan probabilitas terkait
        layerOutputs = net.forward(ln) # melakukan penerusan jaringan detektor objek YOLO, Parameter ln menentukan lapisan dari mana kotak pembatas dan probabilitas harus diekstraksi

        # initialize our lists of detected bounding boxes, centroids, and
        # confidences, respectively
        boxes = [] # kotak pembatas
        centroids = [] # pusat geometri
        confidences = [] # nilai kepercayaan

        # loop over each of the layer outputs
        for output in layerOutputs: # looping dari keluaran lapisan
            # loop over each of the detections
            for detection in output: # looping dari keluaran
                # extract the class ID and confidence (i.e., probability)
                # of the current object detection
                scores = detection[5:] # mengekstrak skor daftar probabilitas setiap kelas. keluaran lapisan berisi 5 daftar nilai dari objek terdeteksi : ID kelas, Keyakinan/probabilitas, Koordinat x,  Koordinat y, Lebar kotak pembatas
                classID = np.argmax(scores) # fungsi np.argmax() untuk menemukan indeks kelas dengan probabilitas tertinggi, Indeks ini adalah ID kelas dari objek yang terdeteksi. mengekstrak keyakinan deteksi, yang merupakan probabilitas bahwa objek terdeteksi dengan benar.
                confidence = scores[classID] # mengembalikan ID kelas dan keyakinan deteksi.

                # filter detections by (1) ensuring that the object
                # detected was a person and (2) that the minimum
                # confidence is met
                if classID == Idx and confidence > self.MIN_CONF: # memastikan bahwa objek yang terdeteksi adalah orang dan keyakinan minimum terpenuhi
                    # scale the bounding box coordinates back relative to
                    # the size of the image, keeping in mind that YOLO
                    # actually returns the center (x, y)-coordinates of
                    # the bounding box followed by the boxes' width and
                    # height
                    box = detection[0:4] * np.array([W, H, W, H]) # mengalikan koordinat kotak pembatas dengan lebar dan tinggi gambar, fungsi np.array() untuk mengubah koordinat kotak pembatas menjadi larik NumPy. memastikan bahwa koordinat kotak pembatas diperkecil relatif terhadap ukuran gambar
                    (centerX, centerY, width, height) = box.astype("int") # menampilkan koordinat kotak pembatas yang diskalakan. astype() kemudian mengubah koordinat kotak pembatas menjadi bilangan bulat, diperlukan karena koordinat kotak pembatas digunakan untuk menggambar kotak pembatas pada gambar, dan Python hanya mendukung bilangan bulat untuk operasi menggambar

                    # use the center (x, y)-coordinates to derive the top
                    # and and left corner of the bounding box
                    x = int(centerX - (width / 2)) # mendapatkan sudut kiri kotak pembatas
                    y = int(centerY - (height / 2)) # mendapatkan sudut puncak kotak pembatas

                    # update our list of bounding box coordinates,
                    # centroids, and confidences
                    boxes.append([x, y, int(width), int(height)]) # memperbarui kotak pembatas dengan menambahkan (x,y) sudut puncak dan kiri pembatas
                    centroids.append((centerX, centerY)) # memperbarui pusat geomtris
                    confidences.append(float(confidence)) # memperbarui nilai kepercayaan

        # apply non-maxima suppression to suppress weak, overlapping
        # bounding boxes
        # non-maximum suppression (NMS) adalah teknik yang digunakan untuk menekan kotak pembatas yang tumpang tindih, hanya menyisakan kotak pembatas terkuat.
        # kode kemudian menggunakan indeks untuk memfilter kotak pembatas. Hanya kotak pembatas dengan indeks dalam daftar yang dipertahankan
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.MIN_CONF, self.NMS_THRESH)

        # ensure at least one detection exists
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # extract the bounding box coordinates
                (x, y) = (boxes[i][0], boxes[i][1]) # ekstrak koordinat x,y bounding box
                (w, h) = (boxes[i][2], boxes[i][3]) # ekstrak lebar,tinggi bounding box

                # update our results list to consist of the person
                # prediction probability, bounding box coordinates,
                # and the centroid
                r = (confidences[i], (x, y, x + w, y + h), centroids[i]) # Variabel r adalah tuple saat ini berisi nilai kepercayaan deteksi, koordinat kotak pembatas, dan pusat geometri
                results.append(r) # menambahkan r tuple ke daftar hasil.

        # return the list of results
        return results # mengeluarkan hasil
    
    def detect_dt(self, frame, net, ln, Idx=3):
    	# grab the dimensions of the frame and  initialize the list of
        # results
        (H, W) = frame.shape[:2]
        results = []

        # construct a blob from the input frame and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes
        # and associated probabilities
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (480, 480),
            swapRB=True, crop=False)
        net.setInput(blob)
        layerOutputs = net.forward(ln)

        # initialize our lists of detected bounding boxes, centroids, and
        # confidences, respectively
        boxes = []
        centroids = []
        confidences = []
        # right_bottom = []

        # loop over each of the layer outputs
        for output in layerOutputs:
            # loop over each of the detections
            for detection in output:
                # extract the class ID and confidence (i.e., probability)
                # of the current object detection
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                # filter detections by (1) ensuring that the object
                # detected was a person and (2) that the minimum
                # confidence is met
                if classID == Idx and confidence > self.MIN_CONF:
                    # scale the bounding box coordinates back relative to
                    # the size of the image, keeping in mind that YOLO
                    # actually returns the center (x, y)-coordinates of
                    # the bounding box followed by the boxes' width and
                    # height
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")

                    # use the center (x, y)-coordinates to derive the top
                    # and and left corner of the bounding box
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))

                    # coordinates of bottom right corner bounding box
                    x_ = x + width # mendapatkan sudut kanan kotak pembatas
                    y_ = y + height # mendapatkan sudut bawah kotak pembatas

                    # update our list of bounding box coordinates,
                    # centroids, and confidences
                    boxes.append([x, y, int(width), int(height)])
                    centroids.append((centerX, centerY))
                    confidences.append(float(confidence))
                    # right_bottom.append(x_, y_)

        # apply non-maxima suppression to suppress weak, overlapping
        # bounding boxes
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.MIN_CONF, self.NMS_THRESH)

        # ensure at least one detection exists
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # extract the bounding box coordinates
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                # update our results list to consist of the person
                # prediction probability, bounding box coordinates,
                # and the centroid
                r = (confidences[i], (x, y, x + w, y + h), centroids[i])
                results.append(r)

        # return the list of results
        return results
        
    def analitik(self, frame):
        # INITIALITATION -------------------------------------------------------------
        # resize the frame and then detect people (and only people) in it
        # frame = imutils.resize(frame, width=700)
        results_person = self.detect_person(frame, self.net, self.ln, Idx=self.LABELS.index("person")) # inisialisasi daftar kotak pembatas dan koordinat centroid untuk person yang terdeteksi di frame
        results_dt = self.detect_dt(frame, self.net, self.ln, Idx=self.LABELS.index("DT")) # inisialisasi daftar kotak pembatas dan koordinat centroid untuk HD yang terdeteksi di frame

        # DRAW POLYGON AND LINE ----------------------------------------------------------------------
        # Draw the high-risk area
        cv2.polylines(frame, [np.array(self.safeArea_person, dtype=np.int32)], True, (0, 255, 0), thickness=2) # Area pengawas hijau
        cv2.polylines(frame, [np.array(self.dumping_area, dtype=np.int32)], True, (0, 0, 255), thickness=2) # Area dumping merah

        # PERSON ANALITIK -----------------------------------------------------------------------
        count_person_no_risk_area = 0 # set variabel penghitung aman = 0
        count_person_risk_area = 0 # set variabel penghitung tidak aman = 0
        count_person_risk_dt = 0

        count_dt_risk_area = 0 # set variabel penghitung HD tidak ada resiko = 0
        count_dt_risk_person = 0

        for (j, (prob, bbox, centroid)) in enumerate(results_person): # looping melalui daftar hasil yang dikembalikan oleh fungsi `detect_person()`.
                # extract the bounding box and centroid coordinates, then
                # initialize the color of the annotation
            (startXp, startYp, endXp, endYp) = bbox # mengekstrak kotak pembatas
            (cX, cY) = centroid # mengekstrak koordinat sentroid
            color = (0, 255, 245) # kuning

            startXp = startXp-36
            startYp = startYp-36
            endXp = endXp+36
            endYp = endYp+36

            # Pengawas terhadap area pengawas
            if (endXp >= self.safeArea_person[0][0]) and (startYp <= self.safeArea_person[1][1]) and (endYp >= self.safeArea_person[0][1]) and (startXp <= self.safeArea_person[3][0]):
                count_person_no_risk_area += 1 # variabel berisiko bertambah satu
                color = (0, 255, 0) # warna kotak pembatas hijau
                # Pengawas ke area dumping
            elif (endXp >= self.dumping_area[0][0]) and (startYp <= self.dumping_area[1][1]) and (endYp >= self.dumping_area[0][1]) and (startXp <= self.dumping_area[3][0]):
                count_person_risk_area += 1 # variabel berisiko bertambah satu
                color = (0, 0, 255) # warna kotak pembatas merah

            cv2.rectangle(frame, (startXp, startYp), (endXp, endYp), color, 2) # menggambar kotak pembatas di sekitar orang dalam frame

            w, h = frame.shape[1],frame.shape[0] # mengambil lebar dan tinggi gambar bingkai. Nilai-nilai ini digunakan untuk menghitung koordinat kotak pembatas

            for (i, (prob, bbox, centroid)) in enumerate(results_dt):  # looping melalui daftar hasil yang dikembalikan oleh fungsi `detect_dt()`.
                (startXd, startYd, endXd, endYd) = bbox # mengekstrak kotak pembatas
                (cX, cY) = centroid # mengekstrak koordinat sentroid
                colordt = (0, 255, 245) # kuning

                startXd = startXd-72
                startYd = startYd-72
                endXd = endXd+72
                endYd = endYd+72

                # DT terhadap person (bergerak)
                if (endXd >= startXp) and (startXd <= endXp) and (startYd <= endYp) and (endYd >= startXp):
                    count_dt_risk_person += 1
                    count_person_risk_dt += 1
                    colordt = (0, 0, 255) # warna kotak pembatas merah
                    color = (0, 0, 255) # warna kotak pembatas merah

                cv2.rectangle(frame, (startXd, startYd), (endXd, endYd), colordt, 2) # menggambar kotak pembatas di sekitar dt dalam frame
                cv2.rectangle(frame, (startXp, startYp), (endXp, endYp), color, 2) # menggambar kotak pembatas di sekitar orang dalam frame

        # DT ANALITIK ----------------------------------------------------------------------------
        for (i, (prob, bbox, centroid)) in enumerate(results_dt):  # looping melalui daftar hasil yang dikembalikan oleh fungsi `detect_dt()`.
            (startXd, startYd, endXd, endYd) = bbox # mengekstrak kotak pembatas
            (cX, cY) = centroid # mengekstrak koordinat sentroid
            color = (0, 255, 245) # kuning

            # DT terhadap area dumping dan area person
            if (endXd >= self.dumping_area[0][0]) and (startYd <= self.dumping_area[1][1]) and (endYd >= self.dumping_area[0][1]) and (startXd <= self.dumping_area[3][0]):
                count_dt_risk_area += 1 # variabel berisiko bertambah satu
                color = (0, 0, 255) # warna kotak pembatas merah
            elif (endXd >= self.safeArea_person[0][0]) and (startYd <= self.safeArea_person[1][1]) and (endYd >= self.safeArea_person[0][1]) and (startXd <= self.safeArea_person[3][0]):
                count_dt_risk_area += 1 # variabel berisiko bertambah satu
                color = (0, 0, 255) # warna kotak pembatas merah

            cv2.rectangle(frame, (startXd, startYd), (endXd, endYd), color, 2) # menggambar kotak pembatas di sekitar dt dalam frame

        # TEXT ANALITIK -------------------------------------------------------------------------------------
        # membuat tulisan di dalam frame
        text_person_no_risk = "Manusia Aman : {}".format(count_person_no_risk_area)
        cv2.putText(frame, text_person_no_risk, (900, frame.shape[0] - 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        if count_person_risk_dt == count_person_risk_area:
            text_person_risk = "Manusia Area Tidak Aman : {}".format(count_person_risk_dt)
            cv2.putText(frame, text_person_risk, (900, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            self.socket.emit('message_from_server', {'type_object': 'person', 'count': count_person_risk_dt, "time": datetime.now()})
        else :
            text_person_risk = "Manusia Area Tidak Aman : {}".format(count_person_risk_area)
            cv2.putText(frame, text_person_risk, (900, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            self.socket.emit('message_from_server', {'type_object': 'person', 'count': count_person_risk_area, "time": datetime.now()})

        if count_dt_risk_person == count_dt_risk_area:
            text_hd = "Dump Truck Area Tidak Aman : {}".format(str(count_dt_risk_person))
            cv2.putText(frame, text_hd, (900, frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            self.socket.emit('message_from_server', {'type_object': 'DT', 'count': count_dt_risk_person, "time": datetime.now()})
        else :
            text_hd = "Dump Truck Area Tidak Aman : {}".format(str(count_dt_risk_area))
            cv2.putText(frame, text_hd, (900, frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            self.socket.emit('message_from_server', {'type_object': 'DT', 'count': count_dt_risk_area, "time": datetime.now()})

        return frame