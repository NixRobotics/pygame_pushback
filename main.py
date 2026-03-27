import asyncio
from math import sin, cos, radians
import pygame
import random

FIELD_TO_SCREEN_SCALE = 2
FIELD_WIDTH = 3600
FIELD_HEIGHT = 3600
BACKGROUND_WIDTH = FIELD_WIDTH // FIELD_TO_SCREEN_SCALE
BACKGROUND_HEIGHT = FIELD_HEIGHT // FIELD_TO_SCREEN_SCALE
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 960
GAME_SPEED_TICKS = 60
POOP_SIZE = 50
CHARACTER_SIZE = 50
ROBOT_SIZE = 200
ROBOT_ASPECT =  1.277
FLAGS = 0 | pygame.SCALED

pygame.init()
pygame.mixer.init()
# The screen where all the graphics will be drawn
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FLAGS)
# sets the background of the screen, try updating this for something more beautiful!
background_image = pygame.image.load('assets/field_top.png')
background_image = pygame.transform.scale(background_image, (BACKGROUND_WIDTH, BACKGROUND_HEIGHT)).convert()

players = pygame.sprite.Group()
enemies = pygame.sprite.Group()
poops = pygame.sprite.Group()
clock = pygame.time.Clock()


class Poop(pygame.sprite.Sprite):
    ''' Represents the poop projectiles fired by the player.'''
    def __init__(self, x, y, cam_x, cam_y, angle):
        super().__init__()
        self.image = pygame.image.load('assets/octo_blue.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (POOP_SIZE, POOP_SIZE))
        self.x = x
        self.y = y
        # TODO: Clean-up camera code on objet creation
        self.rect = self.image.get_rect(
            center = (
                (self.x - cam_x) // FIELD_TO_SCREEN_SCALE + SCREEN_WIDTH // 2 - POOP_SIZE // 2,
                -(self.y - cam_y) // FIELD_TO_SCREEN_SCALE + SCREEN_HEIGHT // 2 - POOP_SIZE // 2)
            )
        self.angle = angle

    def update(self, cam_x, cam_y):
        '''This method is called by the event loop below, driven by the loop in main().
        This is called ever frame. Read the pyGame documentation for more details on a frame.
        TL;DR: A frame is one iteration of the game loop, which is typically 1/60th of a second.
        Our job here to update the poop's position, orientation, color, live-or-death
        etc properties as needed.
        '''
        if self.rect is None: return

        self.x += 8 * sin(radians(self.angle)) # Move sideways
        self.y += 8 * cos(radians(self.angle)) # Move upward

        # Note: Balls do not change aspect, so this works
        self.rect.x = (self.x - cam_x) // FIELD_TO_SCREEN_SCALE + SCREEN_WIDTH // 2 - POOP_SIZE // 2  # Move sideways
        self.rect.y = -(self.y - cam_y) // FIELD_TO_SCREEN_SCALE + SCREEN_HEIGHT // 2 - POOP_SIZE // 2 # Move upward

        if self.x < 0: self.kill() # Remove if off-screen
        if self.x > FIELD_WIDTH: self.kill() # Remove if off-screen
        if self.y < 0: self.kill() # Remove if off-screen
        if self.y > FIELD_HEIGHT: self.kill() # Remove if off-screen

class Player(pygame.sprite.Sprite):
    ''' Represents the player character, which is a cannon that can move left and right and fire poops.
    
    Notice that it's very similar to Poop? They both inherit from pygame.sprite.Sprite, and they both
    have an image and a rect. The main difference is that the Player has more complex behavior in its
    update() method, and it also has a hit() method to play a sound when it gets hit by an enemy.
    '''

    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load('assets/remy.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (ROBOT_SIZE, int(ROBOT_SIZE * ROBOT_ASPECT)))
        self.angle = 0
        self.x = 600
        self.y = 600
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        # TODO: Currently this assumes camera is right over robot - should set initial view properly
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.ticks = pygame.time.get_ticks()

    def update(self, cam_x, cam_y):
        if (self.rect is None): return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.angle -= 2
        if keys[pygame.K_RIGHT]: self.angle += 2
        if keys[pygame.K_UP]:
            self.y += 10 * cos(radians(self.angle))
            self.x += 10 * sin(radians(self.angle))
        if keys[pygame.K_DOWN]:
            self.y -= 10 * cos(radians(self.angle))
            self.x -= 10 * sin(radians(self.angle))

        # Block driving through walls ...
        if self.x < 300: self.x = 300
        if self.x > FIELD_WIDTH - 300: self.x = FIELD_WIDTH - 300
        if self.y < 300: self.y = 300
        if self.y > FIELD_HEIGHT - 300: self.y = FIELD_HEIGHT - 300

        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        # Note: robot aspect changes with rotation, so we need to update the rect every time
        self.rect = self.image.get_rect(center=(
             (self.x - cam_x) // FIELD_TO_SCREEN_SCALE + SCREEN_WIDTH // 2,
            -(self.y - cam_y) // FIELD_TO_SCREEN_SCALE + SCREEN_HEIGHT // 2)
        )

        if keys[pygame.K_SPACE]:
            # Slow down bullet firing for more fun
            if pygame.time.get_ticks() - self.ticks > 5 * GAME_SPEED_TICKS:
                self.ticks = pygame.time.get_ticks()
                Poop(self.x, self.y, cam_x, cam_y, self.angle).add(poops)
    
    def hit(self):
        ''' This method is called by in the event loop when the player gets hit by an enemy.

        In this method we define the sepcific behavior that happens when the player gets hit.
        In this case, we simply play a sound effect.
        '''
        sound = pygame.mixer.Sound('assets/game-over.ogg')
        sound.play()

class Enemy(pygame.sprite.Sprite):
    ''' Represents the enemy characters, which are monsters that move downward and can be hit by poops.
    
    Now do you see the pattern? Enemy is also a Sprite, and it has an image and a rect. It also has an
    update() method. Do you see how nice classes and inheritance can be? We can reuse a lot of code and
    just change the parts that are different. This is one of the main benefits of object-oriented
    programming (OOP).  This pattern can also significantly simplify our code and make things much more
    intuitive.
    '''
    def __init__(self, x, y, cam_x, cam_y, angle):
        super().__init__()
        self.image = pygame.image.load('assets/octo_red.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (CHARACTER_SIZE, CHARACTER_SIZE))
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(
            center=(
                (self.x - cam_x) // FIELD_TO_SCREEN_SCALE + SCREEN_WIDTH // 2 - CHARACTER_SIZE // 2,
                -(self.y - cam_y) // FIELD_TO_SCREEN_SCALE + SCREEN_HEIGHT // 2 - CHARACTER_SIZE // 2)
            )
        self.angle = angle
        self.is_hit = False

    def update(self, cam_x, cam_y):
        if self.rect is None: return

        self.x += 10 * sin(radians(self.angle)) # Move sideways
        self.y += 10 * cos(radians(self.angle)) # Move upward

        # Aspect fixed
        self.rect.x = (self.x - cam_x) // FIELD_TO_SCREEN_SCALE + SCREEN_WIDTH // 2 - CHARACTER_SIZE // 2  # Move sideways
        self.rect.y = -(self.y - cam_y) // FIELD_TO_SCREEN_SCALE + SCREEN_HEIGHT // 2 - CHARACTER_SIZE // 2 # Move upward

        if self.x < 0: self.kill() # Remove if off-field
        if self.x > FIELD_WIDTH: self.kill() # Remove if off-field
        if self.y < 0: self.kill() # Remove if off-field
        if self.y > FIELD_HEIGHT: self.kill() # Remove if off-field

    def hit(self):
        sound = pygame.mixer.Sound('assets/ough-hit.ogg')
        sound.play()


# The main game loop, which is the heart of our game. This is where we will handle events,
# update the game state, and render everything on the screen. The async is only needed
# when the code executed in a browser, so that we can yield control back to the browser
# to keep the UI responsive. But the async wouldn't hurt local execution either.
async def main():
    player = Player()
    # Add the player to a group b/c pygame.sprite.groupcollide only works with groups.
    players.add(player)
    camera = [player.x, player.y]

    # Technically we don't need running now and just use break.
    # Please feel free to add other features to utitlize the running
    # variable, such as a pause menu or a game over screen.
    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Simple camera logic - follow player unless close to edge of field to limit border fill
        # TODO: Camera should be updated after player update - right now there is a small "reset" only noticeable when robot stops
        camera[0] = player.x
        camera[1] = player.y
        if camera[0] < 1200: camera[0] = 1200
        elif camera[0] > FIELD_WIDTH - 1200: camera[0] = FIELD_WIDTH - 1200
        if camera[1] < 900: camera[1] = 900
        elif camera[1] > FIELD_HEIGHT - 900: camera[1] = FIELD_HEIGHT - 900

        # random.random() generates a random number between 0 and 1, so this means
        # we have a 20% chance to spawn an enemy every frame.
        # The enimies can also be added in its own thread and loop. Feel free to try that!
        if random.random() >= 0.99:
            # Spawn an enemy at a random angle from center goals
            k = Enemy(1800, 1800, camera[0], camera[1], 45 + 90 * int(4 * random.random()))
            enemies.add(k)

        # Check to see if anyone dies
        player_hits = pygame.sprite.groupcollide(players, enemies, True, True)

        # pygame.sprite.groupcollide returns a dictionary of all the sprites in
        # the first group that collided with sprites in the second group.
        # we have to decide what to do when a collision happens. In this case,
        # we simply call the hit() method of the Sprite and the behavior will be
        # handled accordingly depending on the type of the Sprite. This is another
        # example of how OOP can help us write clean and intuitive code.
        for player in player_hits.keys():
            player.hit()
        # TODO: Hits are processed on full bounding rect which is conservative
        enemy_hits = pygame.sprite.groupcollide(enemies, poops, True, True)
        for enemy in enemy_hits.keys():
            enemy.hit()

        # Update
        players.update(camera[0], camera[1])
        poops.update(camera[0], camera[1])
        enemies.update(camera[0], camera[1])
        
        # In each iteration the whole screen is redrawn, including the background and all
        # Sprites on the screen. This is similar to how a movie works, where each frame is
        # a still image, and when you play the movie, it shows the frames in quick succession
        # to create the illusion of motion.
        position = (camera[0], camera[1])
        field_top_left = (
            position[0] // FIELD_TO_SCREEN_SCALE - SCREEN_WIDTH // 2,
            BACKGROUND_HEIGHT - position[1] // FIELD_TO_SCREEN_SCALE - SCREEN_HEIGHT // 2)
        screen.fill((0, 0, 0)) # Clear the screen with white before drawing the new frame
        screen.blit(background_image, (0, 0), (field_top_left[0], field_top_left[1], SCREEN_WIDTH, SCREEN_HEIGHT))
        players.draw(screen)
        enemies.draw(screen)
        poops.draw(screen)
        pygame.display.flip()
        clock.tick(GAME_SPEED_TICKS)
        await asyncio.sleep(0)  # Yields control to the browser if playing inside a browser.

    pygame.quit()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())