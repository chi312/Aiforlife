import pygame
from pygame.locals import *

# Khởi tạo pygame
pygame.init()

# Kích thước cửa sổ.
WIDTH, HEIGHT = 400, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chuông thông báo MP3")

# Màu sắc
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

# Font chữ
font = pygame.font.Font(None, 36)

# Button
button_rect = pygame.Rect(150, 120, 100, 50)

# Âm thanh MP3
pygame.mixer.init()
pygame.mixer.music.load("quaymanh.mp3")

running = True
while running:
    screen.fill(WHITE)

    # Vẽ button
    pygame.draw.rect(screen, GRAY, button_rect)
    text = font.render("Chuông", True, BLACK)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)

    # Vòng lặp sự kiện
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):  # Kiểm tra nhấn vào button
                pygame.mixer.music.play()  # Phát âm thanh MP3

    # Cập nhật màn hình
    pygame.display.flip()

# Kết thúc pygame
pygame.quit()
