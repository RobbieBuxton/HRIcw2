import pygame
import os
import threading
import time
import random

# Constants for the grid size and image size
GRID_WIDTH = 7
GRID_HEIGHT = 7
IMAGE_WIDTH = 100
IMAGE_HEIGHT = 100
GAME_MINUTES = 3
black = (0, 0, 0)
white = (255, 255, 255)
black_image = pygame.Surface((100,100))


# Initialize pygame
pygame.init()

font = pygame.font.Font(None, 36)

# Set up the window size
window_width = GRID_WIDTH * IMAGE_WIDTH
window_height = GRID_HEIGHT * IMAGE_HEIGHT
window_size = (window_width, window_height)
window = pygame.display.set_mode(window_size)

def start_cooking_burger(grid_loc):
	time.sleep(5) 
	grid_loc.image = images["cooked_burger_pan"]
	grid_loc.piece = "cooked_burger_pan"

class GridBox():
	def __init__(self, image, piece):
		self.image = image
		self.piece = piece 

		if (self.piece == "floor"):	
			self.movable = True
		else:
			self.movable = False

	def update_char(self, character):
		if character == "person":
			self.image = images["person"]
			self.piece = "person"
			self.movable = False
		if character == "empty":
			self.image = images["floor"]
			self.piece = "floor"
			self.movable = True
		if character == "robot":
			self.image = images["robot"]
			self.piece = "robot"
			self.movable = False


	def update(self,piece):
		self.piece = piece
		self.image = images[piece]

	def remove_piece(self):
		self.image = images["empty_counter"]
		self.piece = "empty_counter" 

	def remove_burger(self):
		self.image = images["empty_pan"]
		self.piece = "empty_pan"



class Gridworld():
	def __init__(self):
		self.gw = [[GridBox("","") for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

	def fill_initial_grid(self,images):

		# initiate the full grid to be empty floor
		for i in range (0, GRID_HEIGHT):
			for j in range (0, GRID_WIDTH):
				self.gw[i][j] = GridBox(images["floor"], "floor")

		# all the edges are countertops
		for i in range(0,GRID_HEIGHT-3):
			self.gw[i][0] = GridBox(images["empty_counter"], "empty_counter")
			self.gw[i][GRID_WIDTH-1] = GridBox(images["empty_counter"], "empty_counter")
			self.gw[i][3] = GridBox(images["empty_counter"], "empty_counter")
		for i in range(0, GRID_WIDTH):
			self.gw[0][i] = GridBox(images["empty_counter"], "empty_counter")
			self.gw[GRID_HEIGHT-3][i] = GridBox(images["empty_counter"], "empty_counter")

		# place things on counter
		self.gw[0][1] = GridBox(images["raw_burger_mount"], "raw_burger_mount")
		self.gw[4][1] = GridBox(images["cheese_mount"], "cheese_mount")
		self.gw[2][6] = GridBox(images["empty_pan"], "empty_pan")
		self.gw[3][6] = GridBox(images["empty_pan"], "empty_pan")
		self.gw[4][4] = GridBox(images["bap_mount"], "bap_mount")
		# self.gw[4][1] = GridBox(images["empty_pan"], "empty_pan")
		# self.gw[3][2] = GridBox(images["empty_counter"], "empty_counter")
		self.gw[2][0] = GridBox(images["exit_counter"], "exit_counter")

		#create the emptry two rows at the bottom to display information
		for i in range (0,GRID_WIDTH):
			self.gw[5][i] = GridBox(black_image, "bottom")
			self.gw[6][i] = GridBox(black_image, "bottom")

	#update what the screen shows is in the hands of the player
	def update_hand(self,piece, char):
		if char == "person":
			self.gw[6][0].image = images[piece]
		if char == "robot":
			self.gw[6][2].image = images[piece]

		

class Player():
	score = 0
	def __init__(self, c, x, y):
		# Initial character position
		self.pos_x = x
		self.pos_y = y
		self.char = c
		self.score = 0
		self.direction = "none"
		self.hand = "empty"

		#Additionally store a player's internal state. Not used by human player
		# but can be mainpulated for the robot player
		self.state = "idle"
		self.source_pos = None
		self.target_pos = None
		self.desired_hand= None

		# I think this should be gw[y],[x] since gw is stored row major
		# In fact every access into gw should be [y][x] not [x][y]
		# I could change this everywhere, or I could just make my function ugly
		grid_world.gw[x][y] = GridBox(images[c], c)
	
	def move(self, direction):
		if direction == "down":
			self.direction = "down"
			if (grid_world.gw[self.pos_x+1][self.pos_y].movable == True): 
				grid_world.gw[self.pos_x+1][self.pos_y].update_char(self.char)
				grid_world.gw[self.pos_x][self.pos_y].update_char("empty")
				self.pos_x +=1
				
		if direction == "up":
			self.direction = "up"
			if (grid_world.gw[self.pos_x-1][self.pos_y].movable == True): 
				grid_world.gw[self.pos_x-1][self.pos_y].update_char(self.char)
				grid_world.gw[self.pos_x][self.pos_y].update_char("empty")
				self.pos_x -=1
				
		if direction == "left":
			self.direction = "left"
			if (grid_world.gw[self.pos_x][self.pos_y-1].movable == True): 
				grid_world.gw[self.pos_x][self.pos_y-1].update_char(self.char)
				grid_world.gw[self.pos_x][self.pos_y].update_char("empty")
				self.pos_y -=1
				
		if direction == "right":
			self.direction = "right"
			if (grid_world.gw[self.pos_x][self.pos_y+1].movable == True): 
				grid_world.gw[self.pos_x][self.pos_y+1].update_char(self.char)
				grid_world.gw[self.pos_x][self.pos_y].update_char("empty")
				self.pos_y +=1
				

	def pickup(self):

		# cannot pickup if hands are full
		if self.hand != "empty":
			return

		if (self.direction == "right"):
			grid_loc = grid_world.gw[self.pos_x][self.pos_y+1]
		elif (self.direction == "left"):
			grid_loc = grid_world.gw[self.pos_x][self.pos_y-1]
		elif (self.direction == "up"):
			grid_loc = grid_world.gw[self.pos_x-1][self.pos_y]
		elif (self.direction == "down"):
			grid_loc = grid_world.gw[self.pos_x+1][self.pos_y]
		else:
			return




		pickupable_pieces = ["bap", "raw_burger", "cheese", "cooked_burger", "bap_burger", "bap_burger_cheese", "bap_burger_cheese_bap"]

		if (grid_loc.piece in pickupable_pieces):
			self.hand = grid_loc.piece
			grid_world.update_hand(grid_loc.piece, self.char)
			grid_loc.remove_piece()


		pickupable_mounts = ["bap_mount", "raw_burger_mount", "cheese_mount"]
		if (grid_loc.piece in pickupable_mounts):
			if grid_loc.piece == "bap_mount":
				self.hand = "bap"
				grid_world.update_hand("bap", self.char)
			if grid_loc.piece == "raw_burger_mount":
				self.hand = "raw_burger"
				grid_world.update_hand("raw_burger", self.char)
			if grid_loc.piece == "cheese_mount":
				self.hand = "cheese"
				grid_world.update_hand("cheese", self.char)

		if (grid_loc.piece == "cooked_burger_pan"):
			self.hand = "cooked_burger"
			grid_loc.remove_burger()
			grid_world.update_hand("cooked_burger", self.char)



	def drop(self):
		# print(self.direction)
		if (self.direction == "right"):
			grid_loc = grid_world.gw[self.pos_x][self.pos_y+1]
		if (self.direction == "left"):
			grid_loc = grid_world.gw[self.pos_x][self.pos_y-1]
		if (self.direction == "up"):
			grid_loc = grid_world.gw[self.pos_x-1][self.pos_y]
		if (self.direction == "down"):
			grid_loc = grid_world.gw[self.pos_x+1][self.pos_y]

		if grid_loc.piece == "empty_counter":
			grid_loc.update(self.hand)
			self.hand = "empty"
			grid_world.update_hand("empty_counter", self.char)

		elif grid_loc.piece == "empty_pan":
			if self.hand == "raw_burger":
				grid_loc.update("burger_pan")
				self.hand = "empty"
				grid_world.update_hand("empty_counter", self.char)
				delayed_thread = threading.Thread(target=start_cooking_burger, args=(grid_loc,))
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
		if (self.hand == "empty"):
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
	return (images)



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


# Helper functions for robot_move() to make code more readable
def find_item(item, arr):
	# returns the index of the first occurance of item in arr, -1 if not found

	for i in range(len(arr)):
		if arr[i] == item:
			return i
		
	return -1


def both_pans_done(pans):
	"""
	returns the index of the first done pan ONLY if both pans are done, -1 otherwise
	"""
	done = 0
	for item in pans:
		if(item == "cooked_burger"):
			done += 1
	if(done == 2):
		return find_item("cooked_burger", pans)
	else:
		return -1


def two_table_spaces(table):
	"""
	returns the index of the first empty table space ONLY if 2 spaces are empty, -1 otherwise
	"""
	free = 0
	for item in table:
		if(item == "empty_counter"):
			free += 1
	if(free >= 2):
		return find_item("empty_counter", table)
	else:
		return -1
		

def print_state(robot):
	print(f"State: {robot.state}")
	print(f"Source_pos: {robot.source_pos}")
	print(f"Target_pos: {robot.target_pos}")
	print(f"Desired_hand: {robot.desired_hand}")
	print(f"Pos_x: {robot.pos_x}")
	print(f"Pos_y: {robot.pos_y}")
	print(f"Hand: {robot.hand}")
	print("")


def robot_determine_state(robot):
	"""
	based on the grid_world and robot hand determine the robot's desired high level action
	returns 4-tuple (state, start_pos, end_pos, desired_hand) - start_pos and end_pos may be None
			go to start_pos, pick up desired_hand, go to end_pos, put down
	"""
	table = [grid_world.gw[3][3].piece, grid_world.gw[2][3].piece, grid_world.gw[1][3].piece]
	table_coords = [(3,4,"left"), (2,4,"left"), (1,4,"left")]
	#note these are the coords the robot should be to interact with table[i], not the coord of table[i] itself

	pans = [ p[:p.rfind('_')] for p in [grid_world.gw[3][6].piece, grid_world.gw[2][6].piece]]
	pan_coords = [(3,5,"right"), (2,5,"right")]
	 # for convenience we strip the ending "_pan" so that a cooked_burger in the pan or the hand both appear as cooked_burger
	 # so that looking for "cooked_burger" in hand or "cooked_burger_pan" in pans is the same as "cooked_burger" in pans + hand

	hand = [robot.hand]
	# lists are defined in this order to give precedance to the table and pan closest to the burger mount,
	#  since it is preferable for the robot to stay close to this side 

	storage = [grid_world.gw[0][4].piece,grid_world.gw[0][5].piece,grid_world.gw[1][6].piece,grid_world.gw[4][5].piece]
	storage_coords = [(1,4,"up"),(1,5,"up"),(1,5,"right"),(3,5,"down")]
	# all aditional work surfaces. Used to dump contents if needed

	print("")
	print(table)
	print(pans)
	print(hand)
	print("")

	# if we have previously dumped a bap into storage, take that one first, to clear storage
	if (s := find_item("bap", storage)) != -1:
		bap_coords = storage_coords[s]
	else:
		bap_coords = (3,4,"down")

	
	#if statements are defined in this order to give precedence to more important actions
	# in the case that we could transition to multiple states

	if (t := find_item("bap_burger_cheese", table)) != -1:
		return ("place_bap", bap_coords, table_coords[t], "bap")
	
	elif ((t := find_item("bap_cheese", table)) != -1) and ((p := find_item("cooked_burger", pans + hand)) != -1):
		return ("place_burger", pan_coords[p], table_coords[t], "cooked_burger")
	
	elif ((t := find_item("bap", table)) != -1) and ((p := find_item("cooked_burger", pans + hand)) != -1):
		return ("place_burger",pan_coords[p], table_coords[t], "cooked_burger")
	
	elif (t := find_item("cooked_burger", table)) != -1:
		return ("place_bap", bap_coords, table_coords[t], "bap")
	
	elif (t := find_item("cheese", table)) != -1:
		return ("place_bap", bap_coords, table_coords[t], "bap")
	
	elif (p := both_pans_done(pans) != -1) and (t := find_item("empty_counter", table)) != -1:
		return ("place_burger", pan_coords[p], table_coords[t], "cooked_burger")
	
	elif ((t := find_item("raw_burger", table + hand)) != -1) and ((p := find_item("empty", pans)) != -1):
		return ("cook_burger", table_coords[t], pan_coords[p], "raw_burger")
	
	elif (t := two_table_spaces(table)) != -1:
		return ("place_bap", bap_coords, table_coords[t], "bap")

	else:
		return ("idle", None, None, None)


def robot_move_to(robot, pos, press_space=True):
	"""
	Moves the robot to position x,y facing in direction dir
	if press_space set then robot presses space when in desired position
	Returns True if achieved desired position, False otherwise
	"""
	(x,y,dir) = pos
	print(f"walking to {x},{y},{dir}")
	print(f"currently at {robot.pos_x},{robot.pos_y},{robot.direction}")
	print(f"in state: {robot.state}")

	# I hate it here. robot position accesses gw[x][y], but gw is row major grid
	#[[o,o,o],
    # [o,o,o],
	# [o,*,o]] <- which row we are in stored as robot's x_pos
	#    ^ which element within this row is stored as robot's y_pos

	# so x is actually its height in the gw, ie the logical y coordinate
	# this is why the x check decides up or down and y decides left or right. Very unintuitive

	pathx = []
	dx = robot.pos_x - x
	pathx = abs(dx) * (["down"] if dx < 0 else ["up"])

	pathy = []
	dy = robot.pos_y - y
	pathy = abs(dy) * (["right"] if dy < 0 else ["left"])

	if dir in ["up", "down"]:
		path = pathy + pathx
	else:
		path = pathx + pathy
	# if we want to be facing horizontal then our last movement should be a horizontal one, else vertical
	#  recall x is actually vertical position so pathx is vertical movements

	print(f"path: {path}")
	print("")

	if not path: #if list is empty
		if robot.direction != dir: #correct space, wrong direction. This can only happen if we didnt need to move to complete this action
			path = [dir]
		else: #at correct position and direction
			if press_space:
				robot.space()
			return True

	robot.move(path[0])
	return False


def robot_move(robot):
	
	#if we are currently idleing, check if we can do a more important task
	if(robot.state == "idle"):
		print("Changing State")
		robot.state, robot.source_pos, robot.target_pos, robot.desired_hand = robot_determine_state(robot)
		print(robot.state, robot.source_pos, robot.target_pos, robot.desired_hand)
	

	if robot.state == "idle": #if we really are still idle move to a convenient location which is close to most tasks, but dont pick anything up
		robot_move_to(robot, (3, 4, "left"), False)
	
	elif robot.state in ["place_bap", "place_burger", "cook_burger"]:
		if robot.hand == "empty":
			robot_move_to(robot, robot.source_pos, True)
		elif robot.hand == robot.desired_hand:
			done = robot_move_to(robot, robot.target_pos, True)
			if done: #got to target pos and pressed space
				robot.state = "idle"
		else:
			print("Uh oh hands full")
			print(f"state: {robot.state}, source:{robot.source_pos} target:{robot.target_pos}")

	else:
		raise Exception(f"UNKNOWN STATE: {robot.state}")


#loads all images from the images directory and inserts them into a dictionary
images = load_images()

# creates the gridworld and fills it in with the appropriate gridboxes
grid_world = Gridworld()
grid_world.fill_initial_grid(images)


def main():

	#creates the person and the robot players
	person = Player("person",2,2)
	robot = Player("robot",2,4)

	start_time = time.time()
	end_time = start_time + GAME_MINUTES * 60  # 5 minutes in seconds
	robot_move_timer = time.time() + 0.5

	#main loop
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
					person.move("up")
				elif event.key == pygame.K_DOWN:
					person.move("down")
				elif event.key == pygame.K_LEFT:
					person.move("left")
				elif event.key == pygame.K_RIGHT:
					person.move("right")
				elif event.key == pygame.K_SPACE:
					person.space()
				elif event.key == pygame.K_w:
					robot.move("up")
				elif event.key == pygame.K_s:
					robot.move("down")
				elif event.key == pygame.K_a:
					robot.move("left")
				elif event.key == pygame.K_d:
					robot.move("right")
				elif event.key == pygame.K_RSHIFT:
					robot.space()

		if time.time() >= robot_move_timer:
			robot_move_timer = time.time() + 0.5
			robot_move(robot)

		display_screen(end_time)
		

	# Quit pygame
	pygame.quit()


if __name__ == "__main__":
	main()