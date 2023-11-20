import pygame
import os
import threading
import time
import random
import numpy as np

# Constants for the grid size and image size
GRID_WIDTH = 7
GRID_HEIGHT = 7
IMAGE_WIDTH = 100
IMAGE_HEIGHT = 100
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


# Maps
states = [
    "grab_raw_burger",
    "cook_raw_burger",
    "grab_cooked_burger",
    "grab_cheese",
    "grab_bap",
    "combine_bap_burger",
    "combine_bap_cheese",
    "combine_bap_cheese_burger",
    "combine_bap_cheese_burger_bap",
    "deliver_cheeseburger",
]

state_targets = {
    #Grab Raw Burger
    "grab_raw_burger": {
        "empty":["raw_burger_mount","raw_burger"]},
        # "raw_burger":["empty_counter"]},
    #Cook Raw Burger
    "cook_raw_burger": {
        "empty":["raw_burger"],
        "raw_burger":["empty_pan"]},
    #Grab Cooked Burger
    "grab_cooked_burger": {
        "empty":["cooked_burger_pan","cooked_burger"]},
        # "cooked_burger":["empty_counter"]},
    #Grab Cheese
    "grab_cheese": {
        "empty":["cheese_mount","cheese"]},
        # "cheese":["empty_counter"]},
    #Grab Bap
    "grab_bap": {
        "empty":["bap_mount","bap"]},
        # "bap":["empty_counter"]},
    #Combine Bap Burger
    "combine_bap_burger": {
        "empty":["cooked_burger","bap"],
        "bap":["cooked_burger"],
        "cooked_burger":["bap"]},
    #Combine Bap Cheese
    "combine_bap_cheese": {
        "empty":["cheese","bap"],
        "bap":["cheese"],
        "cheese":["bap"]},
    #Combine Bap Cheese Burger   
    "combine_bap_cheese_burger": {
        "empty":["bap_cheese","bap_burger","cooked_burger","cheese"],
        "bap_burger":["cheese"],
        "cheese":["bap_burger"],
        "bap_cheese":["cooked_burger"],
        "cooked_burger":["bap_cheese"]},
    #Combine Bap Cheese Burger Bap
    "combine_bap_cheese_burger_bap": {
        "empty":["bap","bap_burger_cheese"],
        "bap":["bap_burger_cheese"],
        "bap_burger_cheese":["bap"]},
    #Deliver Cheeseburger
    "deliver_cheeseburger": {
        "empty":["bap_burger_cheese_bap"],
        "bap_burger_cheese_bap":["exit_counter"]}
}

state_map = {}
for idx, state in enumerate(states):
    state_map[state] = idx

obs = ["up", "down", "left", "right", "space"]

obs_map = {}
for idx, ob in enumerate(obs):
    obs_map[ob] = idx

# New Helper Functions


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

        # all the edges are countertops
        for i in range(0, GRID_HEIGHT - 3):
            self.gw[i][0] = GridBox(images["empty_counter"], "empty_counter")
            self.gw[i][GRID_WIDTH - 1] = GridBox(
                images["empty_counter"], "empty_counter"
            )
        for i in range(0, GRID_WIDTH):
            self.gw[0][i] = GridBox(images["empty_counter"], "empty_counter")
            self.gw[GRID_HEIGHT - 3][i] = GridBox(
                images["empty_counter"], "empty_counter"
            )

        # place things on counter
        self.gw[0][1] = GridBox(images["raw_burger_mount"], "raw_burger_mount")
        self.gw[0][4] = GridBox(images["cheese_mount"], "cheese_mount")
        self.gw[2][6] = GridBox(images["empty_pan"], "empty_pan")
        self.gw[4][4] = GridBox(images["bap_mount"], "bap_mount")
        self.gw[4][1] = GridBox(images["empty_pan"], "empty_pan")
        self.gw[3][2] = GridBox(images["empty_counter"], "empty_counter")
        self.gw[2][0] = GridBox(images["exit_counter"], "exit_counter")

        # create the emptry two rows at the bottom to display information
        for i in range(0, GRID_WIDTH):
            self.gw[5][i] = GridBox(black_image, "bottom")
            self.gw[6][i] = GridBox(black_image, "bottom")

    # update what the screen shows is in the hands of the player
    def update_hand(self, piece, char):
        if char == "person":
            self.gw[6][0].image = images[piece]
        if char == "robot":
            self.gw[6][2].image = images[piece]


    def get_piece_map(self, hand):
        piece_map={}
        if hand != "empty":
            piece_map[hand] = 1
        
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                piece = self.gw[x][y].piece
                if piece in piece_map:
                    piece_map[piece] += 1
                else:
                    piece_map[piece] = 1

        return piece_map

    # A and B are pieces that are not the floor
    def find_shortest_paths(self, a, bs):
        def bfs_to_target(search_space, start):
            labelled_space = [[-1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            # Bredth first search
            # maintain a queue of paths
            queue = []
            # push the first path into the queue
            labelled_space[start[0]][start[1]] = 0
            queue.append([start])
            target = (-1, -1)
            while queue:
                # get the first path from the queue
                path = queue.pop(0)
                # get the last node from the path
                node = path[-1]
                # Add surrounding paths to the queue. Assume it's impossible to go out of bounds because floor is never at boundry of map
                for coord in [
                    (node[0] - 1, node[1]),
                    (node[0], node[1] + 1),
                    (node[0] + 1, node[1]),
                    (node[0], node[1] - 1),
                ]:
                    if search_space[coord[0]][coord[1]] == "D":
                        return labelled_space, coord, node
                    if search_space[coord[0]][coord[1]] == "O":
                        if labelled_space[coord[0]][coord[1]] == -1:
                            labelled_space[coord[0]][coord[1]] = (
                                labelled_space[node[0]][node[1]] + 1
                            )
                        else:
                            labelled_space[coord[0]][coord[1]] = min(
                                labelled_space[node[0]][node[1]] + 1,
                                labelled_space[coord[0]][coord[1]],
                            )
                        new_path = list(path)
                        new_path.append(coord)
                        queue.append(new_path)

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
        found_d = False
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                if self.gw[i][j].piece == "floor":
                    search_space[i][j] = "O"
                if self.gw[i][j].piece == a:
                    search_space[i][j] = "S"
                    start = (i, j)
                if self.gw[i][j].piece in bs:
                    search_space[i][j] = "D"
                    found_d = True
                    
        if not found_d:
            return False
        labelled_space, target, pre_target = bfs_to_target(search_space, start)
        sub_paths = get_sub_paths(pre_target, labelled_space)
        print('output')
        print([(path + [target]) for path in sub_paths])
        print('end_output')
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
            if self.hand == "bap_cheese":
                self.hand = "empty"
                grid_loc.update("bap_burger_cheese")
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


def robot_move(robot):
    robot_direction = random.choice(["up", "down", "right", "left"])
    robot.move(robot_direction)

    ##################################################################


def get_largest_idx(vector):
    return list(vector).index(max(list(vector)))


class UserModel:
    def __init__(self):
        self.paths_lens_history = []
        self.old_piece_map = grid_world.get_piece_map("empty")
        self.state_history = []
        self.ticks_since_state_change = 0

        for i in range(5):
            self.paths_lens_history.append([-1]*10)

        self.users_real_actions = []
        self.users_predicted_actions = (
            []
        )  # you want to be careful that the predicted_actions and the real_actions match up in size, as you will get more observations than you will get real actions.

        self.prob_state = np.ones((10, 1))/10.0

        # TODO: create other needed variables

    def generate_can_reach_state_array(self, person, piece_map):
        can_reach_state_array = np.zeros(10)
        # "grab_raw_burger",
        can_reach_state_array[state_map['grab_raw_burger']] = (person.hand in ["empty"])
        # "cook_raw_burger",
        can_reach_state_array[state_map['cook_raw_burger']] = ((('empty_pan' in piece_map) and ('raw_burger' in piece_map)) and (person.hand in ["raw_burger"]))
        # "grab_cooked_burger",
        can_reach_state_array[state_map['grab_cooked_burger']] = ((('cooked_burger_pan' in piece_map) or ("cooked_burger" in piece_map)) and (person.hand in ["empty"]))
        # "grab_cheese",
        can_reach_state_array[state_map['grab_cheese']] = (person.hand in ["empty"])
        # "grab_bap",
        can_reach_state_array[state_map['grab_bap']] = (person.hand in ["empty"])
        # "combine_bap_burger",
        can_reach_state_array[state_map['combine_bap_burger']] = ((('cooked_burger' in piece_map) and ('bap' in piece_map)) and (person.hand in ["empty","cooked_burger","bap"]))
        # "combine_bap_cheese",
        can_reach_state_array[state_map['combine_bap_cheese']] = ((('cheese' in piece_map) and ('bap' in piece_map)) and (person.hand in ["empty","cheese","bap"]))
        # "combine_bap_cheese_burger",
        can_reach_state_array[state_map['combine_bap_cheese_burger']] = (((('bap_burger' in piece_map) and ('cheese' in piece_map)) or (('cooked_burger' in piece_map) and ('bap_cheese' in piece_map))) and (person.hand in ["empty","cheese","cooked_burger","bap_burger",'bap_cheese']))
        # "combine_bap_cheese_burger_bap",
        can_reach_state_array[state_map['combine_bap_cheese_burger_bap']] = ((('bap_burger_cheese' in piece_map) and ('bap' in piece_map)) and (person.hand in ["empty","bap",'bap_burger_cheese']))
        # "deliver_cheeseburger",
        can_reach_state_array[state_map['deliver_cheeseburger']] = ("bap_burger_cheese_bap" in piece_map) and (person.hand in ["empty",'bap_burger_cheese_bap'])
        return can_reach_state_array

    #Scale by how far away we are from the emission target
    def distance_factor(self, paths_lens, idx):
        total = 0
        for i in range(len(paths_lens)):
            if paths_lens[i] != -1:
                total += paths_lens[i]
        return total/paths_lens[idx]


    def repeat_penalty(self,i):
        if len(self.state_history) == 0:
            return 1
        else:
            print("last: " + str(self.state_history[-1]) + " now: " + str(i))
            if self.state_history[-1] == i:
                return 0.25
            else:
                if len(self.state_history) == 1:
                    return 1
                if self.state_history[-2] == i:
                    return 0.25
                else:
                    return 1
            

    def emissions_scale(self,idx):
        for i in range(self.ticks_since_state_change):
            if self.paths_lens_history[i-1][idx] <= self.paths_lens_history[i][idx]:
                return 0.75
        return 1

    def update_transition_probabilities(self):
        #Normalise here and adjust for distance
        n = np.zeros(10)
        last_paths_lens = self.paths_lens_history[-1]
        for i in range(len(last_paths_lens)):
            if last_paths_lens[i] != -1:
                n[i] = self.distance_factor(last_paths_lens,i) * self.repeat_penalty(i) * self.emissions_scale(i)

        n /= n.sum()
        print(n)
        self.transition_probabilities = (np.column_stack((n,n,n,n,n,n,n,n,n,n)))


    def update_emission_probabilites(self, person, grid_world, paths):
        self.emission_probabilities = np.zeros((5, 10))
        for i in range(len(paths)):
            if paths[i] != None:
                probs = self.get_ob_probs_to_piece(person, grid_world, paths[i])
                for k in range(5):
                    self.emission_probabilities[k, i] = probs[k]
     
    def get_ob_probs_to_piece(self, person, grid_world, paths):
        obs_lists = [self.path_to_obs_list(path, person) for path in paths]
        obs_head_lists = set([ob_list[0] for ob_list in obs_lists])
        probs = np.zeros((5))
        for ob in obs_head_lists:
            probs[ob] = 1.0 / len(obs_head_lists)
        return probs

    def get_piece_map_difference(self,old_piece_map,new_piece_map):
        a = set(new_piece_map.items())
        b = set(old_piece_map.items())
        return [[val[0] for val in b-a], [val[0] for val in a-b]]


    def determine_last_state(self,piece_map_difference):
        before = piece_map_difference[0]
        after = piece_map_difference[1]
        print(str(before) + ":" + str(after))
        if "raw_burger" in after:
            return state_map["grab_raw_burger"]
        if 'raw_burger' in before and 'burger_pan' in after:
            return state_map["cook_raw_burger"]
        if ('cooked_burger_pan' in before or 'burger_pan' in before) and 'cooked_burger' in after:
            return state_map["grab_cooked_burger"]
        if 'cheese' in after:
            return state_map["grab_cheese"]
        if 'bap' in after:
            return state_map["grab_bap"]
        if 'bap' in before and 'cooked_burger' in before and 'bap_burger' in after:
            return state_map["combine_bap_burger"]
        if 'bap' in before and 'cheese' in before and 'bap_cheese' in after:
            return state_map["combine_bap_cheese"]
        if (('cheese' in before and 'bap_burger' in before) or ('cooked_burger' in before and 'bap_cheese' in before)) and "bap_burger_cheese" in after: 
            return state_map["combine_bap_cheese_burger"]
        if 'bap' in before and 'bap_burger_cheese' in before and 'bap_burger_cheese_bap' in after:
            return state_map['combine_bap_cheese_burger_bap']
        if 'bap_burger_cheese_bap' in before:
            return state_map['deliver_cheeseburger']
        return "none" 

    def update_user_action_probabilities(self, user_obs, person, robot, grid_world):
        print("###########################ß")
        piece_map = grid_world.get_piece_map(person.hand)

        piece_map_difference = self.get_piece_map_difference(self.old_piece_map,piece_map)
        self.old_piece_map = piece_map

        if len(piece_map_difference) > 0:
            last_state = self.determine_last_state(piece_map_difference)
            if last_state != "none":
                print(states[last_state])   
                for i in range(self.ticks_since_state_change):
                    self.users_real_actions.append(last_state)
                
                self.ticks_since_state_change = 0
                self.state_history.append(last_state)
        
                print(self.users_predicted_actions)
                print(self.users_real_actions)
                print(self.get_similarity(self.users_predicted_actions,self.users_real_actions))

        print(self.ticks_since_state_change)
        can_reach_state = self.generate_can_reach_state_array(person, piece_map)

        paths = [None]*len(can_reach_state)
        paths_lens = [-1]*len(can_reach_state)
        for i in range(len(can_reach_state)):
            if can_reach_state[i]:
                paths[i] = grid_world.find_shortest_paths("person", state_targets[states[i]][person.hand])
                #Currently doesn't account for facing the same direction
                paths_lens[i] = len(paths[i][0]) - 1
        self.paths_lens_history.append(paths_lens)

        #Check if you need to drop the item
        if (can_reach_state.sum() == 0):
            paths_to_drop = grid_world.find_shortest_paths("person", "empty_counter")
            prob_actions = np.array(self.get_ob_probs_to_piece(person, grid_world, paths_to_drop))
            prob_actions.shape = (5,1)
            self.users_predicted_actions.append(-1)
        else:
            self.update_transition_probabilities()
            self.update_emission_probabilites(person, grid_world, paths)

            self.prob_state = np.matmul(self.transition_probabilities, self.prob_state)
            self.users_predicted_actions.append(np.argmax(self.prob_state))
            prob_actions = np.matmul(self.emission_probabilities, self.prob_state)
        
        for idx, action in enumerate(prob_actions):
            print(str(obs[idx]) + ": " + "{:.3f}".format(action[0]))
        
        self.ticks_since_state_change+=1
        return list(prob_actions)


    def get_similarity(self, predicted, real):
        cnt = 0
        same = 0
        for i in range(len(real)):
            if (predicted[i] == real[i]):
                same += 1
            cnt += 1
        return same/cnt


    def print_accuracy_of_predictions(self):
        predicted = self.users_predicted_actions
        real = self.users_real_actions
       
        f = open("state_prob.txt", "w")
        f.write(str(real))
        f.write('\n')
        f.write(str(predicted[:len(real)]))
        f.write('\n')
        f.write(str(self.get_similarity(predicted,real)))
        f.close()



    def path_to_obs_list(self, path, person):
        obs = []
        for i in range(len(path) - 2):
            match (path[i][0] - path[i + 1][0], path[i][1] - path[i + 1][1]):
                case (-1, 0):
                    obs.append(obs_map["down"])
                case (0, 1):
                    obs.append(obs_map["left"])
                case (1, 0):
                    obs.append(obs_map["up"])
                case (0, -1):
                    obs.append(obs_map["right"])
        last_dir = ""
        match (path[-2][0] - path[-1][0], path[-2][1] - path[-1][1]):
            case (-1, 0):
                last_dir = obs_map["down"]
            case (0, 1):
                last_dir = obs_map["left"]
            case (1, 0):
                last_dir = obs_map["up"]
            case (0, -1):
                last_dir = obs_map["right"]
        if last_dir == obs_map[person.direction]:
            obs.append(obs_map["space"])
        else:
            obs.append(last_dir)
        return obs

    ##################################################################


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

                user_model.update_user_action_probabilities(
                    user_action, person, robot, grid_world
                )

        display_screen(end_time)

    # Quit pygame
    user_model.print_accuracy_of_predictions()
    pygame.quit()


if __name__ == "__main__":
    main()
