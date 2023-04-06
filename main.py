import pygame as pg
import sys
import math
import random
import os

################################################ GAME INFO ######################################################
#                                                                                                               #                     
# - Game Objective - Collect 5 coins to level up, starting point level 0, end point reach level 5 without dying.#
# - Two types of ghosts come from above:                                                                        #
# - Type 1: Gray: They are following you whenever you go.                                                       #
# - Type 2: Pink: They only fall down, but can do damage too                                                    #
# - If any ghost touch you, you lose one of your lives and the ghost dissapear.                                 #
# - On each level you gain, the ghosts are increased x 5 of each type are added to the game                     #
# - When you kill ghost, coin spawns at the location where you killed it and starts falling down.               #
# - In order to catch it you must wait for it to fall down to you.                                              #
# - If you shoot another ghost the coin respawns at the new location. Sometimes would be necessary to do so.    #
# - There is some kind of escape mechanism with the doors, with little delay between usage.                     #
# - Goal is to reach level 5 without spending all your lives/hits.                                              #
# - Bonus coin spawns at random location - Left or Right corner at the start of the game.                       #
#                                                                                                               #
################################################ GAME INFO ######################################################

pg.init()

# Start game at center of the screen
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Global's
WIN_WIDTH, WIN_HEIGHT = (800, 800)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (42, 178, 106)
GRAY = (177, 177, 177)
PINK = (255,20,147)
POINTS = 25
FPS = 60

# Class for creating the enemies, loading images, editing them and random location on screen
class EnemyController:
    def __init__(self, window_rect):
        # Create enemies 
        self.window_rect = window_rect
        self.enemies = []
        self.player_enemies = 5
        self.gray_enemy_image = self.enemy_image_load('gray')
        self.pink_enemy_image = self.enemy_image_load('pink')
        self.create_enemies()

        # Used only for our game over screen
        self.enemy_image_won = self.enemy_image_load('pink')
        self.enemy_image_won_rect = self.enemy_image_won.get_rect()
    
    # Create our enemies. Load them and do modifications. Append them to our list with enemies
    def create_enemies(self):

        for i in range(self.player_enemies):
            self.enemies.append(self.random_enemy_location('gray'))
            self.enemies.append(self.random_enemy_location('pink'))
        
    # This method is used to swap the img color of our ghost from black to gray and eyes color to red
    def swap_enemy_color(self, surface, from_, to):
        arr = pg.PixelArray(surface)
        arr.replace(from_, to)
        del arr
    
    # Load enemy image, swap colors, transform image
    def enemy_image_load(self, type):
        image = pg.image.load('monster.png').convert_alpha()
        if type == 'gray':
            transformed_image = pg.transform.rotate(image, 180)
            self.swap_enemy_color(transformed_image, (BLACK), (GRAY))
            self.swap_enemy_color(transformed_image, (255, 255, 255), (RED))
            image.set_colorkey((0, 0, 0))

            return transformed_image
        
        elif type == 'pink':
            transformed_image = pg.transform.rotate(image, 50)
            self.swap_enemy_color(transformed_image, (BLACK), (PINK))
            self.swap_enemy_color(transformed_image, (255, 255, 255), (GREEN))
            #image.set_colorkey((0, 0, 0))
            #transformed_image = image
            
            return transformed_image

    # Generate random enemy location on screen      
    def random_enemy_location(self, type):
        x = random.randint(0, self.window_rect.width)
        y = random.randint(-500, -100)
        
        if type == 'gray':
            return Enemy(self.gray_enemy_image, self.window_rect, (x, y), type)
        elif type == 'pink':
            return Enemy(self.pink_enemy_image, self.window_rect, (x, y), type)
      
    # Update our enemies and check for: Collision with player, if enemy is killed or if enemy is off screen
    def update(self, player, window):
        for enemy in self.enemies:
            enemy.update(player)
            enemy_type = random.choice(['gray', 'pink'])
            if enemy.dead: # If enemy dead
                self.enemies.remove(enemy)
                player.add_points(POINTS)
                self.enemies.append(self.random_enemy_location(enemy_type))

             # If there is collision with player           
            if enemy.collide_player:
                self.enemies.remove(enemy)
                player.take_damage(1)
                self.enemies.append(self.random_enemy_location(enemy_type))
                # Sometimes generates error when player is moving and ghost touch it
                break 

            # If its offscren, remove it and add it to a random starting location again
            if enemy.off_screen: 
                self.enemies.remove(enemy)
                enemy.off_screen = False
                self.enemies.append(self.random_enemy_location(enemy_type))

            # If level up upgrade_enemies == True. Upgrade max enemies, set upgrade to false for next level up
            if player.upgrade_enemies: 
                self.update_max_enemies(player)
                player.upgrade_enemies = False
                
            enemy.draw(window)
        
    def update_max_enemies(self, player):
        # Increase our max enemies by 5 - 5 of each kind so its 10
        # Create new enemies 
        self.player_enemies += 5 
        self.create_enemies()    
        print(len(self.enemies))
    
class Enemy:
    def __init__(self, image, window_rect, starting_position, enemy_type):
        # Enemy image and rect
        self.window_rect = window_rect
        self.image = image
        self.rect = self.image.get_rect(center=(starting_position[0], starting_position[1]))
        self.mask = pg.mask.from_surface(self.image)
        
        # Distance from played the ghost has to go & speed of ghost
        self.distance_from_player = 50
        self.speed = 1
        self.enemy_type = enemy_type
        self.dead = False
        self.collide_player = False
        
        # Enemy position on screen
        self.off_screen = False

    # Method to keep track of player position and move the ghost toward him
    def position_to_player(self, player_rect):
        c = math.sqrt((player_rect.x - self.rect.x) ** 2 + (player_rect.y - self.distance_from_player - self.rect.y) **2)
        try:
            x = round((player_rect.x - self.rect.x) / c)
            y = round(((player_rect.y - self.distance_from_player) - self.rect.y) / c)
        except ZeroDivisionError:
            return False
        return (x, y)

    # Update each enemy type and move them
    def update(self, player):
        if self.enemy_type == 'gray':
            new_position = self.position_to_player(player.rect) # We send player rect location
            if new_position: # If position_to_player returns cordinates
                self.rect.x = (self.rect.x + new_position[0] * self.speed)
                self.rect.y = (self.rect.y + new_position[1] * self.speed)

        elif self.enemy_type == 'pink':
            
            self.rect.y = (self.rect.y + self.speed)
        
        # If ghost top rect is greater than window rect bottom - ghost is off screen
        if self.rect.top > self.window_rect.bottom - (player.rect.height + 35):
            self.off_screen = True
        
        # Check for player collision
        self.check_player_collision(player)
    
    # Check player collision
    def check_player_collision(self, player):
        # Check if both rects collide.  If they do collide,  create offset x and y and check if masks collide too.
        if self.rect.colliderect(player.rect): 
            offset_x = player.rect.x - self.rect.x 
            offset_y = player.rect.y - self.rect.y
            if self.mask.overlap(player.mask, (offset_x, offset_y)):
                self.collide_player = True
                         
    # Draw enemy on screen/surface/window
    def draw(self, surface):
        surface.blit(self.image, self.rect )

class Player:
    def __init__(self, window_rect, tools):
        # Player image, position and starting position
        self.window_rect = window_rect
        self.image = pg.image.load('robot.png').convert()
        self.mask = pg.mask.from_surface(self.image)
        self.original_image = pg.transform.scale(self.image, (50, 86))
        self.start_buffer = 141
        self.speed = 3
        self.rect = self.image.get_rect(center=(self.window_rect.centerx, self.window_rect.bottom - self.start_buffer)) 

        # Image for dead screen
        self.dead_image = pg.transform.rotate(self.image, 180) 
        self.dead_image_rect = self.dead_image.get_rect(center=(self.rect.centerx, self.rect.bottom - self.start_buffer))

        # Player laser
        self.bullet_color = (GREEN)
        self.lasers = []

        # Timer for laser
        self.timer = 0.0
        self.laser_delay = 500
        self.add_laser = False

        # Player stats
        self.points = 0
        self.lives = 3

        # Player level
        self.level = 0
        self.upgrade_enemies = False
        self.dead = False
        self.game_won = False

        # Spawn coin if enemy dead
        self.spawn_coin = False
        self.coin_count = 0
        self.coin_cord = []

        # Timer and delay for door use
        self.door_timer = 0.0
        self.door_delay = 1000
        self.can_enter = False

        # To update our stats information - take_damage, add_points, level_up
        self.tools = tools
    
    def take_damage(self, value):
        self.lives -= value
        self.tools.update_lives(self.lives)
    
    def add_points(self, value):
        self.points += value
        self.tools.update_score(self.points)
    
    def level_up(self):
        self.level += 1
        self.upgrade_enemies = True
        self.tools.update_level(self.level)

        if self.level == 5:
            self.game_won = True
    
    # Listening for events for player if pressing space == shooting
    def get_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                if self.add_laser:  # If True == We can shoot
                    self.lasers.append(GhostBlaster(self.rect.center, self.window_rect, self.bullet_color)) # Create laser obj from Laser class and append to lasers
                    self.add_laser = False # Set to False after appending                                                         
            if event.key == pg.K_q:
                pg.quit()
                sys.exit()

    # Update player
    def update(self, keys, enemies, door):
        # Set boundaries for player not being able moving off screen
        self.rect.clamp_ip(self.window_rect)
        
        # Move left or right
        if keys[pg.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pg.K_RIGHT]:
            self.rect.x += self.speed
        
        # Every time player.update() is run check if we can shoot
        if pg.time.get_ticks() - self.timer > self.laser_delay: # Subtract time from our timer and compare with the set delay
            self.timer = pg.time.get_ticks() # Set our timer to the current tick
            self.add_laser = True # True == we can shoot
        
        # Update laser and check if its off screen. If off screen we remove it
        for laser in self.lasers[:]:
            remove = laser.update(laser)
            if remove:
                self.lasers.remove(laser)

        # Check collision with laser, ghosts and door a
        self.check_collision_blaster(enemies)
        self.check_player_enter_door(door)
        self.check_player_level()
        
        # Keep track of player lives,  0 == dead
        if self.lives <= 0:
            self.lives = 0
            self.dead = True   

    # Loop tru total fired lasers, update laser on each iteration. If laser rect collide with ghost rect we check if their masks colide too
    # The masks of each are checked so we are sure that they collide - the ghost and the laser
    def check_collision_blaster(self, enemies):
        for laser in self.lasers[:]:
            laser.update()
            for enemy in enemies: # Iterating over each enemy in our enemies list
                if laser.rect.colliderect(enemy.rect): # If there is collision with both rects
                    offset_x = laser.rect.x - enemy.rect.x # Create offset x and y
                    offset_y = laser.rect.y - enemy.rect.y
                    if enemy.mask.overlap(laser.mask, (offset_x, offset_y)): # Check if mask overlap and set enemy to dead = True
                        enemy.dead = True
                        if not self.spawn_coin: # If we dont have alrdy spawned coin
                            self.spawn_coin = True 
                            self.coin_cord = enemy.rect.x, enemy.rect.y # Spawn coin at enemy cordinates we killed it
                        self.lasers.remove(laser) # Remove laser after we kill enemy
                        break

    # On every 5 coins level up and set coins count to 0 again
    def check_player_level(self):
        if self.coin_count == 5:
            self.level_up()
            self.coin_count = 0
    
    # Check if player is entering door and use timer.
    def check_player_enter_door(self, door):
        # For some reason could not check for collision between door and player and used player rect x & screen width.
        # Timer to enter the door
        if pg.time.get_ticks() - self.door_timer > self.door_delay: 
            self.door_timer = pg.time.get_ticks() # Door timer is set to current time tick
            self.can_enter = True 
            # Left door
            if self.rect.x < door.rect.x and self.can_enter:
                self.rect = self.image.get_rect(center=(self.window_rect.right - 50, self.window_rect.bottom - self.start_buffer))
                self.can_enter = False
            # Right door   
            elif self.rect.x > WIN_WIDTH - 70 and self.can_enter:
                self.rect = self.image.get_rect(center=(self.window_rect.left - 50, self.window_rect.bottom - self.start_buffer))
                self.can_enter = False

    # Draw player and render shooting with laser
    def draw(self, surface):
        for laser in self.lasers[:]:
            laser.render(surface)

        surface.blit(self.original_image, self.rect)

class GhostBlaster:
    def __init__(self, loc, window_rect, color):
        self.window_rect = window_rect
        self.image = pg.Surface([3, 50]).convert_alpha()
        self.mask = pg.mask.from_surface(self.image)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=loc) # loc = location of our robot
        self.speed = 8
    
    def update(self, direction='up'):
        if direction == 'down':
            self.rect.y += self.speed
        else:
            self.rect.y -= self.speed
        
        # Check if laser is off screen and remove it
        if self.rect.bottom < self.window_rect.top: 
            return True
    
    # Draw laser on screen
    def render(self, surface):
        surface.blit(self.image, self.rect)

# Class for our coin
class Coin:
    def __init__(self):
        self.image = pg.image.load('coin.png').convert()
        self.image.set_colorkey(BLACK)

        # Spawn coin at start at random location - Left corner or Right corner
        self.spawn_random = random.choice([[20, 0], [WIN_WIDTH -20, 0]])
        self.rect = self.image.get_rect(center=(self.spawn_random))
 
        #self.rect = self.image.get_rect(center=(self.window_rect.centerx, self.window_rect.bottom - self.start_buffer)) 
        
        self.collected = False
        self.coin_points = 50
        self.speed = 5

    #  Update our coin and if not collected move it down
    def update(self, player):
        if not self.collected:
            self.rect.y += self.speed
            
        if player.spawn_coin: # if true
            self.rect = self.image.get_rect(center=(player.coin_cord[0], player.coin_cord[1])) # spawn coin
            player.spawn_coin = False # set to false
             
        self.player_collide_check(player)

    # Check for collision between player and coin      
    def player_collide_check(self, player):
        if self.rect.colliderect(player.rect): 
            player.add_points(self.coin_points)
            self.collected = True
            player.coin_count += 1
            self.rect = self.image.get_rect().move((-500, -500))
        
        self.collected = False
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
class Floor:
    def __init__(self):
        self.image = pg.Surface([50, 50]).convert_alpha()
        self.image_rect = self.image.get_rect()
        self.image.fill((112, 128, 144))
        pg.draw.rect(self.image, (255, 0, 0), [0, 0, 50, 50], 1)
        self.bottom_position = (WIN_HEIGHT - self.image_rect.width) - self.image_rect.height
        self.floor = []

        # Get total amouunt of tiles
        for i in range(round(WIN_WIDTH / self.image_rect.width)):
            self.floor.append(self.image)

    # Draw floor according to screen width
    def draw(self, surface):
        x = 0
        for i in range(len(self.floor)):
            surface.blit(self.image, [x + self.image_rect.width * i, self.bottom_position])

# Escape mechanism for our robot
class Door:
    def __init__(self):
        self.image = pg.image.load('door.png').convert()
        self.original_image = pg.transform.scale(self.image, (50, 100))
        self.rect = self.original_image.get_rect()
        self.original_image.set_colorkey(BLACK)
        
        # Door height position
        self.door_height_position = WIN_HEIGHT - (95 + self.rect.height)
    # Draw our doors at both sides on screen
    def draw(self, surface):
        surface.blit(self.original_image, (0, self.door_height_position))
        surface.blit(self.original_image, (WIN_WIDTH - self.rect.width, self.door_height_position))

# For printing Game won, game over and player stats & score
class Tools:
    def __init__(self, window):
        # window rect and font init
        self.window = window
        self.window_rect = window.get_rect()
        self.font_init(self.window_rect)
    
    # Defining font size, color and position on screen for texts also update them
    def font_init(self, window_rect):
        # Size and color
        self.text_size = 25
        self.text_color = (GREEN)

        # Game texts position on screen
        self.score_position = (10, WIN_HEIGHT - 10)
        self.font = pg.font.SysFont('Arial', self.text_size)
        self.lives_position = (185, window_rect.bottom - 10)
        self.level_position = (WIN_WIDTH - 475, WIN_HEIGHT - 10)
        self.new_game_position = (WIN_WIDTH - 380, WIN_HEIGHT - 10)
        self.exit_game_position = (WIN_WIDTH - 250, window_rect.bottom - 10)

        # Create our update's texts for score, lives, level
        self.update_score()
        self.update_lives()
        self.update_level()

        # Create exit, start & new game texts
        self.exit_text()
        self.start_screen()
        self.new_game()

        # Create game over and game won texts
        self.game_over()
        self.game_won()

    # Create score, lives, level, exit, new game texts  updates and rects   
    def update_score(self, score=0):
        self.score_text, self.score_text_rect = self.make_text(f'Score: {score}', self.score_position)
    
    def update_lives(self, lives=3):
        self.lives_text, self.lives_text_rect = self.make_text(f'Lives {lives}', self.lives_position)
    
    def update_level(self, level=0):
        self.level_text, self.level_text_rect = self.make_text(f'Level {level}', self.level_position)
    
    def exit_text(self):
        self.ex_text, self.exit_text_rect = self.make_text(f'(Press Q = Exit game)', self.exit_game_position)
    
    def new_game(self):
        self.new_game_text, self.new_game_text_rect = self.make_text(f'(F2 = NG)', self.new_game_position)
    
    # Method to make our text and position
    def make_text(self, display_text, position):
        text = self.font.render(display_text, True, self.text_color)
        rect = text.get_rect(bottomleft=position)

        return text, rect
    
    # Starting screen text
    def start_screen(self):
        start_screen_font = pg.font.SysFont('Arial', 50)
        press_key_font = pg.font.SysFont('Arial', 22)

        self.start_screen_text = start_screen_font.render(f'Are you Ready?', True, (GREEN))
        self.press_key = press_key_font.render('Press any key', True, (GREEN))

        self.start_screen_text_rect = self.start_screen_text.get_rect(center=self.window_rect.center)
        self.press_key_rect = self.press_key.get_rect(center=self.start_screen_text_rect.midbottom)

    # Game over text and position on screen
    def game_over(self):
        game_over_font = pg.font.SysFont('Arial', 55)
        self.game_over_text = game_over_font.render('GAME OVER!', True, (RED))
        self.game_over_rect = self.game_over_text.get_rect(center=self.window_rect.center)

    # Game won text and position on screen
    def game_won(self):
        game_won_font = pg.font.SysFont('Arial', 55)
        self.game_won_text = game_won_font.render('YOU WON THE GAME!', True, (RED))
        self.game_won_rect = self.game_won_text.get_rect(center=self.window_rect.center)

    # Draw texts on screen
    def draw(self):
        self.window.blit(self.score_text, self.score_text_rect)
        self.window.blit(self.lives_text, self.lives_text_rect)
        self.window.blit(self.level_text, self.level_text_rect)
        self.window.blit(self.ex_text, self.exit_text_rect)
        self.window.blit(self.new_game_text, self.new_game_text_rect)

# The Game class with the main loop, updates and draws.
class Game:
    def __init__(self):  
        # Creating window screen
        self.window = pg.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.window_rect = self.window.get_rect()

        pg.display.set_caption("Ghost Blaster")

        # Start the game. Create player, enemies...
        self.new_game()

    # Player, floor, door, enemy_control/enemies & coin. Tools for our texts, start and game over screens
    def new_game(self):
        tools = Tools(self.window)
        player = Player(self.window_rect, tools)
        floor = Floor()
        door = Door()
        enemy_contol = EnemyController(self.window_rect)
        coin = Coin()

        # Start game main loop
        self.main_loop(tools, player, floor, door, enemy_contol, coin)

    # Main loop of our game
    def main_loop(self, tools, player, floor, door, enemy_control, coin):
        # Clock
        clock = pg.time.Clock()

         # While loop is running
        running = True

        # Start screen check
        pressed_key = False

        # Main game loop  
        while running:
            # Listen for keys pressed / movement
            keys = pg.key.get_pressed()
            # Listen for events. Start game, exit game and shooting
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    pressed_key = True 
                    if event.key == pg.K_F2:
                        self.new_game()
                if event.type == pg.QUIT:
                    running = False
                player.get_event(event)
            
            self.window.fill(BLACK)

            # If player is alive and game is not won and game is started. Update player, enemies and coin and draw them on screen
            if not player.dead and not player.game_won and pressed_key:
                player.update(keys, enemy_control.enemies, door)
                enemy_control.update(player, self.window)
                coin.update(player)

                coin.draw(self.window)
                player.draw(self.window)

            # If player is dead display game over screen.
            if player.dead:
                self.window.blit(tools.game_over_text, tools.game_over_rect)
                self.window.blit(player.dead_image, player.dead_image_rect)
                self.window.blit(enemy_control.enemy_image_won, (330, 447))

            # Game won screen
            if player.game_won:
                self.window.blit(tools.game_won_text, tools.game_won_rect)

            # Start screen
            if not pressed_key:
                self.window.blit(tools.start_screen_text, tools.start_screen_text_rect)
                self.window.blit(tools.press_key, tools.press_key_rect)
                self.window.blit(player.original_image, tools.press_key_rect.midbottom)

            # Floor and door draw. Score, lives, level, exit and new game texts draw.
            floor.draw(self.window)
            door.draw(self.window)
            tools.draw()
        
            pg.display.update()
            clock.tick(FPS)

        # Exit
        pg.quit()
        sys.exit(0)

if __name__ == "__main__":
    game = Game()
    game.new_game()