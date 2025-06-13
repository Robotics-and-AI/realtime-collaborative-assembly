import math
from settings import constants
import mediapipe as mp
import numpy as np


# class to get hand-tracking data from frames
class HandTracker:
    def __init__(self):
        # hand tracking object
        self._hand_tracker = mp.solutions.hands.Hands(max_num_hands=2, model_complexity=1,
                                                      min_detection_confidence=0.3, min_tracking_confidence=0.3,
                                                      static_image_mode=True)

        # last hand vectors
        self._last_left_hand = None
        self._last_right_hand = None

        # reset values for last saved hands
        self.reset()

    def reset(self):
        """
        Reset last hand tracking values.
        """
        self._last_left_hand = np.zeros((3, 21))
        self._last_right_hand = np.zeros((3, 21))

    def _calculate_squared_distance(self, point_1: np.array, point_2: np.array) -> float:
        """
        Squared Euclidean distance between two points.

        :param point_1: coordinates of point 1
        :param point_2: coordinates of point 2
        :return: Squared Euclidean distance between 2 points
        """

        return ((point_1 - point_2) ** 2).sum()

    def _calculate_hand_centre(self, hand: np.array) -> tuple:
        """
        Get centre coordinates from landmark coordinates.

        :param hand: hand coordinates
        :return: Centre coordinates of hand
        """

        # centre defined as the point between landmarks with indexes 0 and 9.
        return (math.floor((hand[0, 0] + hand[0, 9]) * constants.STREAM_WIDTH / 2),
                math.floor((hand[1, 0] + hand[1, 9]) * constants.STREAM_HEIGHT / 2))

    def get_hand_poses_from_frames(self, rgb_frames: list) -> np.array:
        """
        Get hand vectors for all frames and return in list.

        :param rgb_frames: Frames to calculate hand poses from
        :param depth_frames: Depth frames to add depth value of hand centre
        :return: list of hand poses
        """

        hands = []

        for frame, depth in zip(rgb_frames):
            hand = self.get_hand_poses_from_frame(frame, depth)
            hands.append(hand)

        return np.array(hands)

    def _get_vector_from_landmarks(self, landmarks: dict) -> np.array:
        """
        Transform landmark data into matrix of dimension [number of coordinate axis, number of landmarks]

        :param landmarks: Landmark data calculated from mediapipe
        :param depth_frame: depth frame to gather depth information of hand centre
        :return: array of x, y and z coordinates for each landmark
        """

        hands = np.transpose(np.array([[landmark.x, landmark.y, landmark.z] for landmark in landmarks]))

        return hands

    def get_hand_poses_from_frame(self, rgb_frame: np.array) -> np.array:
        """
        Calculate hand pose from rgb frame.

        :param rgb_frame: frame to calculate hand landmarks
        :return: array of hand landmarks
        """

        # calculate hand poses
        rgb_frame.flags.writeable = False
        hand_pose = self._hand_tracker.process(rgb_frame)
        rgb_frame.flags.writeable = True

        # if no hand detected, keep previous landmarks
        if not hand_pose.multi_hand_landmarks:
            return np.concatenate((self._last_left_hand, self._last_right_hand), axis=1)

        if len(hand_pose.multi_hand_landmarks) == 1:
            # get calculated hand
            hand = self._get_vector_from_landmarks(hand_pose.multi_hand_landmarks[0].landmark)

            # find last hand closer to hand found and update its value
            if self._calculate_squared_distance(hand, self._last_left_hand) < \
                    self._calculate_squared_distance(hand, self._last_right_hand):
                self._last_left_hand = hand
            else:
                self._last_right_hand = hand

            # swap hands if x coordinate of the right hand is bigger than left
            if self._calculate_hand_centre(self._last_left_hand)[0] < \
                    self._calculate_hand_centre(self._last_right_hand)[0]:
                self._last_left_hand, self._last_right_hand = self._last_right_hand, self._last_left_hand

        elif len(hand_pose.multi_hand_landmarks) > 2:
            # initialize best distance to hands
            best_left_dist, best_right_dist = math.inf, math.inf

            # for each found hand find the hand that is closer to the last left and right hands
            for hand in hand_pose.multi_hand_landmarks:
                hand_vector = self._get_vector_from_landmarks(hand.landmark)
                left_dist = self._calculate_squared_distance(self._last_left_hand, hand_vector)
                right_dist = self._calculate_squared_distance(self._last_right_hand, hand_vector)

                # update closest hand to previous left hand
                if left_dist < best_left_dist:
                    self._last_left_hand = hand_vector
                    best_left_dist = left_dist

                # update closest hand to previous right hand
                if right_dist < best_right_dist:
                    self._last_right_hand = hand_vector
                    best_right_dist = right_dist

        elif len(hand_pose.multi_hand_landmarks) == 2:
            # get 2 calculated hands and assign left to the hand on the left side
            hand_1 = self._get_vector_from_landmarks(hand_pose.multi_hand_landmarks[0].landmark)
            hand_2 = self._get_vector_from_landmarks(hand_pose.multi_hand_landmarks[1].landmark)

            self._last_left_hand, self._last_right_hand = (hand_2, hand_1) if \
                self._calculate_hand_centre(hand_1)[0] < self._calculate_hand_centre(hand_2)[0] else (hand_1, hand_2)

        return np.concatenate((self._last_left_hand, self._last_right_hand), axis=1)
