import numpy as np
from skimage.feature import hog

POSTIVE_REWARD = 10
NEGATIVE_REWARD = -10
DELAY_REWARD = -1


class Environment(object):
    def __init__(self, original_image, initial_gamestate, grid_dim,
                 puzzle_pieces, image_dim, window, stride, num_channels):
        self.original_image = original_image
        self.jigsaw_image = np.zeros([image_dim, image_dim])
        self.initial_gamestate = initial_gamestate
        self.gamestate = initial_gamestate
        self.grid_dim = grid_dim
        self.puzzle_pieces = puzzle_pieces
        self.image_dim = image_dim
        self.state_height = self.gamestate[0]
        self.state_width = self.state_height
        self.window = tuple(window)
        self.num_gradients = num_channels
        self.stride = stride
        self.action = None
        self.placed_pieces = []
        self.already_present_flag = False
        self.already_absent_flag = False
        self.terminal = False
        self.jigsaw_split = np.split(np.array(range(self.image_dim)), self.grid_dim)

    def __update_state(self):
        image_id, jigwaw_range, removal = self.map_action()
        if removal:
            if image_id in self.placed_pieces:
                self.placed_pieces.remove(image_id)
                self.already_absent_flag = False
            else:
                self.already_absent_flag = True
        else:
            if image_id not in self.placed_pieces:
                self.placed_pieces.append(image_id)
                self.already_present_flag = False
            else:
                self.already_present_flag = True

        # update the next state only when it is required
        if self.already_absent_flag or self.already_present_flag:
            self.update_jigsaw(image_id, jigwaw_range, removal)
            hog_gradients = hog(self.jigsaw_image,
                                orientations=self.num_gradients,
                                pixels_per_cell=self.window,
                                cells_per_block=(1, 1), visualise=False)
            hog_gradients = hog_gradients.resize((self.state_height, self.state_width, self.num_gradients))
            assert self.gamestate.shape() == hog_gradients.shape(), "The state dimension is trying to be altered"
            self.gamestate = hog_gradients

    def set_action(self, action):
        self.action = action
        self.__update_state()

    def __get_reward(self):
        # get the reward based on the afterstate
        if self.terminal:
            if self.jigsaw_image == self.original_image:
                return POSTIVE_REWARD
            else:
                return NEGATIVE_REWARD
        else:
            return DELAY_REWARD

    def __get_next_state(self):
        return self.gamestate

    def __is_terminal(self):
        # check if self.gamestate is terminal
        if len(self.placed_pieces) == len(self.puzzle_pieces):
            self.terminal = True
        return self.terminal

    def get_state_reward_pair(self):
        return self.__get_reward(), self.__get_next_state(), self.__is_terminal()

    def map_action(self):
        image_id = int(self.action / (self.state_height * self.state_width))
        removal = False
        if image_id in self.placed_pieces:
            removal = True
        place_id = self.action % (self.state_height * self.state_height)
        place_row = place_id / self.state_width

        # get the range for placing the jigsaw piece in the jigsaw image
        row_range = self.jigsaw_split[place_row]
        col_range = row_range

        return image_id, (row_range[0], row_range[-1], col_range[0], col_range[-1]), removal

    def update_jigsaw(self, image_id, placing_range, removal):
        x_s, x_e, y_s, y_e = placing_range
        if removal:
            self.jigsaw_image[x_s:x_e, y_s, y_e] = np.zeros([x_e-x_s, y_e-y_s])
        else:
            self.jigsaw_image[x_s:x_e, y_s, y_e] = self.puzzle_pieces[image_id]

    def get_state(self):
        return self.gamestate

    def update_puzzle_pieces(self, puzzle_pieces):
        self.puzzle_pieces = puzzle_pieces

    def update_original_image(self, original_image):
        self.original_image = original_image

    def reset(self):
        self.jigsaw_image = np.zeros([self.image_dim, self.image_dim])
        self.gamestate = self.initial_gamestate
        self.placed_pieces = []
        self.already_present_flag = False
        self.already_absent_flag = False
        self.terminal = False