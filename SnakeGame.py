import pygame
import random
import math
import sys
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
BASE_SNAKE_SPEED = 10  # Base speed that will be adjusted based on difficulty

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (40, 40, 40)
GREEN = (46, 204, 113)
LIGHT_GREEN = (88, 214, 141)
DARK_GREEN = (39, 174, 96)
RED = (231, 76, 60)
GOLD = (241, 196, 15)
BLUE = (52, 152, 219)
LIGHT_BLUE = (133, 193, 233)
PURPLE = (155, 89, 182)

# Direction enum
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Game difficulty enum
class Difficulty(Enum):
    EASY = 8
    MEDIUM = 12
    HARD = 16

# Food types
class FoodType(Enum):
    REGULAR = 1  # Regular food (red)
    BONUS = 2    # Bonus food (gold) - worth more points but disappears quickly
    SPEED = 3    # Speed food (blue) - temporarily increases snake speed
    SLOW = 4     # Slow food (purple) - temporarily decreases snake speed

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Snake Game")
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.title_font = pygame.font.SysFont('Arial', 50, bold=True)
        self.menu_font = pygame.font.SysFont('Arial', 30)
        self.game_font = pygame.font.SysFont('Arial', 25)
        self.small_font = pygame.font.SysFont('Arial', 20)
        
        # Background pattern
        self.bg_pattern = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.bg_pattern.fill(BLACK)
        pygame.draw.rect(self.bg_pattern, DARK_GRAY, (1, 1, GRID_SIZE-2, GRID_SIZE-2))
        
        # Load sounds
        pygame.mixer.init()
        try:
            self.eat_sound = pygame.mixer.Sound("eat.wav")
            self.crash_sound = pygame.mixer.Sound("crash.wav")
            self.bonus_sound = pygame.mixer.Sound("bonus.wav")
        except:
            # If sound files not found, create placeholders
            self.eat_sound = pygame.mixer.Sound(buffer=bytes(bytearray([0])))
            self.crash_sound = pygame.mixer.Sound(buffer=bytes(bytearray([0])))
            self.bonus_sound = pygame.mixer.Sound(buffer=bytes(bytearray([0])))
            print("Sound files not found. Continuing without sound.")
        
        # Set default game settings
        self.difficulty = Difficulty.MEDIUM
        self.obstacles_enabled = False
        self.special_food_enabled = True
        
        # Initialize game variables
        self.speed_modifier = 1.0
        self.speed_effect_time = 0
        self.snake_positions = []
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.game_over = False
        self.paused = False
        self.foods = []
        self.obstacles = []
        self.high_score = 0
        
        # Start with menu
        self.game_state = "MENU"
        
    def reset_game(self):
        # Initialize snake in the middle of the screen
        center_x, center_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.snake_positions = [(center_x, center_y)]
        # Add a few initial segments
        for i in range(1, 3):
            self.snake_positions.append((center_x - i, center_y))
        
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        
        # Game variables
        self.score = 0
        self.game_over = False
        self.paused = False
        
        # Food variables
        self.foods = []
        self.add_food(FoodType.REGULAR)
        
        # Special effects
        self.speed_modifier = 1.0
        self.speed_effect_time = 0
        
        # Generate obstacles if enabled
        self.obstacles = []
        if self.obstacles_enabled:
            self.generate_obstacles()
    
    def generate_obstacles(self):
        num_obstacles = random.randint(5, 10)
        for _ in range(num_obstacles):
            # Create small obstacle clusters
            cluster_center = (random.randint(3, GRID_WIDTH-4), random.randint(3, GRID_HEIGHT-4))
            cluster_size = random.randint(1, 3)
            
            for dx in range(-cluster_size, cluster_size+1):
                for dy in range(-cluster_size, cluster_size+1):
                    # Create a somewhat random pattern
                    if random.random() < 0.6:
                        pos = (cluster_center[0] + dx, cluster_center[1] + dy)
                        # Ensure obstacles don't overlap with snake
                        if pos not in self.snake_positions and 0 <= pos[0] < GRID_WIDTH and 0 <= pos[1] < GRID_HEIGHT:
                            self.obstacles.append(pos)
    
    def add_food(self, food_type=None):
        if food_type is None:
            # If special food is enabled, occasionally spawn special food
            if self.special_food_enabled and random.random() < 0.2:
                food_type = random.choice([FoodType.BONUS, FoodType.SPEED, FoodType.SLOW])
            else:
                food_type = FoodType.REGULAR
        
        # Try to find a valid position for the food
        attempts = 0
        while attempts < 100:  # Prevent infinite loop
            pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if pos not in self.snake_positions and pos not in self.obstacles and pos not in [f[0] for f in self.foods]:
                # For bonus food, set a timer
                timer = 0
                if food_type == FoodType.BONUS:
                    timer = pygame.time.get_ticks() + 5000  # 5 seconds
                
                self.foods.append((pos, food_type, timer))
                break
            attempts += 1
    
    def handle_keys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if self.game_state == "MENU":
                    self.handle_menu_keys(event.key)
                elif self.game_state == "PLAYING":
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
                        elif event.key == pygame.K_m:
                            self.game_state = "MENU"
                        elif event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()
                    else:
                        self.handle_game_keys(event.key)
    
    def handle_menu_keys(self, key):
        if key == pygame.K_1 or key == pygame.K_KP1:
            self.difficulty = Difficulty.EASY
        elif key == pygame.K_2 or key == pygame.K_KP2:
            self.difficulty = Difficulty.MEDIUM
        elif key == pygame.K_3 or key == pygame.K_KP3:
            self.difficulty = Difficulty.HARD
        elif key == pygame.K_o:
            self.obstacles_enabled = not self.obstacles_enabled
        elif key == pygame.K_s:
            self.special_food_enabled = not self.special_food_enabled
        elif key == pygame.K_RETURN:
            self.game_state = "PLAYING"
            self.reset_game()
    
    def handle_game_keys(self, key):
        if key == pygame.K_p:
            self.paused = not self.paused
        elif key == pygame.K_UP and self.direction != Direction.DOWN:
            self.next_direction = Direction.UP
        elif key == pygame.K_DOWN and self.direction != Direction.UP:
            self.next_direction = Direction.DOWN
        elif key == pygame.K_LEFT and self.direction != Direction.RIGHT:
            self.next_direction = Direction.LEFT
        elif key == pygame.K_RIGHT and self.direction != Direction.LEFT:
            self.next_direction = Direction.RIGHT
    
    def update(self):
        if self.game_state != "PLAYING" or self.game_over or self.paused:
            return
        
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake_positions[0]
        dx, dy = self.direction.value
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)
        
        # Check for collisions with obstacles
        if new_head in self.obstacles:
            self.game_over = True
            self.crash_sound.play()
            return
        
        # Check for collision with self
        if new_head in self.snake_positions:
            self.game_over = True
            self.crash_sound.play()
            return
        
        # Move snake
        self.snake_positions.insert(0, new_head)
        
        # Check for food collisions
        ate_food = False
        for i, (food_pos, food_type, timer) in enumerate(self.foods):
            if new_head == food_pos:
                # Remove the food
                self.foods.pop(i)
                
                # Apply food effects
                if food_type == FoodType.REGULAR:
                    self.score += 10
                    self.eat_sound.play()
                elif food_type == FoodType.BONUS:
                    self.score += 50
                    self.bonus_sound.play()
                elif food_type == FoodType.SPEED:
                    self.speed_modifier = 1.5
                    self.speed_effect_time = pygame.time.get_ticks() + 5000  # 5 seconds
                    self.eat_sound.play()
                elif food_type == FoodType.SLOW:
                    self.speed_modifier = 0.7
                    self.speed_effect_time = pygame.time.get_ticks() + 5000  # 5 seconds
                    self.eat_sound.play()
                
                # Don't remove the tail when eating
                ate_food = True
                
                # Add a new food
                self.add_food()
                break
        
        # Remove tail if no food was eaten
        if not ate_food:
            self.snake_positions.pop()
        
        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
        
        # Check for expired bonus food
        current_time = pygame.time.get_ticks()
        self.foods = [(pos, type, timer) for pos, type, timer in self.foods if timer == 0 or timer > current_time]
        
        # Add new bonus food occasionally
        if self.special_food_enabled and random.random() < 0.005 and not any(f[1] == FoodType.BONUS for f in self.foods):
            self.add_food(FoodType.BONUS)
        
        # Check for speed effect expiration
        if self.speed_effect_time > 0 and current_time > self.speed_effect_time:
            self.speed_modifier = 1.0
            self.speed_effect_time = 0
    
    def draw_menu(self):
        self.screen.fill(BLACK)
        
        # Draw title
        title = self.title_font.render("ENHANCED SNAKE", True, GREEN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # Draw options
        y_pos = 150
        difficulty_text = f"Difficulty: "
        self.screen.blit(self.menu_font.render(difficulty_text, True, WHITE), (SCREEN_WIDTH//2 - 150, y_pos))
        
        # Draw difficulty options with the selected one highlighted
        easy_color = GOLD if self.difficulty == Difficulty.EASY else WHITE
        medium_color = GOLD if self.difficulty == Difficulty.MEDIUM else WHITE
        hard_color = GOLD if self.difficulty == Difficulty.HARD else WHITE
        
        self.screen.blit(self.menu_font.render("1. Easy", True, easy_color), (SCREEN_WIDTH//2 + 50, y_pos))
        y_pos += 40
        self.screen.blit(self.menu_font.render("2. Medium", True, medium_color), (SCREEN_WIDTH//2 + 50, y_pos))
        y_pos += 40
        self.screen.blit(self.menu_font.render("3. Hard", True, hard_color), (SCREEN_WIDTH//2 + 50, y_pos))
        y_pos += 60
        
        # Draw other options
        obstacles_text = f"Obstacles: {'ON' if self.obstacles_enabled else 'OFF'} (press O to toggle)"
        self.screen.blit(self.menu_font.render(obstacles_text, True, WHITE), (SCREEN_WIDTH//2 - 200, y_pos))
        y_pos += 40
        
        special_food_text = f"Special Food: {'ON' if self.special_food_enabled else 'OFF'} (press S to toggle)"
        self.screen.blit(self.menu_font.render(special_food_text, True, WHITE), (SCREEN_WIDTH//2 - 200, y_pos))
        y_pos += 80
        
        # Draw instructions
        start_text = "Press ENTER to Start"
        self.screen.blit(self.menu_font.render(start_text, True, GREEN), (SCREEN_WIDTH//2 - 100, y_pos))
        y_pos += 60
        
        controls_text = "Controls: Arrow Keys to move, P to pause"
        self.screen.blit(self.small_font.render(controls_text, True, WHITE), (SCREEN_WIDTH//2 - 180, y_pos))
        
        # Draw high score
        high_score_text = f"High Score: {self.high_score}"
        self.screen.blit(self.small_font.render(high_score_text, True, GOLD), (SCREEN_WIDTH - 200, 20))
    
    def draw_game(self):
        # Draw background pattern
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
                self.screen.blit(self.bg_pattern, (x, y))
        
        # Draw obstacles
        for x, y in self.obstacles:
            pygame.draw.rect(self.screen, (100, 100, 100), 
                            (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            # Add some texture to obstacles
            pygame.draw.line(self.screen, (70, 70, 70), 
                           (x * GRID_SIZE, y * GRID_SIZE), 
                           (x * GRID_SIZE + GRID_SIZE, y * GRID_SIZE + GRID_SIZE), 3)
            pygame.draw.line(self.screen, (70, 70, 70), 
                           (x * GRID_SIZE + GRID_SIZE, y * GRID_SIZE), 
                           (x * GRID_SIZE, y * GRID_SIZE + GRID_SIZE), 3)
        
        # Draw food with pulsing effect
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.1 + 0.8
        for pos, food_type, timer in self.foods:
            food_x, food_y = pos
            rect = (food_x * GRID_SIZE, food_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            if food_type == FoodType.REGULAR:
                color = RED
                pygame.draw.ellipse(self.screen, (color[0]*pulse, color[1]*pulse, color[2]*pulse), rect)
            elif food_type == FoodType.BONUS:
                color = GOLD
                # Draw with blinking effect if about to expire
                if timer == 0 or timer - pygame.time.get_ticks() > 1000 or (pygame.time.get_ticks() // 200) % 2:
                    pygame.draw.ellipse(self.screen, (color[0]*pulse, color[1]*pulse, color[2]*pulse), rect)
                    # Add sparkle effect
                    pygame.draw.line(self.screen, WHITE, 
                                   (food_x * GRID_SIZE + GRID_SIZE//2, food_y * GRID_SIZE + 2), 
                                   (food_x * GRID_SIZE + GRID_SIZE//2, food_y * GRID_SIZE + GRID_SIZE - 2), 2)
                    pygame.draw.line(self.screen, WHITE, 
                                   (food_x * GRID_SIZE + 2, food_y * GRID_SIZE + GRID_SIZE//2), 
                                   (food_x * GRID_SIZE + GRID_SIZE - 2, food_y * GRID_SIZE + GRID_SIZE//2), 2)
            elif food_type == FoodType.SPEED:
                color = BLUE
                pygame.draw.ellipse(self.screen, (color[0]*pulse, color[1]*pulse, color[2]*pulse), rect)
                # Add arrow symbol
                arrow_points = [
                    (food_x * GRID_SIZE + GRID_SIZE//2, food_y * GRID_SIZE + 4),
                    (food_x * GRID_SIZE + GRID_SIZE - 4, food_y * GRID_SIZE + GRID_SIZE//2),
                    (food_x * GRID_SIZE + GRID_SIZE//2, food_y * GRID_SIZE + GRID_SIZE - 4)
                ]
                pygame.draw.polygon(self.screen, WHITE, arrow_points)
            elif food_type == FoodType.SLOW:
                color = PURPLE
                pygame.draw.ellipse(self.screen, (color[0]*pulse, color[1]*pulse, color[2]*pulse), rect)
                # Add slow symbol
                pygame.draw.rect(self.screen, WHITE, 
                              (food_x * GRID_SIZE + 4, food_y * GRID_SIZE + GRID_SIZE//2 - 2, 
                               GRID_SIZE - 8, 4))
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake_positions):
            # Different colors for head, body segments
            if i == 0:  # Head
                color = DARK_GREEN
                # Draw with a slightly larger size for the head
                rect = pygame.Rect(x * GRID_SIZE - 1, y * GRID_SIZE - 1, GRID_SIZE + 2, GRID_SIZE + 2)
                pygame.draw.rect(self.screen, color, rect, border_radius=4)
                
                # Draw eyes based on direction
                eye_size = GRID_SIZE // 5
                eye_offset_x = GRID_SIZE // 3
                eye_offset_y = GRID_SIZE // 3
                
                # Adjust eye positions based on direction
                if self.direction == Direction.RIGHT:
                    left_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset_x, y * GRID_SIZE + eye_offset_y)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset_x, y * GRID_SIZE + GRID_SIZE - eye_offset_y)
                elif self.direction == Direction.LEFT:
                    left_eye = (x * GRID_SIZE + eye_offset_x, y * GRID_SIZE + eye_offset_y)
                    right_eye = (x * GRID_SIZE + eye_offset_x, y * GRID_SIZE + GRID_SIZE - eye_offset_y)
                elif self.direction == Direction.UP:
                    left_eye = (x * GRID_SIZE + eye_offset_x, y * GRID_SIZE + eye_offset_y)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset_x, y * GRID_SIZE + eye_offset_y)
                else:  # DOWN
                    left_eye = (x * GRID_SIZE + eye_offset_x, y * GRID_SIZE + GRID_SIZE - eye_offset_y)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset_x, y * GRID_SIZE + GRID_SIZE - eye_offset_y)
                
                pygame.draw.circle(self.screen, WHITE, left_eye, eye_size)
                pygame.draw.circle(self.screen, WHITE, right_eye, eye_size)
                
                # Draw pupils
                pygame.draw.circle(self.screen, BLACK, 
                                 (left_eye[0] + eye_size//3, left_eye[1]), eye_size//2)
                pygame.draw.circle(self.screen, BLACK, 
                                 (right_eye[0] + eye_size//3, right_eye[1]), eye_size//2)
                
            else:  # Body
                # Alternate colors for body segments
                color = GREEN if i % 2 == 0 else LIGHT_GREEN
                
                # Draw rounded segments with connection gaps
                rect = pygame.Rect(x * GRID_SIZE + 1, y * GRID_SIZE + 1, GRID_SIZE - 2, GRID_SIZE - 2)
                pygame.draw.rect(self.screen, color, rect, border_radius=3)
        
        # Draw score and game info
        score_text = self.game_font.render(f'Score: {self.score}', True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw high score
        high_score_text = self.game_font.render(f'High Score: {self.high_score}', True, GOLD)
        self.screen.blit(high_score_text, (SCREEN_WIDTH - high_score_text.get_width() - 10, 10))
        
        # Draw current speed effect if active
        if self.speed_effect_time > 0:
            if self.speed_modifier > 1:
                speed_text = self.small_font.render('SPEED BOOST!', True, BLUE)
            else:
                speed_text = self.small_font.render('SLOWED DOWN!', True, PURPLE)
            
            # Calculate time remaining
            time_left = max(0, (self.speed_effect_time - pygame.time.get_ticks()) // 1000)
            time_text = self.small_font.render(f'{time_left}s', True, WHITE)
            
            self.screen.blit(speed_text, (10, 40))
            self.screen.blit(time_text, (speed_text.get_width() + 20, 40))
        
        # Display game over message
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.title_font.render('GAME OVER', True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(game_over_text, text_rect)
            
            instructions = self.menu_font.render('Press R to Restart, M for Menu, Q to Quit', True, WHITE)
            inst_rect = instructions.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            self.screen.blit(instructions, inst_rect)
            
            final_score = self.game_font.render(f'Final Score: {self.score}', True, WHITE)
            score_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            self.screen.blit(final_score, score_rect)
        
        # Display pause message
        elif self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.title_font.render('PAUSED', True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
            
            instruction = self.menu_font.render('Press P to Resume', True, WHITE)
            inst_rect = instruction.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            self.screen.blit(instruction, inst_rect)
    
    def draw(self):
        if self.game_state == "MENU":
            self.draw_menu()
        elif self.game_state == "PLAYING":
            self.draw_game()
        
        pygame.display.update()
    
    def run(self):
        while True:
            self.handle_keys()
            self.update()
            self.draw()
            
            # Adjust speed based on difficulty and any active effects
            snake_speed = self.difficulty.value * self.speed_modifier
            self.clock.tick(snake_speed)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()