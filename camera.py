import pyrealsense2 as rs
import numpy as np
import time
import logging
from settings import constants
from handtracker import HandTracker
import os
import cv2 as cv


# define logging file for the camera process
logger = logging.getLogger("camera")
logging.basicConfig(level=logging.DEBUG if constants.DEBUG else logging.INFO, format='[%(asctime)s] [%(name)s] %(message)s')
file_handler = logging.FileHandler("camera.log")
formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_hand_tracker():
    # initialise hand tracker class
    hand_tracker = HandTracker()
    hand_tracker.reset()
    return hand_tracker

def camera_loop(frame_queue, stop_event):
    try:
        # variable to subsample video
        frame_count = 0

        # initialize pipeline and config
        pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(pipeline)
        try:
            pipeline_profile = config.resolve(pipeline_wrapper)
        except RuntimeError:
            raise

        device = pipeline_profile.get_device()

        # check if camera has the necessary capabilities
        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            raise IOError("RGB camera not found!")

        config.enable_stream(rs.stream.color, constants.STREAM_WIDTH, constants.STREAM_HEIGHT, rs.format.bgr8, constants.STREAM_FPS)

    except Exception as e:
        logger.error("Camera error initializing", exc_info=e)
        return
  
    try:
        # create hand tracker and start camera stream
        hand_tracker = get_hand_tracker()
        pipeline.start(config)

        # load normalisation vectors        
        min_vector = np.transpose(np.load(os.path.join("settings", "min_vector.npy")).reshape((-1, 3)))
        max_vector = np.transpose(np.load(os.path.join("settings", "max_vector.npy")).reshape((-1, 3)))

        logger.info("Camera started")

        last_heartbeat = time.time()

        while not stop_event.is_set():
            # get frame from camera
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            
            # process frame
            color_frame = np.asanyarray(color_frame.get_data())
            color_frame = cv.cvtColor(color_frame, cv.COLOR_BGR2RGB)

            # reduce framerate, if fps == 30 and SKIP_FRAMES == 2, then true_fps == 10
            # requesting a higher framerate leads to lower motion blur
            if frame_count == constants.SKIP_FRAMES:
                frame_count = 0

                # get landmarks from RGB frame
                hand_poses = hand_tracker.get_hand_poses_from_frame(color_frame)

                # mask hands that were detected (hands not yet detected are represented as zeros)
                mask = hand_poses.sum(axis=0) > 0.001

                # normalise detected hands
                hand_poses =  np.where(mask, np.clip((hand_poses - min_vector) / (max_vector - min_vector), 0, 1), hand_poses)
                
                # add landmarks to queue
                if not frame_queue.full():
                    frame_queue.put(hand_poses)
                else:
                    logger.warning("Camera queue full!")
            else:
                frame_count += 1

            if time.time() - last_heartbeat > 5:
                logger.info("Camera running...")
                last_heartbeat = time.time()

    except Exception as e:
        logger.error("Camera error", exc_info=True)
    finally:
        pipeline.stop()
        while not frame_queue.empty():
            frame_queue.get()
        logger.info("Camera stopped")
