import pygame
import os
import threading
import time
import numpy as np

DEBUG = False

# Constants for the grid size and image size
GRID_WIDTH = 7
GRID_HEIGHT = 7
IMAGE_WIDTH = 100
IMAGE_HEIGHT = 100
if DEBUG:
    GAME_MINUTES = 10000
else:
    GAME_MINUTES = 3

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
                self.piece = "robot"
                self.movable = False
                match direction:
                    case "right":
                        person_image = pygame.transform.flip(
                            images["robot_side"].copy(), True, False
                        )
                    case "up":
                        person_image = images["robot_back"]
                    case "left":
                        person_image = images["robot_side"]
                    case "down":
                        person_image = images["robot_front"]
                self.image = merge_images(images["floor"], person_image)

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
        self.gw[0][5] = GridBox(images["floor"], "idle_state")
        self.gw[3][2] = GridBox(images["bap_mount"], "bap_mount")
        self.gw[3][3] = GridBox(images["cheese_mount"], "cheese_mount")
        self.gw[3][4] = GridBox(images["empty_counter"], "empty_counter")
        self.gw[4][0] = GridBox(images["raw_burger_mount"], "raw_burger_mount")
        self.gw[4][6] = GridBox(images["exit_counter"], "exit_counter")

        # create the empty two rows at the bottom to display information
        for i in range(0, GRID_WIDTH):
            self.gw[5][i] = GridBox(black_image, "bottom")
            self.gw[6][i] = GridBox(black_image, "bottom")

        grid_world.gw[0][5].movable = True # Idle State
        grid_world.gw[1][3] = GridBox(images["wall"], "wall")


    # update what the screen shows is in the hands of the player
    def update_hand(self, piece, char):
        if char == "person":
            self.gw[6][0].image = images[piece]
        if char == "robot":
            self.gw[6][2].image = images[piece]


    def find_shortest_paths(self, a, b):
        # print("Print_a")
        # print(a)
        # print("Print_b")
        # print(b)
        # print("Print_done")

        def bfs_to_target(search_space, start):
            if not any("D" in row for row in search_space):
                return None, None, None

            labelled_space = [[-1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            queue = []
            labelled_space[start[0]][start[1]] = 0
            queue.append([start])
            target = (-1, -1)

            while queue:
                path = queue.pop(0)
                node = path[-1]

                # Check surrounding nodes
                for coord in [
                    (node[0] - 1, node[1]),
                    (node[0], node[1] + 1),
                    (node[0] + 1, node[1]),
                    (node[0], node[1] - 1),
                ]:
                    # Check bounds
                    if 0 <= coord[0] < GRID_HEIGHT and 0 <= coord[1] < GRID_WIDTH:
                        if search_space[coord[0]][coord[1]] == "D":
                            return labelled_space, coord, node
                        if search_space[coord[0]][coord[1]] == "O" and labelled_space[coord[0]][coord[1]] == -1:
                            labelled_space[coord[0]][coord[1]] = labelled_space[node[0]][node[1]] + 1
                            new_path = list(path)
                            new_path.append(coord)
                            queue.append(new_path)

            # If the queue is empty and target is not found
            return None, (-1, -1), None

        # Guarentee of no hitting out of bounds
        def get_sub_paths(pos, labelled_space):
            paths = []
            to_eval = []
            current_val = labelled_space[pos[0]][pos[1]]
            if current_val == 0:
                return [[pos]]

            for adj_pos in [
                (pos[0] - 1, pos[1]),
                (pos[0], pos[1] + 1),
                (pos[0] + 1, pos[1]),
                (pos[0], pos[1] - 1),
            ]:
                if labelled_space[adj_pos[0]][adj_pos[1]] == current_val - 1:
                    to_eval.append(adj_pos)

            results = []
            for eval_pos in to_eval:
                results.append(get_sub_paths(eval_pos, labelled_space))
            flat_results = [item for sublist in results for item in sublist]
            for path in flat_results:
                path.append(pos)
            return flat_results
            
        # Initialise problem
        search_space = [["#" for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        start = (-1, -1)
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                if self.gw[i][j].piece == "floor":
                    search_space[i][j] = "O"
                if self.gw[i][j].piece == a:
                    search_space[i][j] = "S"
                    start = (i, j)
                if self.gw[i][j].piece == b:
                    search_space[i][j] = "D"

        labelled_space, target, pre_target = bfs_to_target(search_space, start)
        if labelled_space == None:
            return False
        sub_paths = get_sub_paths(pre_target, labelled_space)
        # print('output')
        # print([(path + [target]) for path in sub_paths])
        # print('end_output')
        return [(path + [target]) for path in sub_paths]

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
        self.path = []

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


def display_screen(end_time, condition=0, robot=None):
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


    if condition == 2 or condition == 3:
        for pos in robot.path[1:]:
            grid_x, grid_y = pos
            center_x = grid_x * IMAGE_WIDTH + IMAGE_WIDTH // 2
            center_y = grid_y * IMAGE_HEIGHT + IMAGE_HEIGHT // 2
            pygame.draw.circle(window, (255, 0, 0), (center_y, center_x), 5)

            if condition == 2:
                break

    # Update the display
    pygame.display.flip()


def get_largest_idx(vector):
    return list(vector).index(max(list(vector)))


# loads all images from the images directory and inserts them into a dictionary
images = load_images()

# creates the gridworld and fills it in with the appropriate gridboxes
grid_world = Gridworld()
grid_world.fill_initial_grid(images)


def run_condition(condition=0):
    # creates the person and the robot players
    person = Player("person", 2, 2)

    if condition == 0:
        robot = None
    else:
        robot = Player("robot", 2, 4)

    start_time = time.time()
    end_time = start_time + GAME_MINUTES * 60 
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


        if condition != 0:
            if time.time() >= robot_move_timer:
                robot_move_timer = time.time() + 0.5
                robot_move(robot)

        display_screen(end_time, condition, robot)

    # Quit pygame
    pygame.quit()
    return Player.score
    
def find_item(item, arr):
	# returns the index of the first occurance of item in arr, -1 if not found

	for i in range(len(arr)):
		if arr[i] == item:
			return i
		
	return -1

def robot_move(robot):
	
	#if we are currently idleing, check if we can do a more important task
	if(robot.state == "idle"):
		robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot)

	if(robot.state == "idle"):
		print('') if robot.pos_x == 0 and robot.pos_y == 5 else robot_move_to(robot, "idle_state", False)

	elif robot.state in ["place_bap", "place_burger", "cook_burger", "place_cheese", "deliver_burger"]:
		if robot.hand == "empty":
			done = robot_move_to(robot, robot.source_pos, True)
			if done and robot.hand == "empty":
				robot.state = "idle"

		elif robot.hand == robot.desired_hand:
			done = robot_move_to(robot, robot.target_pos, True)

			if done: #got to target pos and pressed space
				robot.state = "idle"
				if robot.hand != "empty":
					robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot, dump_state=True)
		
		else:
			print("Uh oh hands full")
			print(f"state: {robot.state}, source:{robot.source_pos} target:{robot.target_pos}")
			robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot, dump_state=True)
    
	elif robot.state == "dump":
		if robot.hand != "empty":
			done = robot_move_to(robot, robot.target_pos, True)
			if done and robot.hand != "empty":
				#we failed to place again, find a new empty space
				robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot, dump_state=True)
		else:
			#hands are finally free, go idle and get new job
			robot.state = "idle"

	else:
		raise Exception(f"UNKNOWN STATE: {robot.state}")


def robot_determine_state(robot, dump_state=False):

    # raw_burger_coords = (4, 1, 'left')

    hand = [robot.hand]
    pans = [ p[:p.rfind('_')] for p in [grid_world.gw[1][2].piece, grid_world.gw[1][4].piece]]
    # pan_coords = [(1,1,"right"), (2,2,"up"), (1, 3, "left"), (1, 3, "right"), (2, 4, "up"), (1, 5, 'left')]
    storage = [grid_world.gw[1][0].piece, grid_world.gw[2][0].piece, grid_world.gw[3][0].piece, grid_world.gw[3][4].piece]
    # storage_coords = [(1, 1, 'left'), (2, 1, 'left'), (3, 1, 'left'), (2, 4, 'down'), (3, 5, 'left'), (4, 4, 'up')]

    if dump_state:
        if (find_item("empty_counter", storage)) != -1:
            return ("dump", None, "empty_counter", "empty")
        else:
            return ("idle", None, None, None)

    if ((find_item('empty', pans)) != -1) and ((find_item('empty', hand)) != -1) and ((find_item('raw_burger', storage)) != -1):
        return ("cook_burger", "raw_burger", "empty_pan", 'raw_burger')
    if ((find_item('empty', pans)) != -1) and ((find_item('empty', hand)) != -1):
        return ("cook_burger", "raw_burger_mount", "empty_pan", 'raw_burger')    
    elif ((find_item('cooked_burger', pans)) != -1) and ((find_item('empty', hand)) != -1) and ((find_item('bap', storage)) != -1):
        return ("place_burger", "cooked_burger_pan", "bap", "cooked_burger")
    elif  ((find_item('cooked_burger', pans)) != -1) and ((find_item('empty', hand)) != -1) and ((find_item('bap_cheese', storage)) != -1):
        return ("place_burger", "cooked_burger_pan", "bap_cheese", "cooked_burger")
    elif  ((find_item('cooked_burger', pans)) != -1) and ((find_item('empty', hand)) != -1) and ((find_item('bap_burger', storage)) != -1):
        return ("place_cheese", "cheese_mount", "bap_burger", "cheese")
    elif ((find_item('empty', hand)) != -1) and ((find_item('bap_burger_cheese', storage)) != -1):
        return ("place_bap", "bap_mount", "bap_burger_cheese", "bap")
    elif ((find_item('empty', hand)) != -1) and ((find_item('bap', storage)) != -1):
        return ("place_cheese", "cheese_mount", "bap", "cheese")
    elif ((find_item('empty', hand)) != -1) and ((find_item('bap_burger_cheese_bap', storage)) != -1):
        return ("deliver_burger", "bap_burger_cheese_bap", "exit_counter", "bap_burger_cheese_bap")
    elif ((find_item('empty', hand)) != -1) and ((find_item('empty_counter', storage)) != -1):
        return ("place_bap", "bap_mount", "empty_counter", "bap")
    else:
        return ("idle", None, None, None)

        


def robot_move_to(robot, dest, press_space=True):
    # print(dest)
	# (x,y,dir) = pos
	# print(f"walking to {x},{y},{dir}")
	# print(f"currently at {robot.pos_x},{robot.pos_y},{robot.direction}")
	# print(f"in state: {robot.state}")
    print("dest")
    print(dest)
    path = grid_world.find_shortest_paths("robot", dest)

    if path == False:
        return True

    path = path[0]
    path = path[1:] if path[-1] == (0, 5) else path[1:-1]
    robot.path = path


    print(path)

    if not path:
        dir = find_direction(robot, dest)
        move = find_move(robot, dir)

        if robot.direction != dir:
            path = [move]
        else:
            if press_space:
                robot.space()
            return True
        

    follow_directions(robot, robot.pos_x, robot.pos_y, path[0][0], path[0][1])

    return False

def follow_directions(robot, curr_x, curr_y, next_x, next_y):
    direction = ""
    if next_x == curr_x:
        direction = "left" if (next_y < curr_y) else "right"
    else:
        direction = "down" if (next_x > curr_x) else "up"
    robot.move(direction)

    return 

def find_direction(robot, dest):
    x, y = robot.pos_x, robot.pos_y

    print(dest)
    
    if (x, y) == (1, 1):
        if dest == "empty_pan" or dest == "cooked_burger_pan":
            return "right"
        return "left"
    elif (x, y) == (2, 1):
        return "left"
    elif (x, y) == (3, 1):
        if dest == "bap_mount":
            return "right"
        return "left"
    elif (x, y) == (4, 1):
        return "left"
    elif (x, y) == (2, 2):
        if dest == "bap_mount":
            return "down"
        return "up"
    elif (x, y) == (4, 2):
        return "up"
    elif (x, y) == (2, 3):
        return "down"
    elif (x, y) == (4, 3):
        return "up"
    elif (x, y) == (2, 4):
        if dest == "empty_pan" or dest == "cooked_burger_pan":
            return "up"
        return "down"
    elif (x, y) == (4, 4):
        return "up"
    elif (x, y) == (1, 5):
        return "left"
    elif (x, y) == (3, 5):
        return "left"
    elif (x, y) == (4, 5):
        return "right"
    else:
        return None
    

def find_move(robot, dir):
    if dir  == "right":
        return (robot.pos_x, robot.pos_y + 1)
    elif dir == "left":
        return (robot.pos_x, robot.pos_y - 1)
    elif dir == "up":
        return (robot.pos_x - 1, robot.pos_y)
    else:
        return (robot.pos_x + 1, robot.pos_y)

if __name__ == "__main__":

    print("Enter 1, 2 or 3 for condition. Enter 0 for tutorial stage")
    cond = int(input("SELECT CONDITION: "))

    if cond < 0 or cond > 3:
        print("Please enter a valid condition")
        exit()

    score = run_condition(cond)
    print(f"\nFinal score: {score}")