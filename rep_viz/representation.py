import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from rep_viz.plotter import Plotter


class NearestNeighbour(object):
    def __init__(self, image2feature_dict, feature_size):
        """
        Gets the nearest neighbour using cosine similarity metric
        :param image2feature_dict: The key, value pair of image and its corresponding feature
        :param feature_size: The dimension of each feature of each image
        """
        self.image2feature_dict = image2feature_dict
        self.numimages = len(self.image2feature_dict)
        self.feature_size = feature_size
        self.im2index = dict()
        self.index2im = dict()
        self.__vectorify()
        self.__construct_cs_matrix()

    def __vectorify(self):
        """
        Converts the map to a vector of dimension (num_images x feature_dim) and saves it as self.X
        :return: None
        """
        self.X = np.zeros([self.numimages, self.feature_size])
        self.Y = []
        counter = 0
        for key, value in self.image2feature_dict.iteritems():
            object_id = int(key.split('/')[-1].split('_')[0])
            self.Y.append(object_id)
            self.im2index[key] = counter
            self.index2im[counter] = key
            self.X[counter, :] = value
            counter += 1

        self.Y = np.array(self.Y)

    def __construct_cs_matrix(self):
        """
        Creates as cosine similarity matrix between self.X and itself.
        :return: None
        """
        self.similarity_mat = cosine_similarity(self.X, self.X, dense_output=True)
        # print self.similarity_mat

    def save_nearest_neighbors(self, num_neighbors, out_file):
        """
        Saves the nearest neighbors of the key images in the test file
        :param num_neighbors: Number of neighbors to be retrieved
        :param out_file: The output file where the neighbours of each image is to be stored
        :return: None
        """
        neighbor_list = self.compute_nearest_neighbors(num_neighbors)
        # save it
        with open(out_file, 'wb') as out:
            for item in neighbor_list:
                print>>out, item

    def compute_nearest_neighbors(self, num_neighbors):
        result_list = []
        for key, value in self.im2index.iteritems():
            neighbor_list = [key]
            similarity_scores = self.similarity_mat[value]
            # removes best match as same as key
            ind = np.argpartition(similarity_scores, -(num_neighbors + 1))[-(num_neighbors + 1):-1]
            ind = ind[np.argsort(similarity_scores[ind])]
            neighbors = [self.index2im[x] for x in ind]
            neighbor_list.extend(neighbors)

            result_list.append(neighbor_list)

        # compute neighbor statistics
        NearestNeighbour.compute_neighbor_stats(result_list, num_neighbors)

        # plot the TSNE plot
        self.plot_tsne()

        return result_list

    def plot_tsne(self):
        """
        Plots the T-SNE for visualization of the objects and their separation in 2D space
        :return:
        """
        plotter = Plotter(self.X, self.Y)
        plotter.reduce() # reduces to 100 dimensions using PCA and then to 2 dimensions using T-SNE
        plotter.plot()
        plt.show()

    @staticmethod
    def compute_neighbor_stats(result_list, num_neighbors):
        """
        Compute the statistics of found neighbors and displays the histogram statistics of the frequency of images
        with a given number of neighbors of same object class as the key.
        :param result_list: The neighbor list obtained for each key, with key being the first element of the list
        :param num_neighbors: Number of neighbors used
        :return: None
        """
        object_list = [[int(x.split('/')[-1].split('_')[0]) for x in row] for row in result_list]
        image_object = [x[0] for x in object_list]
        neighbors_object = [x[1:] for x in object_list]
        image = [x[0] for x in result_list]
        neighbors = [x[1:] for x in result_list]
        nb_bool = [[x == y and im != n for x, n in zip(row, nb)] for row, y, nb, im in
                   zip(neighbors_object, image_object, neighbors, image)]
        assert np.array(nb_bool).shape[1] == num_neighbors, 'Neighbor info not obtained'
        total_true_nb = [sum(x) for x in nb_bool]

        total_matches = sum(total_true_nb)
        assert len(total_true_nb) == len(image_object), 'Something is wrong...'
        average_match_per_obj = total_matches/float(len(total_true_nb))

        print 'Average Neighbor found per object: %f' % average_match_per_obj

        for i, x in enumerate(total_true_nb):
            if x == 6:
                print '------'
                print image[i]
                print neighbors[i]
                print '------'

        # plot the histogram plot for number of images with more than x matches
        # print plt.hist(total_true_nb, histtype='bar', rwidth=0.8)
        print plt.hist(total_true_nb, bins=np.arange(np.min(total_true_nb), np.max(total_true_nb)+1), align='left')
        # plt.show()
