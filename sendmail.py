import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


def send_email(sender_email, receiver_email, subject, message, attachment_path=None):
    """
    Hàm gửi email qua Gmail, hỗ trợ gửi tệp đính kèm.

    :param sender_email: Email người gửi
    :param receiver_email: Email người nhận
    :param subject: Tiêu đề email
    :param message: Nội dung email
    :param attachment_path: Đường dẫn tới tệp đính kèm (nếu có)
    :return: None
    """
    # Mật khẩu ứng dụng Gmail
    app_password = "wlar homb nauv mpoa"

    try:
        # Tạo email với MIME hỗ trợ định dạng Unicode
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Thêm nội dung email
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        # Thêm tệp đính kèm (nếu có)
        if attachment_path and os.path.isfile(attachment_path):
            with open(attachment_path, 'rb') as attachment_file:
                # Tạo đối tượng MIMEBase cho tệp
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )
                msg.attach(part)
        elif attachment_path:
            print(f"Tệp không tồn tại: {attachment_path}")

        # Kết nối đến máy chủ SMTP của Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Bắt đầu kết nối bảo mật TLS

        # Đăng nhập vào tài khoản Gmail
        server.login(sender_email, app_password)

        # Gửi email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email đã được gửi tới {receiver_email} thành công!")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        # Đóng kết nối
        try:
            server.quit()
        except:
            pass


if __name__ == "__main__":
    # Lấy thông tin từ người dùng
    sender_email = input("SENDER EMAIL: ").strip()
    receiver_email = input("RECEIVER EMAIL: ").strip()
    subject = input("SUBJECT: ").strip()
    message = input("MESSAGE: ").strip()
    attachment_path = input("ATTACHMENT PATH (optional): ").strip()

    # Gọi hàm gửi email
    send_email(sender_email, receiver_email, subject, message, attachment_path if attachment_path else None)
