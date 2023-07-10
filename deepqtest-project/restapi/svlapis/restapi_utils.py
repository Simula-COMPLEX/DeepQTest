# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/4/15 17:32
# @Author  : Chengjie
# @File    : restapi_utils.py


import math
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pyntcloud import PyntCloud

path = '../experiment'


class ProcessImage(object):
    def __init__(self, SENSORS):
        self.sensor = SENSORS

    def save_image(self, sensor_name, image_ID, tag, experiment_tag):
        """
        save images
        :param experiment_tag:
        :param tag:
        :param image_ID:
        :param sensor_name: from which sensor the image to save
        :return:
        """
        camera = None
        image_path = path + '/{}/Image/'.format(experiment_tag) + str(sensor_name).replace(' ', '_')

        if not os.path.exists(image_path):
            os.makedirs(image_path)
        for sensor in self.sensor:
            if sensor.name == sensor_name:
                camera = sensor
                break

        filename = path + '/{}/Image/'.format(experiment_tag) + str(sensor_name).replace(' ', '_') + '/' + str(
            image_ID) + '_' + str(tag) + '.jpg'
        camera.save(filename, quality=75)
        return filename

    def save_lidar(self, tag, experiment_tag):
        lidar_path = path + '/{}/Lidar'.format(experiment_tag)
        if not os.path.exists(lidar_path):
            os.mkdir(lidar_path)

        filename = path + '/{}/Lidar'.format(experiment_tag) + '/lidar_' + str(tag) + '.pcd'
        for sensor in self.sensor:
            if sensor.name == "Lidar":
                sensor.save(filename)
        return filename

    @staticmethod
    def get_image(filename):
        im = cv2.imread(filename, 1)
        im = im[:, :, 0] * 0.299 + im[:, :, 1] * 0.587 + im[:, :, 2] * 0.114
        im = cv2.resize(im, (int(im.shape[1] * 0.2), int(im.shape[0] * 0.2)), interpolation=cv2.INTER_AREA)
        screen_height, screen_width = im.shape
        im = im[int(screen_height * 0.2):int(screen_height * 0.9), :]
        im = im.astype(np.float32)
        im = im / 255
        return im

    @staticmethod
    def get_RGB_image(filename):
        im = cv2.imread(filename, 1)
        screen_height, screen_width, _ = im.shape
        im = cv2.resize(im, (int(im.shape[1] * 0.3), int(im.shape[0] * 0.3)), interpolation=cv2.INTER_AREA)
        im = im[int(screen_height * 0.1):(int(screen_height * 0.1) + 160), 100:476]
        return im

    @staticmethod
    def get_four_frames(path, tag):
        image1 = ProcessImage.get_image(path + '0_' + tag + '.jpg')
        image2 = ProcessImage.get_image(path + '1_' + tag + '.jpg')
        image3 = ProcessImage.get_image(path + '2_' + tag + '.jpg')
        image4 = ProcessImage.get_image(path + '3_' + tag + '.jpg')
        image_combined = np.dstack((image1, image2, image3, image4))
        return image_combined

    @staticmethod
    def process_image(im):
        im = im[:, :, 0] * 0.299 + im[:, :, 1] * 0.587 + im[:, :, 2] * 0.114
        print('image: ', (int(im.shape[1] * 0.2), int(im.shape[0] * 0.2)))
        im = cv2.resize(im, (int(im.shape[1] * 0.2), int(im.shape[0] * 0.2)), interpolation=cv2.INTER_AREA)
        screen_height, screen_width = im.shape
        im = im[int(screen_height * 0.4):int(screen_height * 0.85), :]
        print(im.shape)
        im = im.astype(np.float32)
        im = im / 255
        return im


class ProcessLidar(object):

    @staticmethod
    def get_lidar_Depth_view(filename):
        cloud = PyntCloud.from_file(filename)
        bird = lidar_to_bird_view(np.asarray(cloud.points))
        HRES = 0.35  # horizontal resolution (assuming 20Hz setting)
        VRES = 0.4  # vertical res
        VFOV = (-24.9, 2.0)  # Field of view (-ve, +ve) along vertical axis
        Y_FUDGE = 5  # y fudge factor for velodyne HDL 64E

        lidar_to_2d_front_view(np.asarray(cloud.points), v_res=VRES, h_res=HRES, v_fov=VFOV, val="depth",
                               saveto="./lidar_depth.png", y_fudge=Y_FUDGE)
        return 'lidar'

    @staticmethod
    def get_lidar_bird_view(filename):
        cloud = PyntCloud.from_file(filename)
        bird = lidar_to_bird_view(np.asarray(cloud.points))
        return bird


def lidar_to_bird_view(lidar):
    """

    :param lidar:
    :return:
    """

    # Lidar parameters
    TOP_Y_MIN = -30
    TOP_Y_MAX = +30
    TOP_X_MIN = -30
    TOP_X_MAX = 30
    TOP_Z_MIN = -3.5
    TOP_Z_MAX = 0.6

    TOP_X_DIVISION = 0.2
    TOP_Y_DIVISION = 0.2
    TOP_Z_DIVISION = 0.3

    idx = np.where(lidar[:, 0] > TOP_X_MIN)
    lidar = lidar[idx]
    idx = np.where(lidar[:, 0] < TOP_X_MAX)
    lidar = lidar[idx]

    idx = np.where(lidar[:, 1] > TOP_Y_MIN)
    lidar = lidar[idx]
    idx = np.where(lidar[:, 1] < TOP_Y_MAX)
    lidar = lidar[idx]

    idx = np.where(lidar[:, 2] > TOP_Z_MIN)
    lidar = lidar[idx]
    idx = np.where(lidar[:, 2] < TOP_Z_MAX)
    lidar = lidar[idx]

    pxs = lidar[:, 0]
    pys = lidar[:, 1]
    pzs = lidar[:, 2]
    prs = lidar[:, 3]
    qxs = ((pxs - TOP_X_MIN) // TOP_X_DIVISION).astype(np.int32)
    qys = ((pys - TOP_Y_MIN) // TOP_Y_DIVISION).astype(np.int32)
    # qzs=((pzs-TOP_Z_MIN)//TOP_Z_DIVISION).astype(np.int32)
    qzs = (pzs - TOP_Z_MIN) / TOP_Z_DIVISION
    quantized = np.dstack((qxs, qys, qzs, prs)).squeeze()

    X0, Xn = 0, int((TOP_X_MAX - TOP_X_MIN) // TOP_X_DIVISION) + 1
    Y0, Yn = 0, int((TOP_Y_MAX - TOP_Y_MIN) // TOP_Y_DIVISION) + 1
    Z0, Zn = 0, int((TOP_Z_MAX - TOP_Z_MIN) / TOP_Z_DIVISION)
    height = Xn - X0
    width = Yn - Y0
    channel = Zn - Z0 + 2
    top = np.zeros(shape=(height, width, channel), dtype=np.float32)

    if 1:  # new method
        for x in range(Xn):
            ix = np.where(quantized[:, 0] == x)
            quantized_x = quantized[ix]
            if len(quantized_x) == 0: continue
            yy = -x

            for y in range(Yn):
                iy = np.where(quantized_x[:, 1] == y)
                quantized_xy = quantized_x[iy]
                count = len(quantized_xy)
                if count == 0: continue
                xx = -y

                top[yy, xx, Zn + 1] = min(1, np.log(count + 1) / math.log(32))
                max_height_point = np.argmax(quantized_xy[:, 2])
                top[yy, xx, Zn] = quantized_xy[max_height_point, 3]

                for z in range(Zn):
                    iz = np.where((quantized_xy[:, 2] >= z) & (quantized_xy[:, 2] <= z + 1))
                    quantized_xyz = quantized_xy[iz]
                    if len(quantized_xyz) == 0: continue
                    zz = z

                    max_height = max(0, np.max(quantized_xyz[:, 2]) - z)
                    top[yy, xx, zz] = max_height

    return top


def lidar_to_2d_front_view(points,
                           v_res,
                           h_res,
                           v_fov,
                           val="depth",
                           cmap="jet",
                           saveto=None,
                           y_fudge=0.0
                           ):
    """ Takes points in 3D space from LIDAR data and projects them to a 2D
        "front view" image, and saves that image.

    Args:
        points: (np array)
            The numpy array containing the lidar points.
            The shape should be Nx4
            - Where N is the number of points, and
            - each point is specified by 4 values (x, y, z, reflectance)
        v_res: (float)
            vertical resolution of the lidar sensor used.
        h_res: (float)
            horizontal resolution of the lidar sensor used.
        v_fov: (tuple of two floats)
            (minimum_negative_angle, max_positive_angle)
        val: (str)
            What value to use to encode the points that get plotted.
            One of {"depth", "height", "reflectance"}
        cmap: (str)
            Color map to use to color code the `val` values.
            NOTE: Must be a value accepted by matplotlib's scatter function
            Examples: "jet", "gray"
        saveto: (str or None)
            If a string is provided, it saves the image as this filename.
            If None, then it just shows the image.
        y_fudge: (float)
            A hacky fudge factor to use if the theoretical calculations of
            vertical range do not match the actual data.

            For a Velodyne HDL 64E, set this value to 5.
    """

    # DUMMY PROOFING
    assert len(v_fov) == 2, "v_fov must be list/tuple of length 2"
    assert v_fov[0] <= 0, "first element in v_fov must be 0 or negative"
    assert val in {"depth", "height", "reflectance"}, \
        'val must be one of {"depth", "height", "reflectance"}'

    x_lidar = points[:, 0]
    y_lidar = points[:, 1]
    z_lidar = points[:, 2]
    r_lidar = points[:, 3]  # Reflectance
    # Distance relative to origin when looked from top
    d_lidar = np.sqrt(x_lidar ** 2 + y_lidar ** 2)
    # Absolute distance relative to origin
    # d_lidar = np.sqrt(x_lidar ** 2 + y_lidar ** 2, z_lidar ** 2)

    v_fov_total = -v_fov[0] + v_fov[1]

    # Convert to Radians
    v_res_rad = v_res * (np.pi / 180)
    h_res_rad = h_res * (np.pi / 180)

    # PROJECT INTO IMAGE COORDINATES
    x_img = np.arctan2(-y_lidar, x_lidar) / h_res_rad
    y_img = np.arctan2(z_lidar, d_lidar) / v_res_rad

    # SHIFT COORDINATES TO MAKE 0,0 THE MINIMUM
    x_min = -360.0 / h_res / 2  # Theoretical min x value based on sensor specs
    x_img -= x_min  # Shift
    x_max = 360.0 / h_res  # Theoretical max x value after shifting

    y_min = v_fov[0] / v_res  # theoretical min y value based on sensor specs
    y_img -= y_min  # Shift
    y_max = v_fov_total / v_res  # Theoretical max x value after shifting

    y_max += y_fudge  # Fudge factor if the calculations based on
    # spec sheet do not match the range of
    # angles collected by in the data.

    # WHAT DATA TO USE TO ENCODE THE VALUE FOR EACH PIXEL
    if val == "reflectance":
        pixel_values = r_lidar
    elif val == "height":
        pixel_values = z_lidar
    else:
        pixel_values = -d_lidar

    # PLOT THE IMAGE
    cmap = "jet"  # Color map to use
    dpi = 100  # Image resolution
    fig, ax = plt.subplots(figsize=(x_max / dpi, y_max / dpi), dpi=dpi)
    ax.scatter(x_img, y_img, s=1, c=pixel_values, linewidths=0, alpha=1, cmap=cmap)
    ax.set_axis_bgcolor((0, 0, 0))  # Set regions with no points to black
    ax.axis('scaled')  # {equal, scaled}
    ax.xaxis.set_visible(False)  # Do not draw axis tick marks
    ax.yaxis.set_visible(False)  # Do not draw axis tick marks
    plt.xlim([0, x_max])  # prevent drawing empty space outside of horizontal FOV
    plt.ylim([0, y_max])  # prevent drawing empty space outside of vertical FOV
    print(fig)

    if saveto is not None:
        fig.savefig(saveto, dpi=dpi, bbox_inches='tight', pad_inches=0.0)
    else:
        fig.show()
