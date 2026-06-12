import sys
import os
from asyncio.staggered import staggered_race
from cmath import phase
import json
import random
import cv2
import numpy as np
# from PyQt5.QtGui.QIcon import setFallbackThemeName
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget, \
    QHBoxLayout, QGridLayout, QMenu, QAction
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QBrush, QColor
from PyQt5.QtCore import QTimer, Qt , QDateTime
from pandas.core.window.doc import template_header
from setuptools.sandbox import save_path
from tensorflow.keras.models import load_model
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import  shutil
import time
from sendmail import send_email
import re

from tensorflow.python.ops.ragged.ragged_math_ops import add_n

cred = credentials.Certificate('D:/aiforlife-12891-firebase-adminsdk-9g1al-4b9118fe29.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://aiforlife-12891-default-rtdb.firebaseio.com/'
})



# Load trained models
fruit_model_path = 'FinalModel_2.keras'
disease_model_path = 'Benh-pepper.keras'

fruit_model = load_model(fruit_model_path)
disease_model = load_model(disease_model_path)

# Adjust paths based on your dataset structure
fruit_labels = sorted(os.listdir('dataai/train'))
disease_labels = sorted(os.listdir('data-benh/train'))

def preprocess_image(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def predict_fruit(image):
    preprocessed_img = preprocess_image(image)
    prediction = fruit_model.predict(preprocessed_img)
    confidence = np.max(prediction)
    class_idx = np.argmax(prediction)
    class_label = fruit_labels[class_idx]
    return class_label if confidence >= 0.5 else None

def predict_disease(image):
    preprocessed_img = preprocess_image(image)
    prediction = disease_model.predict(preprocessed_img)
    confidence = np.max(prediction)
    class_idx = np.argmax(prediction)
    class_label = disease_labels[class_idx]
    return class_label if confidence >= 0.5 else None

with open('stage_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

class FruitDiseaseClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DL EcoTech Pioneers')
        self.setGeometry(100, 100, 1200, 800)
        # Set background image
        self.setStyleSheet("""
            QMainWindow {
                 background-color: #3498db;

            }
            QLabel {
                border-radius: 10px;
                color: white;
                padding: 10px;
                font-size: 18px;
            }
            QPushButton {
                color: white;
                padding: 6px;
                font-size: 18px;
                background-color: #3498db;
                border: 3px solid white;
                border-radius: 10px;
                background: qlineargradient(
                spread: pad, x1: 0, y1: 0, x2: 1, y2: 1, 
                stop: 0 #8e44ad, stop: 1 #3498db ); 
                text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.8); 
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)




        # Main layout setup
        main_layout = QVBoxLayout()


        header_layout = QHBoxLayout()



        self.temev_header_label = QLabel("T-EV: --°C", self)
        self.temev_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.temev_header_label.setStyleSheet("color: white;")

        self.humev_header_label = QLabel("Hum-EV: --%", self)
        self.humev_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.humev_header_label.setStyleSheet("color: white;")

        self.tem_soilmoisture_header_label = QLabel("T-Soil: --%", self)
        self.tem_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.tem_soilmoisture_header_label.setStyleSheet("color: white;")

        self.hum_soilmoisture_header_label = QLabel("Hum-Soil: --%", self)
        self.hum_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.hum_soilmoisture_header_label.setStyleSheet("color: white;")


        self.ph_soilmoisture_header_label = QLabel("PH: --", self)
        self.ph_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.ph_soilmoisture_header_label.setStyleSheet("color: white;")

        self.ec_soilmoisture_header_label = QLabel("EC: -- mS / cm", self)
        self.ec_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.ec_soilmoisture_header_label.setStyleSheet("color: white;")

        self.nito_soilmoisture_header_label = QLabel("N: --", self)
        self.nito_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.nito_soilmoisture_header_label.setStyleSheet("color: white;")

        self.photpho_soilmoisture_header_label = QLabel("P: --%", self)
        self.photpho_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.photpho_soilmoisture_header_label.setStyleSheet("color: white;")

        self.kali_soilmoisture_header_label = QLabel("K: --%", self)
        self.kali_soilmoisture_header_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.kali_soilmoisture_header_label.setStyleSheet("color: white;")

        self.user_icon_label = QLabel(self)
        self.user_icon_label.setPixmap(
            QPixmap("background/user.png").scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # Tạo khung hình tròn bằng CSS
        self.user_icon_label.setStyleSheet("""
            border: 2px solid black;          /* Độ dày và màu của khung viền */
            border-radius: 24px;              /* Bán kính bằng nửa chiều rộng/chiều cao để thành hình tròn */
            background-color: white;          /* Màu nền */
            padding: 5px;                     /* Khoảng cách giữa viền và nội dung */
        """)

        # Đặt kích thước cố định cho QLabel để giữ khung tròn
        self.user_icon_label.setAlignment(Qt.AlignCenter)

        self.user_label = QLabel("", self)
        self.user_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.user_label.setStyleSheet("color: pink;")

        self.time_label = QLabel("Time: --:--:--", self)
        self.time_label.setFont(QFont('Arial', 18, QFont.Bold))
        self.time_label.setStyleSheet("color: pink;")

        # Tạo QTimer để cập nhật thời gian
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)


        header_layout.addWidget(self.temev_header_label)
        header_layout.addWidget(self.humev_header_label)
        header_layout.addWidget(self.tem_soilmoisture_header_label)
        header_layout.addWidget(self.hum_soilmoisture_header_label)
        header_layout.addWidget(self.ph_soilmoisture_header_label)
        header_layout.addWidget(self.ec_soilmoisture_header_label)
        header_layout.addWidget(self.nito_soilmoisture_header_label)
        header_layout.addWidget(self.photpho_soilmoisture_header_label)
        header_layout.addWidget(self.kali_soilmoisture_header_label)

        header_layout.addStretch()  # Push the labels to the left
        header_layout.addWidget(self.user_icon_label)
        header_layout.addWidget(self.user_label)
        header_layout.addWidget(self.time_label)


        main_layout.addLayout(header_layout)

        self.user_menu = QMenu(self)
        option1 = QAction("Thông báo Email", self)
        option2 = QAction("Bật thông báo hệ thống", self)
        option3 = QAction("Logout", self)


        self.user_menu.addAction(option1)
        self.user_menu.addAction(option2)
        self.user_menu.addAction(option3)

        option1.triggered.connect(self.option1_clicked)
        option2.triggered.connect(self.option2_clicked)
        option3.triggered.connect(self.option3_clicked)


        self.menu_visible = False


        self.user_icon_label.mousePressEvent = self.toggle_menu

        option1.setCheckable(True)
        option2.setCheckable(True)





        # Title label
        title_label = QLabel("DL EcoTech Pioneers", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 40, QFont.Bold))
        title_label.setStyleSheet("""
            color: white;
            font-size: 40px;
            text-align: center;
            padding: 2px;
            border: 3px solid white;
            border-radius: 20px;
            background: qlineargradient(
                spread: pad, x1: 0, y1: 0, x2: 1, y2: 1, 
                stop: 0 #8e44ad, stop: 1 #3498db
            ); /* Gradient tím đến xanh dương */
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.8); /* Đổ bóng đậm */
        """)


        main_layout.addWidget(title_label)



        # Grid for layout
        grid_layout = QGridLayout()
        self.video_frames = []
        self.result_labels_fruit = []
        self.result_labels_disease = []
        self.stage_labels = []
        self.bio_objective_labels = []
        self.temperature_labels = []
        self.humidity_labels = []
        self.ph_labels = []


        for idx in range(4):
            # Create layout for each cell
            cell_layout = QHBoxLayout()
            cell_layout.setSpacing(10)

            # Left: Image display
            image_label = QLabel(self)
            image_label.setFixedSize(500, 350)
            image_label.setStyleSheet("background-color: #34495e; border: 2px solid #ecf0f1;")

            # Right: Results and buttons
            right_layout = QVBoxLayout()
            right_layout.setSpacing(15)

            # Information labels section
            info_layout = QVBoxLayout()
            info_layout.setSpacing(10)

            # Stage
            stage_label = QLabel("Stage:", self)
            stage_label.setFont(QFont('Arial', 12))
            stage_label.setAlignment(Qt.AlignLeft)
            stage_label.setStyleSheet("color: white;")
            stage_label.setWordWrap(True)
            info_layout.addWidget(stage_label)




            # Bio Objective
            bio_objective_label = QLabel("Bio Objective:", self)
            bio_objective_label.setFont(QFont('Arial', 12))
            bio_objective_label.setAlignment(Qt.AlignLeft)
            bio_objective_label.setStyleSheet("color: white;")
            bio_objective_label.setWordWrap(True)
            info_layout.addWidget(bio_objective_label)

            # Temperature
            temperature_label = QLabel("Temperature:", self)
            temperature_label.setFont(QFont('Arial', 12))
            temperature_label.setAlignment(Qt.AlignLeft)
            temperature_label.setStyleSheet("color: white;")
            temperature_label.setWordWrap(True)
            info_layout.addWidget(temperature_label)

            # Humidity
            humidity_label = QLabel("Humidity:", self)
            humidity_label.setFont(QFont('Arial', 12))
            humidity_label.setAlignment(Qt.AlignLeft)
            humidity_label.setStyleSheet("color: white;")
            humidity_label.setWordWrap(True)
            info_layout.addWidget(humidity_label)

            # pH
            ph_label = QLabel("pH:", self)
            ph_label.setFont(QFont('Arial', 12))
            ph_label.setAlignment(Qt.AlignLeft)
            ph_label.setStyleSheet("color: white;")
            ph_label.setWordWrap(True)
            info_layout.addWidget(ph_label)

            # Add information layout to right section
            right_layout.addLayout(info_layout)

            # Results section
            result_layout = QVBoxLayout()
            result_layout.setSpacing(15)

            # Fruit result label
            result_label_fruit = QLabel('Fruit Result: Not Processed', self)
            result_label_fruit.setFont(QFont('Arial', 14))
            result_label_fruit.setAlignment(Qt.AlignLeft)
            result_label_fruit.setWordWrap(True)
            result_layout.addWidget(result_label_fruit)



            # Disease result label
            result_label_disease = QLabel('Disease Result: Not Processed', self)
            result_label_disease.setFont(QFont('Arial', 14))
            result_label_disease.setAlignment(Qt.AlignLeft)
            result_label_disease.setWordWrap(True)
            result_layout.addWidget(result_label_disease)

            # Add result layout to right section
            right_layout.addLayout(result_layout)

            # Button layout
            button_layout = QHBoxLayout()
            if idx == 0:
                # Webcam control buttons for the first cell
                webcam_start_btn = QPushButton('Start Webcam', self)
                webcam_start_btn.clicked.connect(lambda _, x=idx: self.start_webcam(x))
                button_layout.addWidget(webcam_start_btn)

                webcam_stop_btn = QPushButton('Stop Webcam', self)
                webcam_stop_btn.clicked.connect(lambda _, x=idx: self.stop_webcam(x))
                button_layout.addWidget(webcam_stop_btn)
            else:
                # File selection and processing buttons for other cells
                select_btn = QPushButton(f'Select File {idx}', self)
                select_btn.clicked.connect(lambda _, x=idx: self.select_file(x))
                button_layout.addWidget(select_btn)

                process_btn = QPushButton(f'Process {idx}', self)
                process_btn.clicked.connect(lambda _, x=idx: self.process_file(x))
                button_layout.addWidget(process_btn)

            right_layout.addLayout(button_layout)

            # Combine image and results
            cell_layout.addWidget(image_label)
            cell_layout.addLayout(right_layout)

            row, col = divmod(idx, 2)  # Ensure two cells per row
            grid_layout.addLayout(cell_layout, row, col)

            # Store references
            self.video_frames.append({'label': image_label, 'path': None, 'timer': QTimer(self), 'webcam': None})

            self.result_labels_fruit.append(result_label_fruit)
            self.result_labels_disease.append(result_label_disease)
            self.ph_labels.append(ph_label)
            self.stage_labels.append(stage_label)
            self.bio_objective_labels.append(bio_objective_label)
            self.temperature_labels.append(temperature_label)
            self.humidity_labels.append(humidity_label)



        main_layout.addLayout(grid_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


        self.timer = QTimer()

        self.timer.timeout.connect(self.start_listening_data)
        self.timer.start(8000)

    def set_user_email(self, user_email):
        self.user_email = user_email

    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_user_name(self, username):
        self.username = username
        self.update_user_label()

    def update_user_label(self):
        # Hiển thị tên người dùng trong giao diện
        if hasattr(self, 'user_label'):
            self.user_label.setText(f"Xin chào, {self.username}!")

    def toggle_menu(self, event):
        """Hiển thị hoặc ẩn menu khi nhấn vào user icon."""
        if self.menu_visible:
            self.user_menu.close()  # Đóng menu nếu đang mở
            self.menu_visible = False
        else:
            # Hiển thị menu tại vị trí của user icon
            self.user_menu.exec_(self.user_icon_label.mapToGlobal(event.pos()))
            self.menu_visible = True

    def save_option_to_firebase(self,user_id, option, checked):
        try:
            # Kiểm tra các dữ liệu truyền vào
            try:
                ref = db.reference().child('users').child(user_id).child('options')
                options = ref.get()
                print("Fetched options:", options)  # Kiểm tra kết nối và lấy dữ liệu
            except Exception as e:
                print(f"Error occurred: {e}")

            # Truy cập mục options của user_id

            # Kiểm tra nếu `options` chưa tồn tại, tạo mới
            if options is None:
                print("Options not found. Creating default options...")
                ref.set({
                    'option1': False,  # Mặc định là False
                    'option2': False  # Mặc định là False
                })
                options = {'option1': False, 'option2': False}  # Gán lại giá trị mặc định cho `options`

            # Cập nhật trạng thái của option
            ref.update({option: checked})
            print(f"Option {option} updated to {checked}")

        except Exception as e:
            print(f"Error occurred while saving options: {e}")
            # In thêm thông tin chi tiết để kiểm tra lỗi
            print("Error details:", e.args)

    def option1_clicked(self,checked1):
        print(self.user_id)
        print(checked1)
        self.save_option_to_firebase(self.user_id, "option1", checked1)

    def option2_clicked(self,checked):
        self.save_option_to_firebase(self.user_id,"option2",checked)

    def option3_clicked(self):
        print("Option 3 selected")
        self.close()  # Đóng cửa sổ hiện tại
        from login import LoginWindow
        self.window = LoginWindow()  # Tạo một cửa sổ mới
        self.window.show()  # Hiển thị cửa sổ mới


    def load_user_options(self,userid):
        try:
            # Truy cập dữ liệu các tùy chọn từ Firebase
            ref = db.reference().child('users').child(userid).child('options')
            options = ref.get()  # Lấy dữ liệu các tùy chọn người dùng

            # Trả về giá trị True/False cho option1 và option2
            option1_value = options.get('option1', False)  # Nếu không có, mặc định là False
            option2_value = options.get('option2', False)  # Nếu không có, mặc định là False

            return option1_value, option2_value  # Trả về giá trị của option1 và option2
        except Exception as e:
            print(f"Error occurred while loading user options: {e}")
            return False, False  # Trả về False nếu có lỗi

    def update_time(self):

        current_time = QDateTime.currentDateTime().toString("hh:mm:ss   |   dd-MM-yyyy")
        self.time_label.setText(current_time)


    def start_listening_data(self):
        ref = db.reference('Data_environment')
        ref.listen(self.update_sensor_values)

    def update_sensor_values(self, event):
        data = event.data  # Lấy dữ liệu mới

        if not data:  # Kiểm tra nếu không có dữ liệu mới
            return

        # Cập nhật giá trị mới
        temperature_value = data.get("Temev", 0)
        humidity_value = data.get("Humev", 0)
        temsoil_value = data.get("Temsoil", 0)
        humsoilmoisture_value = data.get("Humsoil",0)
        ph_value = data.get("PH",0)
        ec_value = data.get("EC",0)
        nito_value = data.get("Nito",0)
        phot_value = data.get("Photpho",0)
        kali_value = data.get("kali",0)


        self.temev_header_label.setText(f"T-EV: {temperature_value:}°C")
        self.humev_header_label.setText(f"Hum-EV: {humidity_value:}%")
        self.tem_soilmoisture_header_label.setText(f"T-Soil: {temsoil_value:}°C")
        self.hum_soilmoisture_header_label.setText(f"Hum-Soil: {humsoilmoisture_value}%")
        self.ph_soilmoisture_header_label.setText(f"PH: {ph_value}")
        self.ec_soilmoisture_header_label.setText(f"EC: {ec_value} uS / m")
        self.nito_soilmoisture_header_label.setText(f"N: {nito_value} mg/l")
        self.photpho_soilmoisture_header_label.setText(f"P: {phot_value} mg/l")
        self.kali_soilmoisture_header_label.setText(f"K: {kali_value} mg/l")

    def start_webcam(self, idx):
        if 'webcam' in self.video_frames[idx] and self.video_frames[idx]['webcam']:
            self.result_labels_fruit[idx].setText('Webcam already active!')
            return

        cap = cv2.VideoCapture(0)  # Mở webcam
        if not cap.isOpened():
            self.result_labels_fruit[idx].setText('Cannot access webcam!')
            return

        self.video_frames[idx]['webcam'] = cap
        self.video_frames[idx]['timer'] = QTimer(self)
        self.video_frames[idx]['timer'].timeout.connect(lambda: self.update_webcam_frame(cap, idx))
        self.video_frames[idx]['timer'].start(30)

        self.video_frames[idx]['start_time'] = time.time()
        self.video_frames[idx]['last_saved_time'] = 0

    def stop_webcam(self, idx):
        if 'webcam' in self.video_frames[idx] and self.video_frames[idx]['webcam']:
            self.video_frames[idx]['timer'].stop()
            self.video_frames[idx]['webcam'].release()
            self.video_frames[idx]['webcam'] = None
            self.result_labels_fruit[idx].setText('Webcam stopped')
            self.result_labels_disease[idx].setText('Webcam stopped')
            self.video_frames[idx]['label'].clear()
        else:
            self.result_labels_fruit[idx].setText('Webcam not active!')

    def update_webcam_frame(self, cap, idx):
        ret, frame = cap.read()
        if not ret:
            self.video_frames[idx]['timer'].stop()
            cap.release()
            self.result_labels_fruit[idx].setText('Webcam stopped')
            self.result_labels_disease[idx].setText('Webcam stopped')
            return

        # Predict fruit class
        fruit_class_label = predict_fruit(frame)

        # Predict disease class
        disease_class_label = predict_disease(frame)


        temev_value = self.temev_header_label.text()
        humev_value = self.humev_header_label.text()
        temsoil_value = self.tem_soilmoisture_header_label.text()
        humsoil_value = self.hum_soilmoisture_header_label.text()
        ph_value = self.ph_soilmoisture_header_label.text()
        ec_value = self.ec_soilmoisture_header_label.text()
        nito_value = self.nito_soilmoisture_header_label.text()
        pp_value = self.photpho_soilmoisture_header_label.text()
        kl_value = self.kali_soilmoisture_header_label.text()



        current_time_sec = time.time() - self.video_frames[idx]['start_time']

        # Chỉ lưu ảnh mỗi với số giây
        if current_time_sec >= self.video_frames[idx]['last_saved_time'] + 60:
            self.video_frames[idx]['last_saved_time'] = int(current_time_sec)

            # Đảm bảo thư mục lưu ảnh tồn tại
            save_dir = "data_test"
            os.makedirs(save_dir, exist_ok=True)

            # Tạo tên file ảnh với thời gian hiện tại
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(save_dir, f"video_{idx}_{timestamp}.jpg")

            cv2.imwrite(save_path, frame)
            print(f"Saved frame to {save_path}")

            self.capnhapgaitrilabel(fruit_class_label,disease_class_label, idx, save_path,temev_value,humev_value,temsoil_value,humsoil_value,ph_value,ec_value,nito_value,pp_value,kl_value,True)



        else:
            self.capnhapgaitrilabel(fruit_class_label,disease_class_label, idx,None,temev_value,humev_value,temsoil_value,humsoil_value,ph_value,ec_value,nito_value,pp_value,kl_value,True)


        # Update labels with respective results
        self.result_labels_fruit[idx].setText(f'Fruit: {fruit_class_label if fruit_class_label else "Not Recognized"}')
        self.result_labels_disease[idx].setText(
            f'Disease: {disease_class_label if disease_class_label else "No Disease Detected"}')

        # Display the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], rgb_frame.strides[0],
                      QImage.Format_RGB888)
        self.video_frames[idx]['label'].setPixmap(QPixmap.fromImage(qimg).scaled(500, 350))

        try:
            del qimg  # Giải phóng bộ nhớ của qimg nếu không còn cần thiết nữa
        except Exception as e:
            print(f"Error freeing memory: {e}")


    def select_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Image/Video', '', 'Image/Video Files (*.png; *.jpg; *.jpeg;*.jfif;*webp; *.mp4; *.avi)')
        if file_path:
            self.video_frames[idx]['path'] = file_path
            self.result_labels_fruit[idx].setText('File Selected')
            self.result_labels_disease[idx].setText('File Selected')
            if file_path.endswith(('.png', '.jpg', '.jpeg''.jfif''.webp')):
                pixmap = QPixmap(file_path).scaled(500, 350)
                self.video_frames[idx]['label'].setPixmap(pixmap)

    def process_file(self, idx):
        file_path = self.video_frames[idx]['path']
        if not file_path:
            self.result_labels_fruit[idx].setText('Please select a file!')
            self.result_labels_disease[idx].setText('Please select a file!')
            return

        if file_path.endswith(('.png', '.jpg', '.jpeg''.jfif''.webp')):
            self.process_image(file_path, idx)
        elif file_path.endswith(('.mp4', '.avi')):
            self.process_video(file_path, idx)
        else:
            self.result_labels_fruit[idx].setText('Unsupported file format!')
            self.result_labels_disease[idx].setText('Unsupported file format!')

    def process_image(self, file_path, idx):
        img = cv2.imread(file_path)
        if img is None:
            self.result_labels_fruit[idx].setText('Cannot read image!')
            self.result_labels_disease[idx].setText('Cannot read image!')
            self.ph_labels[idx].setText('pH: N/A')
            self.stage_labels[idx].setText('Stage:')
            self.bio_objective_labels[idx].setText('Bio Objective:')
            self.temperature_labels[idx].setText('Temperature:')
            self.humidity_labels[idx].setText('Humidity:')

            return

        # Predict fruit class
        fruit_class_label = predict_fruit(img)

        # Predict disease class
        disease_class_label = predict_disease(img)
        temev_value = self.temev_header_label.text()
        humev_value = self.humev_header_label.text()
        temsoil_value = self.tem_soilmoisture_header_label.text()
        humsoil_value = self.hum_soilmoisture_header_label.text()
        ph_value = self.ph_soilmoisture_header_label.text()
        ec_value = self.ec_soilmoisture_header_label.text()
        nito_value = self.nito_soilmoisture_header_label.text()
        pp_value = self.photpho_soilmoisture_header_label.text()
        kl_value = self.kali_soilmoisture_header_label.text()

        self.capnhapgaitrilabel(fruit_class_label,disease_class_label,idx,file_path,temev_value,humev_value,temsoil_value,humsoil_value,ph_value,ec_value,nito_value,pp_value,kl_value,True)



        # Update labels with respective results

        self.result_labels_fruit[idx].setText(f'Fruit: {fruit_class_label if fruit_class_label else "Not Recognized"}')
        self.result_labels_disease[idx].setText(f'Disease: {disease_class_label if disease_class_label else "No Disease Detected"}')



    def capnhapgaitrilabel(self, name,name_benh,idx,file_path,temev_value,humev_value, temsoil_value, humsoil_value,pht_value, ec_value, nito_value, pp_value,kl_value,capnhap_lb):
        # Kiểm tra giai đoạn và lấy giá trị pH tương ứng
        ph_value = None
        stage_value = None
        Bio_value = None
        Tem_value = None
        Hum_value = None
        da_value = None
        nd_value = None
        ecc_value = None
        Temev_value = temev_value
        Humev_value = humev_value
        Temsoil_value = temsoil_value
        Humsoil_value = humsoil_value
        Pht_value = pht_value
        Ec_value = ec_value
        Nito_value = nito_value
        Pp_value = pp_value
        Kl_value = kl_value
        if name == "GĐ1_GIEO_HAT_NAY_MAM":
            ph_value = data["0"]["ph"]
            stage_value = data["0"]["stage"]
            Bio_value = data["0"]["bio_objective"]
            Tem_value = data["0"]["temperature"]
            Hum_value = data["0"]["humidity"]
            da_value = data["0"]["dad"]
            nd_value = data["0"]["ndd"]
            ecc_value = data["0"]["ec"]
        elif name == "GĐ2_PHAT_TRIEN_CAY_CON":
            ph_value = data["1"]["ph"]
            stage_value = data["1"]["stage"]
            Bio_value = data["1"]["bio_objective"]
            Tem_value = data["1"]["temperature"]
            Hum_value = data["1"]["humidity"]
            da_value = data["1"]["dad"]
            nd_value = data["1"]["ndd"]
            ecc_value = data["1"]["ec"]
        elif name == "GĐ3_PHAT_TRIEN_SINH_TRUONG":
            ph_value = data["2"]["ph"]
            stage_value = data["2"]["stage"]
            Bio_value = data["2"]["bio_objective"]
            Tem_value = data["2"]["temperature"]
            Hum_value = data["2"]["humidity"]
            da_value = data["2"]["dad"]
            nd_value = data["2"]["ndd"]
            ecc_value = data["2"]["ec"]
        elif name == "GĐ4_RA_HOA_TAO_QUA":
            ph_value = data["3"]["ph"]
            stage_value = data["3"]["stage"]
            Bio_value = data["3"]["bio_objective"]
            Tem_value = data["3"]["temperature"]
            Hum_value = data["3"]["humidity"]
            da_value = data["3"]["dad"]
            nd_value = data["3"]["ndd"]
            ecc_value = data["3"]["ec"]
        elif name == "GĐ5_CHIN_QUA":
            ph_value = data["4"]["ph"]
            stage_value = data["4"]["stage"]
            Bio_value = data["4"]["bio_objective"]
            Tem_value = data["4"]["temperature"]
            Hum_value = data["4"]["humidity"]
            da_value = data["4"]["dad"]
            nd_value = data["4"]["ndd"]
            ecc_value = data["4"]["ec"]


        if name_benh == "BENH-DOM-LA":
            x ="Bệnh đóm lá"
            result_benh = (
                "Thuốc hóa học khuyến cáo sử dụng là hỗn hợp đồng + mancozeb + streptocycline "
                "phun định kỳ để phòng và trừ bệnh."
            )
        elif name_benh == "BENH-KHAM-LA":
            x ="Bệnh khám lá"
            result_benh = (
                "Cần tiến hành phun Viruka Max để giúp phục hồi lại lá nhiễm bệnh và lá mới không bị bệnh.\n"
                "(Giúp cây phát triển bình thường vẫn ra bông, đậu trái và đạt chất lượng bình thường, "
                "tăng cường kháng thể cho cây tránh côn trùng chích hút – trung gian truyền bệnh)."
            )
        elif name_benh == "BENH-PHAN-TRANG":
            x ="Bệnh phấn trắng"
            result_benh = (
                "Pha mỗi loại 1 chai bao gồm Nano Đồng + Nano Silica + Nano Chitosan vào phuy 200 lít nước. "
                "Phun 1 lần/ ngày vào buổi sáng sớm."
            )
        elif name_benh == "BENH-THAN-THU":
            x ="Bệnh thán thư"
            result_benh = (
                "Khi thấy dấu hiệu bệnh xuất hiện thì phun thuốc kịp thời với hỗn hợp Agrilife 100SL và Envio 250SC "
                "(25 ml + 25 ml/ 25 lít) và phun lặp lại lần 2 nếu thấy bệnh chưa dứt hẳn."
            )
        elif name_benh == "THOI-TRAI-DO-VI-KHUAN":
            x ="Bệnh thối trái do vi khuẩn"
            result_benh = (
                "Chưa có biện pháp đặc trị.\n"
                "Cách phòng ngừa: Trước khi trồng cần thu gom những cây ớt của vụ trước, tiêu hủy triệt để lá bệnh sang vụ sau. "
                "Phải làm đất và lồng lên mặt trồng để hạn chế sâu bệnh truyền qua đất."
            )
        elif name_benh == "BINH-THUONG":
            x=""
            result_benh = "Không có bệnh."




        if capnhap_lb:
        # Cập nhật giá trị pH vào giao diện nếu ph_value không phải None
            if ph_value is not None:

                self.ph_labels[idx].setText(f'pH: {ph_value}')
                self.stage_labels[idx].setText(f'Stage: {stage_value}')
                self.bio_objective_labels[idx].setText(f'Bio Objective: {Bio_value}')
                self.temperature_labels[idx].setText(f'Temperature: {Tem_value}')
                self.humidity_labels[idx].setText(f'Humidity: {Hum_value}')




                if file_path == None:
                    print("oke")
                else :
                    self.save_data_to_firebase(stage_value, ph_value, Bio_value, Tem_value, Hum_value, idx)
                    self.save_to_project_folder(file_path, idx, ph_value, stage_value, Bio_value, Tem_value, Hum_value)


                    temp_optimal = re.search(r"Tối ưu: (\d+)-(\d+)", Tem_value)
                    if temp_optimal:
                        temp_min = float(temp_optimal.group(1))
                        temp_max = float(temp_optimal.group(2))
                        temp_avg = (temp_min + temp_max) / 2
                        hum_optimal = re.search(r"Tối ưu: (\d+)-(\d+)", Hum_value)
                    if hum_optimal:
                        hum_min = float(hum_optimal.group(1))
                        hum_max = float(hum_optimal.group(2))
                        hum_avg = (hum_min + hum_max) / 2
                    ph_range = re.search(r"([\d.]+) – ([\d.]+)", ph_value)
                    if ph_range:
                        ph_min = float(ph_range.group(1))
                        ph_max = float(ph_range.group(2))
                        ph_avg = (ph_min + ph_max) / 2


                    da_optimal = re.search(r"Tối ưu: (\d+)-(\d+)", da_value)

                    if da_optimal:
                        da_min = float(da_optimal.group(1))
                        da_max = float(da_optimal.group(2))
                        da_avg = (da_min + da_max) / 2

                    nd_range = re.search(r"([\d.]+) – ([\d.]+)", nd_value)
                    if nd_range:
                        nd_min = float(nd_range.group(1))
                        nd_max = float(nd_range.group(2))
                        nd_avg = (nd_min + nd_max) / 2
                    ecc_range = re.search(r"([\d.]+) – ([\d.]+)", ecc_value)
                    print(ecc_range)
                    if ecc_range:
                        ecc_min = float(ecc_range.group(1))
                        ecc_max = float(ecc_range.group(2))
                        ecc_avg = (ecc_min + ecc_max) / 2
                    print(ecc_avg)



                    Temev_temperature = self.extract_average(Temev_value)
                    Humev_temperature = self.extract_average(Humev_value)
                    pht_temperature = self.extract_average(pht_value)
                    Temsoil_temperature = self.extract_average(Temsoil_value)
                    Humsoil_temperature = self.extract_average(Humsoil_value)
                    ec_temperature = self.extract_average(Ec_value)


                    result_mes =  self.calculate_differences(Temev_temperature,Humev_temperature,pht_temperature,Temsoil_temperature,Humsoil_temperature,ec_temperature,temp_avg,hum_avg,ph_avg,da_avg,nd_avg,ecc_avg)

                    idcammail = idx + 1
                    option1, _ = self.load_user_options(self.user_id)
                    if option1:  # True thì gửi email
                        message = (
                            "Thông báo tình trạng ở vườn\n\n"
                            "Dữ liệu môi trường:\n"
                            f"- {Temev_value}\n"
                            f"- {Humev_value}\n"
                            f"- {Temsoil_value}\n"
                            f"- {Humsoil_value}\n"
                            f"- {Pht_value}\n"
                            f"- {Ec_value}\n"
                            f"- {Nito_value}\n"
                            f"- {Pp_value}\n"
                            f"- {Kl_value}\n\n"
                            "Thông tin sinh trưởng:\n"
                            f"- Giai đoạn: {stage_value}\n"
                            f"- Mục tiêu sinh học: {Bio_value}\n"
                            f"- Nhiệt độ lý tưởng: {Tem_value}\n"
                            f"- Độ ẩm lý tưởng: {Hum_value}\n\n"
                            "Dữ liệu cần bổ sung:\n"
                            f""
                            f"{result_mes}\n\n"
                            f"Trình trạng bệnh của cây:{x}\n"
                            f"{result_benh}"


                        )
                        send_email(
                            sender_email="huynhkanh24@gmail.com",
                            receiver_email=f"{self.user_email}",
                            subject=f"Thông báo tình trạng ở vườn Camera {idcammail} ",
                            message=message,
                            attachment_path=file_path  # Đường dẫn tệp đính kèm
                        )
        else:
            print("o")


    def save_data_to_firebase(self, stage, ph, bio_objective, temperature, humidity, idx):

        if idx == 0:
            cam = "Camera_zon1"
        elif idx == 1:
            cam = "Camera_zon2"
        elif idx == 2:
            cam = "Camera_zon3"
        else:
            cam = "Camera_zon4"

        timestamp = datetime.now().date().isoformat()# ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

        # Tạo đối tượng dữ liệu
        data = {
            "stage": stage,
            "ph": ph,
            "bio_objective": bio_objective,
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": datetime.now().strftime("%Y-%m-%d | %H:%M")
        }
        ref = db.reference().child('plant_data').child(cam).child(timestamp)
        # Lưu dữ liệu vào Firebase
        try:
            ref.push(data)
            print(f"Data saved successfully under path: plant_data/{cam}/{timestamp}")
        except Exception as e:
            print(f"Failed to save data: {str(e)}") # Sử dụng `set` để lưu tại vị trí cụ thể
        print(f"Data saved successfully under path: plant_data/{cam}/{timestamp}")

    def calculate_differences(self, temev_value, humev_value, ph_actual, temsoil_value, humsoil_value, ec_value, temp_avg, hum_avg, ph_avg, temsoil_avg, humsoil_avg, ec_avg):
        result = []

        # Tính sai số nhiệt độ
        temp_difference = temev_value - temp_avg
        if temp_difference < 0:
            result.append(f"Nhiệt độ cần điều chỉnh tăng: {abs(temp_difference):.2f}°C")
        else:
            result.append(f"Nhiệt độ cần điều chỉnh giảm: {temp_difference:.2f}°C")

        # Tính sai số độ ẩm
        hum_difference = humev_value - hum_avg
        if hum_difference < 0:
            result.append(f"Độ ẩm cần điều chỉnh tăng lên: {abs(hum_difference):.2f}%")
        else:
            result.append(f"Độ ẩm cần điều chỉnh đã giảm xuống: {hum_difference:.2f}%")

        # Tính sai số pH
        ph_difference = ph_actual - ph_avg
        if ph_difference < 0:
            result.append(f"pH cần điều chỉnh tăng lên: {abs(ph_difference):.2f}")
        else:
            result.append(f"pH cần điều chỉnh giảm xuống: {ph_difference:.2f}")

        # Tính sai số nhiệt độ đất
        temsoil_difference = temsoil_value - temsoil_avg
        if temsoil_difference < 0:
            result.append(f"Nhiệt độ đất cần điều chỉnh tăng lên: {abs(temsoil_difference):.2f}°C")
        else:
            result.append(f"Nhiệt độ đất cần điều chỉnh giảm xuống: {temsoil_difference:.2f}°C")

        # Tính sai số độ ẩm đất
        humsoil_difference = humsoil_value - humsoil_avg
        if humsoil_difference < 0:
            result.append(f"Độ ẩm đất cần điều chỉnh tăng lên: {abs(humsoil_difference):.2f}%")
        else:
            result.append(f"Độ ẩm đất cần điều chỉnh giảm xuống: {humsoil_difference:.2f}%")

        # Tính sai số EC (Độ dẫn điện)
        ec_difference = ec_value - ec_avg
        if ec_difference < 0:
            result.append(f"EC cần điều chỉnh tăng lên: {abs(ec_difference):.2f}")
        else:
            result.append(f"EC cần điều chỉnh giảm xuống: {ec_difference:.2f}")

        return "\n".join(result)  # Trả về chuỗi kết quả

    def extract_average(self,input_str):
        # Tìm tất cả các số trong chuỗi
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", input_str)
        if matches:
            # Chuyển đổi các số thành float và tính trung bình
            numbers = [float(num) for num in matches]
            return sum(numbers) / len(numbers)  # Tính trung bình
        return None  # Trả về None nếu không tìm thấy số



    def save_to_project_folder(self,file_path, idx, ph_value, stage_value, Bio_value, Tem_value, Hum_value):
        base_dir = os.path.join(os.getcwd(), "data_ls")

        cam_value = f"camera{idx + 1}" #camera1234

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = os.path.join(base_dir, cam_value, timestamp)
        os.makedirs(folder_name, exist_ok=True)

        # Sao chép ảnh vào thư mục
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # Nếu là ảnh, sao chép vào thư mục đã tạo
            img_dst = os.path.join(folder_name, os.path.basename(file_path))
            shutil.copy(file_path, img_dst)
            print(f"Image copied to {img_dst}")
        else:
            # Nếu không phải ảnh, xử lý như video hoặc file khác (ví dụ: sao chép file gốc vào thư mục)
            other_dst = os.path.join(folder_name, os.path.basename(file_path))
            shutil.copy(file_path, other_dst)
            print(f"File copied to {other_dst}")

        # Tạo file txt và ghi dữ liệu
        txt_path = os.path.join(folder_name, "data.txt")
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(f"Stage: {stage_value}\n")
            txt_file.write(f"pH: {ph_value}\n")
            txt_file.write(f"Bio Objective: {Bio_value}\n")
            txt_file.write(f"Temperature: {Tem_value}\n")
            txt_file.write(f"Humidity: {Hum_value}\n")
            txt_file.write(f"Camera: {cam_value}\n")

        print(f"Data and image saved in {folder_name}")

    def process_video(self, file_path, idx):
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            self.result_labels_fruit[idx].setText('Cannot open video!')
            self.result_labels_disease[idx].setText('Cannot open video!')
            return

        self.video_frames[idx]['timer'] = QTimer(self)
        self.video_frames[idx]['timer'].timeout.connect(lambda: self.update_frame(cap, idx))
        self.video_frames[idx]['timer'].start(30)



    def update_frame(self, cap, idx):
        ret, frame = cap.read()
        if not ret:
            cap.release()
            self.video_frames[idx]['timer'].stop()
            self.result_labels_fruit[idx].setText('Video Ended')
            self.result_labels_disease[idx].setText('Video Ended')
            # self.ph_labels[idx].setText('pH: N/A')
            self.video_frames[idx]['video_ended'] = True
            return
        else:
            # Reset trạng thái video nếu video còn chạy
            self.video_frames[idx]['video_ended'] = False
        # Predict fruit class
        fruit_class_label = predict_fruit(frame)

        # Predict disease class
        disease_class_label = predict_disease(frame)
        print(disease_class_label)

        temev_value = self.temev_header_label.text()
        humev_value = self.humev_header_label.text()
        temsoil_value = self.tem_soilmoisture_header_label.text()
        humsoil_value = self.hum_soilmoisture_header_label.text()
        ph_value = self.ph_soilmoisture_header_label.text()
        ec_value = self.ec_soilmoisture_header_label.text()
        nito_value = self.nito_soilmoisture_header_label.text()
        pp_value = self.photpho_soilmoisture_header_label.text()
        kl_value = self.kali_soilmoisture_header_label.text()


        # Khởi tạo giá trị nếu chưa có
        if 'last_saved_time' not in self.video_frames[idx]:
            self.video_frames[idx]['last_saved_time'] = 0  # Lưu thời gian lưu ảnh gần nhất

        # Lấy thời gian hiện tại của video
        current_time_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Thời gian hiện tại của video (giây)


        if self.video_frames[idx].get('video_ended', True):
            cap_nhap_lb = False
        else:
            cap_nhap_lb = True

        print(cap_nhap_lb)

        # Chỉ lưu ảnh mỗi 30 giây

        label_text = self.result_labels_disease[idx].text()

        if int(current_time_sec) >= self.video_frames[idx]['last_saved_time'] + 30 and label_text != 'Video Ended':
            self.video_frames[idx]['last_saved_time'] = int(current_time_sec)

            # Đảm bảo thư mục lưu ảnh tồn tại
            save_dir = "data_test"
            os.makedirs(save_dir, exist_ok=True)

            # Tạo tên file ảnh với thời gian hiện tại
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(save_dir, f"video_{idx}_{timestamp}.jpg")

            cv2.imwrite(save_path, frame)
            print(f"Saved frame to {save_path}")


            self.capnhapgaitrilabel(fruit_class_label,disease_class_label,idx,save_path,temev_value,humev_value,temsoil_value,humsoil_value,ph_value,ec_value,nito_value,pp_value,kl_value,cap_nhap_lb)


        else:
            self.capnhapgaitrilabel(fruit_class_label,disease_class_label, idx, None,temev_value,humev_value,temsoil_value,humsoil_value,ph_value,ec_value,nito_value,pp_value,kl_value,cap_nhap_lb)


        # Cập nhật kết quả lên giao diện
        self.result_labels_fruit[idx].setText(f'Fruit: {fruit_class_label if fruit_class_label else "Not Recognized"}')
        self.result_labels_disease[idx].setText(f'Disease: {disease_class_label if disease_class_label else "No Disease Detected"}')


        # Hiển thị khung hình lên giao diện
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_frame.data, rgb_frame.shape[1], rgb_frame.shape[0], rgb_frame.strides[0],
                      QImage.Format_RGB888)
        self.video_frames[idx]['label'].setPixmap(QPixmap.fromImage(qimg).scaled(500, 350))

        # Giải phóng bộ nhớ của frame hiện tại sau khi sử dụng
        try:
            del qimg  # Giải phóng bộ nhớ của qimg nếu không còn cần thiết nữa
        except Exception as e:
            print(f"Error freeing memory: {e}")



# Run application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FruitDiseaseClassifierApp()
    window.show()
    sys.exit(app.exec_())
