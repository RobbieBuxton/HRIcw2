import pygame
import os
import threading
import time
import numpy as np

DEBUG = True

# Constants for the grid size and image size
GRID_WIDTH = 7
GRID_HEIGHT = 7
IMAGE_WIDTH = 100
IMAGE_HEIGHT = 100
if DEBUG:
    GAME_MINUTES = 10000
else:
    GAME_MINUTES = 1
black = (0, 0, 0)
white = (255, 255, 255)
black_image = pygame.Surface((100, 100))

# Initialize pygame
pygame.init()

font = pygame.font.Font(None, 36)

# Set up the window size
window_width = GRID_WIDTH * IMAGE_WIDTH
window_height = GRID_HEIGHT * IMAGE_HEIGHT
window_size = (window_width, window_height)
window = pygame.display.set_mode(window_size)


def merge_images(base_image, top_image):
    merged_image = base_image.copy()
    merged_image.blit(top_image.copy(), (0, 0))
    return merged_image


def start_cooking_burger(grid_loc):
    time.sleep(5)
    grid_loc.image = images["cooked_burger_pan"]
    grid_loc.piece = "cooked_burger_pan"


class GridBox:
    def __init__(self, image, piece):
        self.image = image
        self.piece = piece

        if self.piece == "floor":
            self.movable = True
        else:
            self.movable = False

    def update_char(self, character, direction):
        match character:
            case "person":
                self.image = merge_images(images["floor"], images["person_front"])
                self.piece = "person"
                self.movable = False
                person_image = images["person_front"]
                match direction:
                    case "right":
                        person_image = pygame.transform.flip(
                            images["person_side"].copy(), True, False
                        )
                    case "up":
                        person_image = images["person_back"]
                    case "left":
                        person_image = images["person_side"]
                    case "down":
                        person_image = images["person_front"]
                self.image = merge_images(images["floor"], person_image)
            case "empty":
                self.image = images["floor"]
                self.piece = "floor"
                self.movable = True
            case "robot":
                self.image = images["robot"]
                self.piece = "robot"
                self.movable = False

    def update(self, piece):
        self.piece = piece
        self.image = images[piece]

    def remove_piece(self):
        self.image = images["empty_counter"]
        self.piece = "empty_counter"

    def remove_burger(self):
        self.image = images["empty_pan"]
        self.piece = "empty_pan"


class Gridworld:
    def __init__(self):
        self.gw = [
            [GridBox("", "") for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)
        ]

    def fill_initial_grid(self, images):
        # initiate the full grid to be empty floor
        for i in range(0, GRID_HEIGHT):
            for j in range(0, GRID_WIDTH):
                self.gw[i][j] = GridBox(images["floor"], "floor")

        # N,E edges are walls, W edge is counter
        for i in range(0, GRID_HEIGHT - 3):
            self.gw[i][0] = GridBox(images["empty_counter"], "empty_counter")
            self.gw[i][GRID_WIDTH - 1] = GridBox(
                images["wall"], "wall"
            )
        for i in range(0, GRID_WIDTH):
            self.gw[0][i] = GridBox(images["wall"], "wall")


        # place things on counter
        self.gw[1][2] = GridBox(images["empty_pan"], "empty_pan")
        self.gw[1][4] = GridBox(images["empty_pan"], "empty_pan")
        self.gw[3][2] = GridBox(images["bap_mount"], "bap_mount")
        self.gw[3][3] = GridBox(images["cheese_mount"], "cheese_mount")
        self.gw[3][4] = GridBox(images["empty_counter"], "empty_counter")
        self.gw[4][0] = GridBox(images["raw_burger_mount"], "raw_burger_mount")
        self.gw[4][6] = GridBox(images["exit_counter"], "exit_counter")

        # create the empty two rows at the bottom to display information
        for i in range(0, GRID_WIDTH):
            self.gw[5][i] = GridBox(black_image, "bottom")
            self.gw[6][i] = GridBox(black_image, "bottom")

    # update what the screen shows is in the hands of the player
    def update_hand(self, piece, char):
        if char == "person":
            self.gw[6][0].image = images[piece]
        if char == "robot":
            self.gw[6][2].image = images[piece]

class Player:
    score = 0

    def __init__(self, c, x, y):
        # Initial character position
        self.pos_x = x
        self.pos_y = y
        self.char = c
        self.score = 0
        self.direction = "none"
        self.hand = "empty"
        self.state = "idle"
        self.source_pos = None
        self.target_pos = None
        self.desired_hand= None

        grid_world.gw[x][y] = GridBox(images[c], c)

    def move(self, direction):
        self.direction = direction
        if direction == "down":
            if grid_world.gw[self.pos_x + 1][self.pos_y].movable == True:
                grid_world.gw[self.pos_x + 1][self.pos_y].update_char(
                    self.char, direction
                )
                grid_world.gw[self.pos_x][self.pos_y].update_char("empty", direction) 
                self.pos_x += 1
        if direction == "up":
            if grid_world.gw[self.pos_x - 1][self.pos_y].movable == True:
                grid_world.gw[self.pos_x - 1][self.pos_y].update_char(
                    self.char, direction
                )
                grid_world.gw[self.pos_x][self.pos_y].update_char("empty", direction)
                self.pos_x -= 1

        if direction == "left":
            if grid_world.gw[self.pos_x][self.pos_y - 1].movable == True:
                grid_world.gw[self.pos_x][self.pos_y - 1].update_char(
                    self.char, direction
                )
                grid_world.gw[self.pos_x][self.pos_y].update_char("empty", direction)
                self.pos_y -= 1

        if direction == "right":
            if grid_world.gw[self.pos_x][self.pos_y + 1].movable == True:
                grid_world.gw[self.pos_x][self.pos_y + 1].update_char(
                    self.char, direction
                )
                grid_world.gw[self.pos_x][self.pos_y].update_char("empty", direction)
                self.pos_y += 1
        grid_world.gw[self.pos_x][self.pos_y].update_char(self.char, direction)

    def pickup(self):
        # cannot pickup if hands are full
        if self.hand != "empty":
            return

        if self.direction == "right":
            grid_loc = grid_world.gw[self.pos_x][self.pos_y + 1]
        elif self.direction == "left":
            grid_loc = grid_world.gw[self.pos_x][self.pos_y - 1]
        elif self.direction == "up":
            grid_loc = grid_world.gw[self.pos_x - 1][self.pos_y]
        elif self.direction == "down":
            grid_loc = grid_world.gw[self.pos_x + 1][self.pos_y]
        else:
            return

        pickupable_pieces = [
            "bap",
            "raw_burger",
            "cheese",
            "cooked_burger",
            "bap_burger",
            "bap_burger_cheese",
            "bap_burger_cheese_bap",
            "bap_cheese",
        ]

        if grid_loc.piece in pickupable_pieces:
            self.hand = grid_loc.piece
            grid_world.update_hand(grid_loc.piece, self.char)
            grid_loc.remove_piece()

        pickupable_mounts = ["bap_mount", "raw_burger_mount", "cheese_mount"]
        if grid_loc.piece in pickupable_mounts:
            if grid_loc.piece == "bap_mount":
                self.hand = "bap"
                grid_world.update_hand("bap", self.char)
            if grid_loc.piece == "raw_burger_mount":
                self.hand = "raw_burger"
                grid_world.update_hand("raw_burger", self.char)
            if grid_loc.piece == "cheese_mount":
                self.hand = "cheese"
                grid_world.update_hand("cheese", self.char)

        if grid_loc.piece == "cooked_burger_pan":
            self.hand = "cooked_burger"
            grid_loc.remove_burger()
            grid_world.update_hand("cooked_burger", self.char)

    def drop(self):
        # print(self.direction)
        if self.direction == "right":
            grid_loc = grid_world.gw[self.pos_x][self.pos_y + 1]
        if self.direction == "left":
            grid_loc = grid_world.gw[self.pos_x][self.pos_y - 1]
        if self.direction == "up":
            grid_loc = grid_world.gw[self.pos_x - 1][self.pos_y]
        if self.direction == "down":
            grid_loc = grid_world.gw[self.pos_x + 1][self.pos_y]

        if grid_loc.piece == "empty_counter":
            grid_loc.update(self.hand)
            self.hand = "empty"
            grid_world.update_hand("empty_counter", self.char)

        elif grid_loc.piece == "empty_pan":
            if self.hand == "raw_burger":
                grid_loc.update("burger_pan")
                self.hand = "empty"
                grid_world.update_hand("empty_counter", self.char)
                delayed_thread = threading.Thread(
                    target=start_cooking_burger, args=(grid_loc,)
                )
                delayed_thread.start()

        if grid_loc.piece == "bap":
            if self.hand == "cooked_burger":
                self.hand = "empty"
                grid_loc.update("bap_burger")
                grid_world.update_hand("empty_counter", self.char)
            if self.hand == "cheese":
                self.hand = "empty"
                grid_loc.update("bap_cheese")
                grid_world.update_hand("empty_counter", self.char)
            if self.hand == "bap_burger_cheese":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese_bap")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "cheese":
            if self.hand == "bap_burger":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese")
                grid_world.update_hand("empty_counter", self.char)
            if self.hand == "bap":
                self.hand = "empty"
                grid_loc.update("bap_cheese")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "cooked_burger":
            if self.hand == "bap":
                self.hand = "empty"
                grid_loc.update("bap_burger")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "bap_burger":
            if self.hand == "cheese":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "bap_cheese":
            if self.hand == "cooked_burger":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "bap_burger_cheese":
            if self.hand == "bap":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese_bap")
                grid_world.update_hand("empty_counter", self.char)

        if grid_loc.piece == "exit_counter":
            if self.hand == "bap_burger_cheese_bap":
                self.hand = "empty"
                Player.score += 1
                grid_world.update_hand("empty_counter", self.char)

    def space(self):
        if self.hand == "empty":
            self.pickup()
        else:
            self.drop()


def load_images():
    image_dir = "images"
    images = {}
    for filename in os.listdir(image_dir):
        if filename.endswith(".png"):
            image_path = os.path.join(image_dir, filename)
            image = pygame.image.load(image_path)
            im_name = filename[0:-4]
            images[im_name] = image

    images["exit_counter"] = images["exit_counter_flipped"]
    return images


def display_screen(end_time):
    # Clear the screen
    window.fill((255, 255, 255))

    # Draw the grid with images
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            grid_image = grid_world.gw[i][j].image
            window.blit(grid_image, (j * IMAGE_WIDTH, i * IMAGE_HEIGHT))

    score_text = font.render(f"Score: {Player.score}", True, white)
    window.blit(score_text, (4 * IMAGE_WIDTH + 50, 5 * IMAGE_HEIGHT + 50))

    remaining_time = int(end_time - time.time())
    minutes = remaining_time // 60
    seconds = remaining_time % 60
    timer_text = font.render(f"Time Left: {minutes:02}:{seconds:02}", True, white)
    window.blit(timer_text, (4 * IMAGE_WIDTH + 50, 6 * IMAGE_HEIGHT + 0))

    person_hand = font.render(f"Person hand:", True, white)
    robot_hand = font.render(f"Robot hand:", True, white)
    window.blit(person_hand, (0 * IMAGE_WIDTH, 5 * IMAGE_HEIGHT + 50))
    window.blit(robot_hand, (2 * IMAGE_WIDTH, 5 * IMAGE_HEIGHT + 50))

    # Update the display
    pygame.display.flip()

def get_largest_idx(vector):
    return list(vector).index(max(list(vector)))


class UserModel:
    def __init__(self):
        self.users_real_actions = []
        self.users_predicted_actions = (
            []
        )  # you want to be careful that the predicted_actions and the real_actions match up in size, as you will get more observations than you will get real actions.

# loads all images from the images directory and inserts them into a dictionary
images = load_images()

# creates the gridworld and fills it in with the appropriate gridboxes
grid_world = Gridworld()
grid_world.fill_initial_grid(images)


def main():
    # creates the person and the robot players
    person = Player("person", 2, 2)
    robot = Player("robot", 2, 4)

    user_model = UserModel()

    start_time = time.time()
    end_time = start_time + GAME_MINUTES * 60  # 5 minutes in seconds
    robot_move_timer = time.time() + 0.5

    # main loop
    running = True
    while (time.time() < end_time) and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # print (event.key)
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    user_action = "up"
                    person.move("up")
                elif event.key == pygame.K_DOWN:
                    user_action = "down"
                    person.move("down")
                elif event.key == pygame.K_LEFT:
                    user_action = "left"
                    person.move("left")
                elif event.key == pygame.K_RIGHT:
                    user_action = "right"
                    person.move("right")
                elif event.key == pygame.K_SPACE:
                    user_action = "space"
                    person.space()

        if time.time() >= robot_move_timer:
            robot_move_timer = time.time() + 0.5
            robot_move(robot)

        display_screen(end_time)

    # Quit pygame
    pygame.quit()


def robot_move(robot):
	
	#if we are currently idleing, check if we can do a more important task
	if(robot.state == "idle"):
		print("Changing State")
		robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot)
		print(robot.state, robot.source_pos, robot.target_pos, robot.desired_hand)
# def robot_move(robot):
#     pass

def robot_determine_state(robot):
    hand = [robot.hand]
    return 1, 2, 3, 4

def robot_move_to(robot):
    pass


if __name__ == "__main__":
    main()