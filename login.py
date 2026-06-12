import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, \
    QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import bcrypt
from main import FruitDiseaseClassifierApp ,firebase_admin, db

def verify_user_credentials(email, password):
    try:
        ref = db.reference('users')
        users = ref.order_by_child('email').equal_to(email).get()

        if users:
            # Lấy ID của người dùng từ khóa của đối tượng
            user_id = list(users.keys())[0]  # Lấy ID người dùng
            user = list(users.values())[0]   # Lấy thông tin người dùng

            stored_password = user['password']  # Mật khẩu đã mã hóa lưu trong DB
            user_email = user['email']  # Lấy email của người dùng

            # So sánh mật khẩu đã nhập với mật khẩu đã mã hóa
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Thêm id vào thông tin người dùng
                user['id'] = user_id  # Thêm ID vào thông tin người dùng
                user['email'] = user_email  # Thêm email vào thông tin người dùng
                return user  # Trả về đối tượng người dùng bao gồm id, email và username
        return None  # Trả về None nếu không tìm thấy người dùng hoặc sai mật khẩu
    except Exception as e:
        print(f"Lỗi khi xác thực: {e}")
        return None


def register_user(username, email, password):
    try:
        ref = db.reference('users')

        # Mã hóa mật khẩu
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Lưu thông tin người dùng, bao gồm mật khẩu đã mã hóa
        new_user_ref = ref.push({
            'username': username,
            'email': email,
            'password': hashed_password.decode('utf-8')  # Chuyển mã hóa thành chuỗi để lưu vào DB
        })
        print("Đăng ký người dùng thành công!")
        return True
    except Exception as e:
        print(f"Lỗi khi đăng ký: {e}")
        return False




class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Đăng nhập và Đăng ký")
        self.setGeometry(100, 100, 700, 600)
        self.setStyleSheet("background-color: #FFFAF0;")

        self.stacked_widget = QStackedWidget(self)
        self.login_screen = self.create_login_screen()
        self.register_screen = self.create_register_screen()
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.register_screen)
        self.stacked_widget.setCurrentWidget(self.login_screen)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def create_login_screen(self):
        screen = QWidget(self)
        layout = QVBoxLayout()

        logo = QLabel("DL ECOTECH PIONEERS", self)
        logo.setFont(QFont("Arial", 35, QFont.Bold))
        logo.setStyleSheet("color: #FF5722;")
        logo.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Nhập thông tin đăng nhập", self)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #FF7043;")
        subtitle.setAlignment(Qt.AlignCenter)

        username = QLineEdit(self)
        username.setPlaceholderText("Email")
        username.setFont(QFont("Arial", 12))

        password = QLineEdit(self)
        password.setPlaceholderText("Mật khẩu")
        password.setFont(QFont("Arial", 12))
        password.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Đăng nhập", self)
        login_button.setFont(QFont("Arial", 14))
        login_button.setStyleSheet(""" 
            QPushButton { 
                border: 2px solid transparent; 
                border-radius: 15px; 
                color: white; 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF5722, stop:1 #FF9800); 
                height: 40px; 
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF7043, stop:1 #FFB74D); 
            }
        """)
        login_button.clicked.connect(lambda: self.login_user(username.text(), password.text()))

        register_button = QPushButton("Đăng ký", self)
        register_button.setFont(QFont("Arial", 14))
        register_button.setStyleSheet(""" 
            QPushButton { 
                border: 2px solid transparent; 
                border-radius: 15px; 
                color: white; 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF5722, stop:1 #FF9800); 
                height: 40px; 
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF7043, stop:1 #FFB74D); 
            }
        """)
        register_button.clicked.connect(self.show_register_screen)

        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(50)
        layout.addWidget(username)
        layout.addWidget(password)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        layout.setAlignment(Qt.AlignCenter)

        screen.setLayout(layout)
        return screen

    def login_user(self, email, password):
        if not email or not password:
            print("Vui lòng điền đầy đủ thông tin!")
            return

        user = verify_user_credentials(email, password)
        if user:
            print("Đăng nhập thành công!")
            username = user['username']  # Lấy tên người dùng
            user_email = user['email']
            user_id= user['id']


            # Mở cửa sổ chính và truyền username
            self.open_main_window(username,user_email,user_id)
        else:
            print("Thông tin đăng nhập sai!")
            QMessageBox.warning(self, "Đăng nhập", "Thông tin đăng nhập sai!")

    def create_register_screen(self):
        screen = QWidget(self)
        layout = QVBoxLayout()

        logo = QLabel("DL ECOTECH PIONEERS", self)
        logo.setFont(QFont("Arial", 30, QFont.Bold))
        logo.setStyleSheet("color: #FF5722;")
        logo.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Tạo tài khoản mới", self)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #FF7043;")
        subtitle.setAlignment(Qt.AlignCenter)

        username = QLineEdit(self)
        username.setPlaceholderText("Tên người dùng")
        username.setFont(QFont("Arial", 12))

        email = QLineEdit(self)
        email.setPlaceholderText("Email")
        email.setFont(QFont("Arial", 12))

        password = QLineEdit(self)
        password.setPlaceholderText("Mật khẩu")
        password.setFont(QFont("Arial", 12))
        password.setEchoMode(QLineEdit.Password)

        back_button = QPushButton("Quay lại", self)
        back_button.setFont(QFont("Arial", 14))
        back_button.setStyleSheet(""" 
            QPushButton { 
                border: 2px solid transparent; 
                border-radius: 15px; 
                color: black; 
                background: #FFEBEE; 
                height: 40px; 
            }
            QPushButton:hover { 
                background: #FFCDD2; 
            }
        """)
        back_button.clicked.connect(self.show_login_screen)

        register_button = QPushButton("Đăng ký", self)
        register_button.setFont(QFont("Arial", 14))
        register_button.setStyleSheet(""" 
            QPushButton { 
                border: 2px solid transparent; 
                border-radius: 15px; 
                color: white; 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF5722, stop:1 #FF9800); 
                height: 40px; 
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF7043, stop:1 #FFB74D); 
            }
        """)
        register_button.clicked.connect(lambda: self.register_user_to_db(username.text(), email.text(), password.text()))

        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(50)
        layout.addWidget(username)
        layout.addWidget(email)
        layout.addWidget(password)
        layout.addWidget(register_button)
        layout.addWidget(back_button)
        layout.setAlignment(Qt.AlignCenter)

        screen.setLayout(layout)
        return screen

    def show_register_screen(self):
        self.stacked_widget.setCurrentWidget(self.register_screen)

    def show_login_screen(self):
        self.stacked_widget.setCurrentWidget(self.login_screen)

    def register_user_to_db(self, username, email, password):
        # Đăng ký người dùng vào Firebase
        if not username or not email or not password:
            print("Vui lòng điền đầy đủ thông tin!")
            return
        if register_user(username, email, password):
            print("Đăng ký thành công!")
            self.show_login_screen()
        else:
            print("Lỗi đăng ký. Vui lòng thử lại!")

    def open_main_window(self, username,user_email,user_id):
        # Đóng cửa sổ đăng nhập hiện tại
        self.close()

        # Mở cửa sổ chính và truyền username
        self.main_window = FruitDiseaseClassifierApp()
        self.main_window.set_user_name(username)
        self.main_window.set_user_email(user_email)
        self.main_window.set_user_id(user_id)
        self.main_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
