import pygame
import sys
import random
import os

pygame.init()
icon = pygame.image.load("icon.png")
pygame.display.set_icon(icon)


def load_and_scale_bg(image_path, default_color, size):
    """Загружает и масштабирует фоновое изображение под указанный размер"""
    try:
        bg = pygame.image.load(image_path)
        bg = pygame.transform.smoothscale(bg, size)  # Плавное масштабирование
        return bg
    except Exception:
        bg = pygame.Surface(size)
        bg.fill(default_color)
        return bg


# Начальные настройки
WIDTH, HEIGHT = 1400, 800
FULLSCREEN = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Время приключений — Карточные Войны")

FONT = pygame.font.SysFont("arial", 20)
BIGFONT = pygame.font.SysFont("arial", 40)
SMALLFONT = pygame.font.SysFont("arial", 16)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 180, 50)
BLUE = (50, 50, 200)
DARKGRAY = (40, 40, 40)

# Загрузка фонов с масштабированием
menu_bg = load_and_scale_bg("images/menu_background.png", DARKGRAY, (WIDTH, HEIGHT))
game_bg = load_and_scale_bg("images/game_background.png", (30, 60, 30), (WIDTH, HEIGHT))
pause_bg = load_and_scale_bg("images/pause_background.png", (0, 0, 0, 180), (WIDTH, HEIGHT))

# Загрузка музыки
music_files = []
current_music_index = 0
try:
    music_folder = "music"
    if os.path.exists(music_folder):
        music_files = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.ogg', '.wav'))]
        if music_files:
            pygame.mixer.music.load(os.path.join(music_folder, music_files[current_music_index]))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Не удалось загрузить музыку: {e}")


def wrap_text(text, font, max_width):
    """Перенос текста на несколько строк, если он не помещается в max_width"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.callback()

    def draw(self, surface):
        color = (180, 180, 180) if self.hovered else (140, 140, 140)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surf = FONT.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Slider:
    def __init__(self, rect, min_val, max_val, start_val, callback):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.callback = callback
        self.dragging = False
        self.handle_radius = 10
        self.handle_x = self.get_handle_x()

    def get_handle_x(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if (mx - self.handle_x) ** 2 + (my - (self.rect.centery)) ** 2 <= self.handle_radius ** 2:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx = event.pos[0]
                mx = max(self.rect.x, min(mx, self.rect.x + self.rect.width))
                self.handle_x = mx
                ratio = (self.handle_x - self.rect.x) / self.rect.width
                self.value = self.min_val + ratio * (self.max_val - self.min_val)
                self.callback(self.value)

    def draw(self, surface):
        pygame.draw.line(surface, WHITE, (self.rect.x, self.rect.centery),
                         (self.rect.x + self.rect.width, self.rect.centery), 4)
        pygame.draw.circle(surface, BLUE, (self.handle_x, self.rect.centery), self.handle_radius)
        val_text = FONT.render(f"{int(self.value * 100)}%", True, WHITE)
        surface.blit(val_text, (self.rect.right + 10, self.rect.centery - val_text.get_height() // 2))


# === Загрузка изображений карт ===
card_images = {}
cards_folder = "cards"
if os.path.exists(cards_folder):
    for filename in os.listdir(cards_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0].lower()
            img_path = os.path.join(cards_folder, filename)
            try:
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.smoothscale(img, (100, 140))
                card_images[name] = img
            except Exception as e:
                print(f"Ошибка загрузки изображения карты {filename}: {e}")


class Card:
    WIDTH = 100
    HEIGHT = 140

    def __init__(self, name, attack, cost):
        self.name = name
        self.attack = attack
        self.cost = cost
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.selected = False
        self.hovered = False
        self.image = card_images.get(self.name.lower(), None)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

    def draw(self, surface, pos):
        self.rect.topleft = pos
        if self.image:
            surface.blit(self.image, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 2)
        else:
            base_color = WHITE
            if self.hovered:
                base_color = (255, 255, 210)
            pygame.draw.rect(surface, base_color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 2)

        if self.selected:
            pygame.draw.rect(surface, BLUE, self.rect, 3)

        name_font = pygame.font.SysFont("arial", 14, bold=True)
        max_width = self.WIDTH - 10

        lines = wrap_text(self.name, name_font, max_width)
        y_offset = 10

        for line in lines:
            name_surf = name_font.render(line, True, BLACK)
            name_rect = name_surf.get_rect(centerx=self.rect.centerx, top=self.rect.y + y_offset - 50)
            surface.blit(name_surf, name_rect)
            y_offset += name_surf.get_height() + 2
            if y_offset > 40:
                break

        stats_font = pygame.font.SysFont("arial", 12)
        cost_surf = stats_font.render(f"Стоимость: {self.cost}", True, BLUE)
        atk_surf = stats_font.render(f"Атк: {self.attack}", True, RED)

        surface.blit(cost_surf, (self.rect.x + 5, self.rect.bottom + 12))
        surface.blit(atk_surf, (self.rect.x + 5, self.rect.bottom + 0))


def create_deck():
    cards = [
        Card("Деревяшка", 2, 1),
        Card("Пламенная Принцесса", 4, 3),
        Card("Финн", 3, 3),
        Card("Джейк", 5, 5),
        Card("Ледяной Король", 3, 4),
        Card("Принцесса Бубльгум", 2, 3),
        Card("Лич", 6, 6),
        Card("БМО", 1, 2),
        Card("Леди Ливнерог", 3, 4),
        Card("Марселин", 4, 3),
        Card("Волшебный Меч", 0, 2),
        Card("Огненный Шар", 3, 3),
        Card("Зелье Исцеления", 0, 2),
        Card("Хансон Абадир", 4, 3),
        Card("Гантер", 1, 1),
        Card("Граф Лимонохват", 2, 3),
        Card("Король Ооо", 2, 1),
        Card("Терпеливая Святая Пим", 3, 3),
        Card("ГОЛБ", 4, 5),
        Card("Волшебный Чел", 3, 2),
        Card("Мятный лакей", 2, 2),
    ]
    deck = cards * 3
    random.shuffle(deck)
    return deck


class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"
        self.full_deck = create_deck()
        self.deck = self.full_deck.copy()
        self.player_hand = []
        self.enemy_hand = []
        self.player2_hand = []
        self.buttons = []
        self.mode_buttons = []
        self.pause_buttons = []
        self.settings_menu_buttons = []
        self.settings_pause_buttons = []
        self.selected_card = None
        self.player_mana = 5
        self.enemy_mana = 5
        self.player_health = 20
        self.enemy_health = 20
        self.player2_mana = 5
        self.player2_health = 20
        self.turn = "player"
        self.message = ""
        self.bot_difficulty = "Средний"
        self.sound_on = True
        self.volume = 0.5
        self.turn_number = 1
        self.game_mode = None
        self.fullscreen = False
        self.sword_buff_active = False

        self.volume_slider = Slider((WIDTH // 2 - 150, 550, 300, 20), 0.0, 1.0, self.volume, self.set_volume)

        self.create_menu_buttons()
        self.create_mode_buttons()
        self.create_pause_buttons()
        self.create_settings_menu_buttons()
        self.create_settings_pause_buttons()

        self.skip_turn_button = Button((WIDTH - 220, HEIGHT // 2 - 30, 180, 60), "Пропустить ход", self.skip_turn)
        self.pause_button = Button((WIDTH - 220, HEIGHT // 2 - 100, 180, 60), "Пауза", self.toggle_pause)

        self.prev_music_button = Button((WIDTH // 2 - 180, 400, 50, 30), "<", self.prev_music)
        self.next_music_button = Button((WIDTH // 2 + 130, 400, 50, 30), ">", self.next_music)

    def reload_backgrounds(self):
        """Перезагружает фоны с новыми размерами"""
        global menu_bg, game_bg, pause_bg
        menu_bg = load_and_scale_bg("images/menu_background.png", DARKGRAY, (WIDTH, HEIGHT))
        game_bg = load_and_scale_bg("images/game_background.png", (30, 60, 30), (WIDTH, HEIGHT))
        pause_bg = load_and_scale_bg("images/pause_background.png", (0, 0, 0, 180), (WIDTH, HEIGHT))

    def toggle_fullscreen(self):
        global screen, WIDTH, HEIGHT, FULLSCREEN
        self.fullscreen = not self.fullscreen
        FULLSCREEN = self.fullscreen

        if self.fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            info = pygame.display.Info()
            WIDTH, HEIGHT = info.current_w, info.current_h
        else:
            WIDTH, HEIGHT = 1400, 800
            screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.reload_backgrounds()
        self.update_ui_positions()

    def update_ui_positions(self):
        """Обновляет позиции UI элементов при изменении размера экрана"""
        self.skip_turn_button.rect = pygame.Rect(WIDTH - 220, HEIGHT // 2 - 30, 180, 60)
        self.pause_button.rect = pygame.Rect(WIDTH - 220, HEIGHT // 2 - 100, 180, 60)

        # Пересоздаем кнопки меню с новыми позициями
        self.create_menu_buttons()
        self.create_mode_buttons()
        self.create_pause_buttons()
        self.create_settings_menu_buttons()
        self.create_settings_pause_buttons()

        # Обновляем позицию слайдера громкости
        self.volume_slider.rect = pygame.Rect(WIDTH // 2 - 150, 550, 300, 20)
        self.prev_music_button.rect = pygame.Rect(WIDTH // 2 - 180, 400, 50, 30)
        self.next_music_button.rect = pygame.Rect(WIDTH // 2 + 130, 400, 50, 30)

    def set_volume(self, val):
        self.volume = val
        pygame.mixer.music.set_volume(val)

    def create_menu_buttons(self):
        self.buttons = []
        self.buttons.append(Button((WIDTH // 2 - 150, 300, 300, 60), "Играть", self.goto_mode_select))
        self.buttons.append(Button((WIDTH // 2 - 150, 390, 300, 60), "Настройки", self.goto_settings_menu))
        self.buttons.append(Button((WIDTH // 2 - 150, 480, 300, 60), "Выход", self.quit_game))

    def create_mode_buttons(self):
        self.mode_buttons = []
        self.mode_buttons.append(Button((WIDTH // 2 - 150, 300, 300, 60), "Против бота", self.start_game_bot))
        self.mode_buttons.append(
            Button((WIDTH // 2 - 150, 390, 300, 60), "2 игрока на одном устройстве", self.start_game_2players))
        self.mode_buttons.append(Button((WIDTH // 2 - 150, 480, 300, 60), "Назад", self.back_to_menu))

    def create_pause_buttons(self):
        self.pause_buttons = []
        self.pause_buttons.append(Button((WIDTH // 2 - 150, 300, 300, 60), "Продолжить", self.resume_game))
        self.pause_buttons.append(Button((WIDTH // 2 - 150, 370, 300, 60), "Настройки", self.goto_settings_pause))
        self.pause_buttons.append(Button((WIDTH // 2 - 150, 440, 300, 60), "Выйти в меню", self.exit_to_menu))

    def create_settings_menu_buttons(self):
        self.settings_menu_buttons = []
        self.settings_menu_buttons.append(
            Button((WIDTH // 2 - 150, 400, 300, 60), f"Сложность бота: {self.bot_difficulty}",
                   self.toggle_bot_difficulty))
        self.settings_menu_buttons.append(Button((WIDTH // 2 - 150, 470, 300, 60),
                                                 "Полный экран: Вкл" if self.fullscreen else "Полный экран: Выкл",
                                                 self.toggle_fullscreen))
        self.settings_menu_buttons.append(Button((WIDTH // 2 - 150, 540, 300, 60), "Назад", self.back_to_menu))

    def create_settings_pause_buttons(self):
        self.settings_pause_buttons = []
        self.settings_pause_buttons.append(
            Button((WIDTH // 2 - 150, 400, 300, 60), f"Сложность бота: {self.bot_difficulty}",
                   self.toggle_bot_difficulty))
        self.settings_pause_buttons.append(Button((WIDTH // 2 - 150, 470, 300, 60),
                                                  "Полный экран: Вкл" if self.fullscreen else "Полный экран: Выкл",
                                                  self.toggle_fullscreen))
        self.settings_pause_buttons.append(Button((WIDTH // 2 - 150, 540, 300, 60), "Назад", self.back_to_pause))

    def toggle_bot_difficulty(self):
        if self.bot_difficulty == "Средний":
            self.bot_difficulty = "Лёгкий"
        elif self.bot_difficulty == "Лёгкий":
            self.bot_difficulty = "Сложный"
        else:
            self.bot_difficulty = "Средний"

        if self.state == "settings_menu":
            self.settings_menu_buttons[0].text = f"Сложность бота: {self.bot_difficulty}"
        elif self.state == "settings_pause":
            self.settings_pause_buttons[0].text = f"Сложность бота: {self.bot_difficulty}"

    def goto_mode_select(self):
        self.state = "mode_select"

    def start_game_bot(self):
        self.game_mode = 'bot'
        self.start_game_common()

    def start_game_2players(self):
        self.game_mode = '2players'
        self.start_game_common()

    def start_game_common(self):
        self.state = "game"
        self.deck = self.full_deck.copy()
        random.shuffle(self.deck)
        self.player_hand = [self.draw_card() for _ in range(5)]
        self.enemy_hand = [self.draw_card() for _ in range(5)]
        self.player2_hand = [self.draw_card() for _ in range(5)]
        self.player_health = 20
        self.enemy_health = 20
        self.player2_health = 20
        self.player_mana = 5
        self.enemy_mana = 5
        self.player2_mana = 5
        self.turn_number = 1
        self.selected_card = None
        self.message = ""
        self.sword_buff_active = False
        if self.game_mode == 'bot':
            self.turn = "player"
        else:
            self.turn = "player"

    def goto_settings_menu(self):
        self.state = "settings_menu"

    def goto_settings_pause(self):
        self.state = "settings_pause"

    def back_to_menu(self):
        self.state = "menu"
        self.create_menu_buttons()

    def back_to_pause(self):
        self.state = "pause"
        self.create_pause_buttons()

    def quit_game(self):
        self.running = False

    def resume_game(self):
        self.state = "game"

    def exit_to_menu(self):
        self.state = "menu"
        self.create_menu_buttons()

    def draw_card(self):
        if not self.deck:
            self.deck = self.full_deck.copy()
            random.shuffle(self.deck)
            self.message = "Колода перемешана заново!"
        return self.deck.pop()

    def player_play_card(self, card_index):
        if self.turn != "player":
            self.message = "Сейчас не ваш ход!"
            return
        if card_index < 0 or card_index >= len(self.player_hand):
            return
        card = self.player_hand[card_index]
        if card.cost > self.player_mana:
            self.message = "Недостаточно маны!"
            return
        self.player_mana -= card.cost

        name_lower = card.name.lower()

        # Обработка Зелья Исцеления
        if "зелье" in name_lower:
            heal_amount = 2
            max_health = 20
            self.player_health = min(self.player_health + heal_amount, max_health)
            self.message = f"Вы использовали {card.name} и восстановили {heal_amount} здоровья."
            self.player_hand.pop(card_index)
            self.player_hand.append(self.draw_card())
            self.end_turn()
            return

        # Обработка Волшебного Меча
        if "меч" in name_lower:
            self.sword_buff_active = True
            self.message = f"Вы использовали {card.name}. Следующая карта получит +1 к урону."
            self.player_hand.pop(card_index)
            self.player_hand.append(self.draw_card())
            self.end_turn()
            return

        # Обычная карта
        damage = card.attack
        if self.sword_buff_active:
            damage += 1
            self.sword_buff_active = False

        if self.game_mode == 'bot':
            self.enemy_health -= damage
        else:
            self.player2_health -= damage

        self.message = f"Вы сыграли карту {card.name} и нанесли {damage} урона."
        self.player_hand.pop(card_index)
        self.player_hand.append(self.draw_card())
        self.end_turn()

    def player2_play_card(self, card_index):
        if self.turn != "player2":
            self.message = "Сейчас не ваш ход!"
            return
        if card_index < 0 or card_index >= len(self.player2_hand):
            return
        card = self.player2_hand[card_index]
        if card.cost > self.player2_mana:
            self.message = "Недостаточно маны!"
            return
        self.player2_mana -= card.cost

        damage = card.attack

        if card.attack == 0 and card.health > 0:
            max_health = 20
            self.player2_health = min(self.player2_health + card.health, max_health)

        self.player_health -= damage

        self.message = f"Игрок 2 сыграл карту {card.name} и нанёс {damage} урона."
        self.player2_hand.pop(card_index)
        self.player2_hand.append(self.draw_card())
        self.end_turn()

    def enemy_turn(self):
        playable_cards = [c for c in self.enemy_hand if c.cost <= self.enemy_mana]
        if not playable_cards:
            self.message = "Враг пропускает ход."
            self.enemy_mana = min(self.enemy_mana + self.turn_number, 10)
            self.turn = "player"
            self.turn_number += 1
            return

        if self.bot_difficulty == "Лёгкий":
            card = min(playable_cards, key=lambda c: c.cost)
        elif self.bot_difficulty == "Средний":
            card = max(playable_cards, key=lambda c: c.attack)
        else:
            card = max(playable_cards, key=lambda c: (c.attack / max(c.cost, 1)))

        self.enemy_mana -= card.cost
        damage = max(card.attack - 1, 0)
        self.player_health -= damage
        if card.attack == 0 and card.health > 0:
            self.enemy_health += card.health
        self.message = f"Враг сыграл карту {card.name} и нанес {damage} урона."
        self.enemy_hand.remove(card)
        self.enemy_hand.append(self.draw_card())
        self.turn = "player"
        self.player_mana = min(self.player_mana + self.turn_number, 10)
        self.turn_number += 1

    def end_turn(self):
        if self.game_mode == 'bot':
            if self.turn == "player":
                self.turn = "enemy"
                self.enemy_mana = min(self.enemy_mana + self.turn_number, 10)
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
            elif self.turn == "enemy":
                self.turn = "player"
                self.player_mana = min(self.player_mana + self.turn_number, 10)
                self.turn_number += 1
        else:
            if self.turn == "player":
                self.turn = "player2"
                self.player2_mana = min(self.player2_mana + self.turn_number, 10)
            elif self.turn == "player2":
                self.turn = "player"
                self.player_mana = min(self.player_mana + self.turn_number, 10)
                self.turn_number += 1

    def skip_turn(self):
        if self.turn is None:
            return
        if self.game_mode == 'bot':
            if self.turn == "player":
                self.message = "Вы пропускаете ход."
                self.turn = "enemy"
                self.enemy_mana = min(self.enemy_mana + self.turn_number, 10)
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
            elif self.turn == "enemy":
                self.message = "Враг пропускает ход."
                self.turn = "player"
                self.player_mana = min(self.player_mana + self.turn_number, 10)
                self.turn_number += 1
        else:
            if self.turn == "player":
                self.message = "Игрок 1 пропускает ход."
                self.turn = "player2"
                self.player2_mana = min(self.player2_mana + self.turn_number, 10)
            elif self.turn == "player2":
                self.message = "Игрок 2 пропускает ход."
                self.turn = "player"
                self.player_mana = min(self.player_mana + self.turn_number, 10)
                self.turn_number += 1

    def prev_music(self):
        global current_music_index
        if music_files:
            current_music_index = (current_music_index - 1) % len(music_files)
            pygame.mixer.music.load(os.path.join("music", music_files[current_music_index]))
            pygame.mixer.music.play(-1)

    def next_music(self):
        global current_music_index
        if music_files:
            current_music_index = (current_music_index + 1) % len(music_files)
            pygame.mixer.music.load(os.path.join("music", music_files[current_music_index]))
            pygame.mixer.music.play(-1)

    def toggle_pause(self):
        if self.state == "game":
            self.state = "pause"
            self.create_pause_buttons()
        elif self.state == "pause":
            self.state = "game"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == "menu":
                for btn in self.buttons:
                    btn.handle_event(event)
            elif self.state == "mode_select":
                for btn in self.mode_buttons:
                    btn.handle_event(event)
            elif self.state == "game":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.toggle_pause()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    if self.pause_button.rect.collidepoint(mx, my):
                        self.pause_button.handle_event(event)
                        continue

                    if self.skip_turn_button.rect.collidepoint(mx, my):
                        self.skip_turn_button.handle_event(event)
                        continue

                    start_x = 100
                    gap = 30
                    if self.game_mode == 'bot':
                        y_player = HEIGHT - Card.HEIGHT - 70
                        for i, card in enumerate(self.player_hand):
                            rect = pygame.Rect(start_x + i * (Card.WIDTH + gap), y_player, Card.WIDTH, Card.HEIGHT)
                            if rect.collidepoint(mx, my):
                                self.player_play_card(i)
                                break
                    else:
                        y_player1 = HEIGHT - Card.HEIGHT - 70
                        y_player2 = 70
                        if self.turn == "player":
                            for i, card in enumerate(self.player_hand):
                                rect = pygame.Rect(start_x + i * (Card.WIDTH + gap), y_player1, Card.WIDTH, Card.HEIGHT)
                                if rect.collidepoint(mx, my):
                                    self.player_play_card(i)
                                    break
                        elif self.turn == "player2":
                            for i, card in enumerate(self.player2_hand):
                                rect = pygame.Rect(start_x + i * (Card.WIDTH + gap), y_player2, Card.WIDTH, Card.HEIGHT)
                                if rect.collidepoint(mx, my):
                                    self.player2_play_card(i)
                                    break
                elif event.type == pygame.USEREVENT + 1:
                    if self.state == "game" and self.turn == "enemy" and self.game_mode == 'bot':
                        self.enemy_turn()
                        pygame.time.set_timer(pygame.USEREVENT + 1, 0)

                if event.type == pygame.MOUSEMOTION:
                    self.pause_button.handle_event(event)
                    self.skip_turn_button.handle_event(event)

                if self.game_mode == 'bot':
                    for card in self.player_hand + self.enemy_hand:
                        card.handle_event(event)
                else:
                    for card in self.player_hand + self.player2_hand:
                        card.handle_event(event)

            elif self.state == "pause":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.toggle_pause()
                for btn in self.pause_buttons:
                    btn.handle_event(event)

            elif self.state == "settings_menu":
                for btn in self.settings_menu_buttons:
                    btn.handle_event(event)
                self.volume_slider.handle_event(event)
                self.prev_music_button.handle_event(event)
                self.next_music_button.handle_event(event)

            elif self.state == "settings_pause":
                for btn in self.settings_pause_buttons:
                    btn.handle_event(event)
                self.volume_slider.handle_event(event)
                self.prev_music_button.handle_event(event)
                self.next_music_button.handle_event(event)

    def draw_menu(self):
        screen.blit(menu_bg, (0, 0))
        title = BIGFONT.render("Время приключений — Карточные Войны", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))
        for btn in self.buttons:
            btn.draw(screen)

    def draw_mode_select(self):
        screen.blit(menu_bg, (0, 0))
        title = BIGFONT.render("Выберите режим игры", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))
        for btn in self.mode_buttons:
            btn.draw(screen)

    def draw_game(self):
        screen.blit(game_bg, (0, 0))

        start_x = 100
        gap = 30
        if self.game_mode == 'bot':
            y_enemy = 70
            for i, card in enumerate(self.enemy_hand):
                pos = (start_x + i * (Card.WIDTH + gap), y_enemy)
                card.draw(screen, pos)
            y_player = HEIGHT - Card.HEIGHT - 70
            for i, card in enumerate(self.player_hand):
                pos = (start_x + i * (Card.WIDTH + gap), y_player)
                card.draw(screen, pos)

            mana_text = FONT.render(f"Мана: {self.player_mana}", True, BLUE)
            screen.blit(mana_text, (10, HEIGHT - 60))

            player_hp_text = FONT.render(f"Здоровье игрока: {self.player_health}", True, GREEN)
            enemy_hp_text = FONT.render(f"Здоровье врага: {self.enemy_health}", True, RED)
            screen.blit(player_hp_text, (10, HEIGHT - 90))
            screen.blit(enemy_hp_text, (10, 10))

            turn_text = FONT.render(f"Ход: {'Игрок' if self.turn == 'player' else 'Враг'}", True, WHITE)
            screen.blit(turn_text, (WIDTH - 150, 10))

        else:
            y_player1 = HEIGHT - Card.HEIGHT - 70
            y_player2 = 70
            for i, card in enumerate(self.player_hand):
                pos = (start_x + i * (Card.WIDTH + gap), y_player1)
                card.draw(screen, pos)
            for i, card in enumerate(self.player2_hand):
                pos = (start_x + i * (Card.WIDTH + gap), y_player2)
                card.draw(screen, pos)

            mana_text_1 = FONT.render(f"Мана Игрока 1: {self.player_mana}", True, BLUE)
            mana_text_2 = FONT.render(f"Мана Игрока 2: {self.player2_mana}", True, BLUE)
            screen.blit(mana_text_1, (WIDTH - 250, 10))
            screen.blit(mana_text_2, (10, 10))

            hp_text_1 = FONT.render(f"Здоровье Игрока 1: {self.player_health}", True, GREEN)
            hp_text_2 = FONT.render(f"Здоровье Игрока 2: {self.player2_health}", True, GREEN)
            screen.blit(hp_text_1, (WIDTH - 250, 40))
            screen.blit(hp_text_2, (10, 40))

            turn_text = FONT.render(f"Ход: {'Игрок 1' if self.turn == 'player' else 'Игрок 2'}", True, WHITE)
            screen.blit(turn_text, (WIDTH // 2 - 50, HEIGHT // 2 - 20))

        msg = FONT.render(self.message, True, WHITE)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT - 60))

        if self.state == "game":
            self.pause_button.draw(screen)
            if self.turn in ("player", "player2", "enemy"):
                self.skip_turn_button.draw(screen)

        if self.game_mode == 'bot':
            if self.player_health <= 0:
                self.message = "Вы проиграли! Нажмите на паузу чтобы выйти."
                lose_text = BIGFONT.render("Поражение!", True, RED)
                screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2))
                self.turn = None
            if self.enemy_health <= 0:
                self.message = "Вы выиграли! Нажмите на паузу чтобы выйти."
                win_text = BIGFONT.render("Победа!", True, GREEN)
                screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2))
                self.turn = None
        else:
            if self.player_health <= 0:
                self.message = "Игрок 1 проиграл! Нажмите на паузу чтобы выйти."
                lose_text = BIGFONT.render("Поражение Игрока 1!", True, RED)
                screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2))
                self.turn = None
            if self.player2_health <= 0:
                self.message = "Игрок 2 проиграл! Нажмите на паузу чтобы выйти."
                lose_text = BIGFONT.render("Поражение Игрока 2!", True, RED)
                screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2))
                self.turn = None

    def draw_pause(self):
        screen.blit(game_bg, (0, 0))
        screen.blit(pause_bg, (0, 0))

        title = BIGFONT.render("Пауза", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for btn in self.pause_buttons:
            btn.draw(screen)

    def draw_settings_menu(self):
        screen.blit(menu_bg, (0, 0))
        title = BIGFONT.render("Настройки (Меню)", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        if music_files:
            music_name = music_files[current_music_index]
            if len(music_name) > 20:
                music_name = music_name[:17] + "..."
            music_text = FONT.render(f"Трек: {music_name}", True, WHITE)
            screen.blit(music_text, (WIDTH // 2 - music_text.get_width() // 2, 200))

            self.prev_music_button.rect.topleft = (WIDTH // 2 - 180, 250)
            self.next_music_button.rect.topleft = (WIDTH // 2 + 130, 250)
            self.prev_music_button.draw(screen)
            self.next_music_button.draw(screen)

            vol_text = FONT.render("Громкость:", True, WHITE)
            screen.blit(vol_text, (WIDTH // 2 - 150, 300))
            self.volume_slider.rect.topleft = (WIDTH // 2 - 150, 330)
            self.volume_slider.draw(screen)

        for btn in self.settings_menu_buttons:
            btn.draw(screen)

    def draw_settings_pause(self):
        screen.blit(pause_bg, (0, 0))
        title = BIGFONT.render("Настройки (Пауза)", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        if music_files:
            music_name = music_files[current_music_index]
            if len(music_name) > 20:
                music_name = music_name[:17] + "..."
            music_text = FONT.render(f"Трек: {music_name}", True, WHITE)
            screen.blit(music_text, (WIDTH // 2 - music_text.get_width() // 2, 200))

            self.prev_music_button.rect.topleft = (WIDTH // 2 - 180, 250)
            self.next_music_button.rect.topleft = (WIDTH // 2 + 130, 250)
            self.prev_music_button.draw(screen)
            self.next_music_button.draw(screen)

            vol_text = FONT.render("Громкость:", True, WHITE)
            screen.blit(vol_text, (WIDTH // 2 - 150, 300))
            self.volume_slider.rect.topleft = (WIDTH // 2 - 150, 330)
            self.volume_slider.draw(screen)

        for btn in self.settings_pause_buttons:
            btn.draw(screen)

    def run(self):
        while self.running:
            self.handle_events()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "mode_select":
                self.draw_mode_select()
            elif self.state == "game":
                self.draw_game()
            elif self.state == "pause":
                self.draw_pause()
            elif self.state == "settings_menu":
                self.draw_settings_menu()
            elif self.state == "settings_pause":
                self.draw_settings_pause()

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()