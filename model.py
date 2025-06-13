import torch
import time
import numpy as np
import logging
import torch_geometric_temporal
import glob
import os
from settings import constants
from collections import deque


# define logging file for the model process
logger = logging.getLogger("model")
logging.basicConfig(level=logging.DEBUG if constants.DEBUG else logging.INFO, format='[%(asctime)s] [%(name)s] %(message)s')
file_handler = logging.FileHandler("model.log")
formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# disjointed graph of landmarks
edge_index = torch.tensor([[0, 1, 1, 2, 2, 3, 3, 4, 0, 5, 5, 6, 6, 7, 7, 8, 5, 9, 9, 10, 10, 11, 11, 12, 9, 13, 13, 14, 14, 15, 15, 16, 13, 17, 17, 18, 18, 19, 19, 20, 17, 0, 
                           21, 22, 22, 23, 23, 24, 24, 25, 21, 26, 26, 27, 27, 28, 28, 29, 26, 30, 30, 31, 31, 32, 32, 33, 30, 34, 34, 35, 35, 36, 36, 37, 34, 38, 38, 39, 39, 40, 40, 41, 38, 21],
                           [1, 0, 2, 1, 3, 2, 4, 3, 5, 0, 6, 5, 7, 6, 8, 7, 9, 5, 10, 9, 11, 10, 12, 11, 13, 9, 14, 13, 15, 14, 16, 15, 17, 13, 18, 17, 19, 18, 20, 19, 0, 17, 
                           22, 21, 23, 22, 24, 23, 25, 24, 26, 21, 27, 26, 28, 27, 29, 28, 30, 26, 31, 30, 32, 31, 33, 32, 34, 30, 35, 34, 36, 35, 37, 36, 38, 34, 39, 38, 40, 39, 41, 40, 21, 38]])

# AAGCN network class
class GraphTransformer(torch.nn.Module):
    def __init__(self, input_size, num_classes, edges, num_nodes, num_blocks=4, hidden_dim=64, temporal_stride=True, residual=True, adaptive=True, attention=True, fc_layers=1, fc_units=128, dropout=0.2):

        super(GraphTransformer, self).__init__()
        
        self.aagcn_layers = []
        last = input_size
        for _ in range(num_blocks):
            self.aagcn_layers.append(torch_geometric_temporal.nn.AAGCN(last, hidden_dim, edges, num_nodes, temporal_stride, residual, adaptive, attention))
            last = hidden_dim
        self.aagcn_layers = torch.nn.ModuleList(self.aagcn_layers)

        self.temporal_pooling = torch.nn.AdaptiveAvgPool2d((1, None))

        self.linear_layers = []
        for _ in range(fc_layers):
            self.linear_layers.append(torch.nn.Linear(last, fc_units))
            self.linear_layers.append(torch.nn.ReLU())
            self.linear_layers.append(torch.nn.Dropout(dropout))
            last = fc_units
        self.linear_layers = torch.nn.ModuleList(self.linear_layers)
        
        self.output_layer = torch.nn.Linear(last, num_classes)

    def forward(self, x):
        for transformer in self.aagcn_layers:
            x = transformer(x)

        x = self.temporal_pooling(x)
        x = x.squeeze(2)
        x = x.mean(dim=-1)
        
        for fc in self.linear_layers:
            x = fc(x)

        x = self.output_layer(x)
        return x
    
def load_models():
    classification_models = []
    segmentation_models = []
    
    # load classification models from the corresponding folder
    for model_path in glob.glob(os.path.join("models", "classification", "model_*.pt")):
        model = GraphTransformer(3, 6, edge_index, 42, constants.C_NUM_BLOCKS, constants.C_HIDDEN_DIM, constants.C_TEMPORAL_STRIDE, constants.C_RESIDUAL, 
                                 constants.C_ADAPTIVE, constants.C_ATTENTION,constants.C_FC_LAYERS, constants.C_FC_UNITS, constants.C_FC_DROPOUT)
        
        state_dict = torch.load(model_path, map_location="cuda")
        model.load_state_dict(state_dict, strict=True)
        model.to("cuda")
        model.eval()  
        classification_models.append(model)

    # load segmentation models from the corresponding folder
    for model_path in glob.glob(os.path.join("models", "segmentation", "model_*.pt")):
        model = GraphTransformer(3, 1, edge_index, 42, constants.S_NUM_BLOCKS, constants.S_HIDDEN_DIM, constants.S_TEMPORAL_STRIDE, constants.S_RESIDUAL, 
                                 constants.S_ADAPTIVE, constants.S_ATTENTION,constants.S_FC_LAYERS, constants.S_FC_UNITS, constants.S_FC_DROPOUT)
        
        state_dict = torch.load(model_path, map_location="cuda")
        model.load_state_dict(state_dict, strict=True)
        model.to("cuda")
        model.eval()  
        segmentation_models.append(model)
    
    return classification_models, segmentation_models

def model_worker(frame_queue, result_queue, stop_event, model_ready_event, moving_flag):
    logger.info("Model worker started")

    # load classification and segmentation models
    classification_models, segmentation_models = load_models()
    logger.info("Models sucessfully loaded")
    ready = False
    last_heartbeat = time.time()

    # create sequences for the classification and segmentation
    c_sequence_queue = torch.zeros((1, 3, constants.C_SEQ_LEN, 42)).to("cuda")
    s_sequence_queue = torch.zeros((1, 3, constants.S_SEQ_LEN, 42)).to("cuda")

    # create queue for the segmentation results
    segmentation_queue = deque([])
    half_window = constants.TIMING_WINDOW // 2
    left_segmentation_sum = 0
    right_segmentation_sum = 0
    last_moving_flag = False

    try:
        while not stop_event.is_set():
            if not frame_queue.empty():
                # get landmarks from queue
                frame = frame_queue.get()

                # wait to detect both hands
                if frame[:, :21].sum() < 0.001 or frame[:, 21:].sum() < 0.001:
                    if time.time() - last_heartbeat > 4.5:
                        logger.info("Waiting to detect both hands...")
                    continue
                
                # inform system that both hands have been recognised
                if not ready:
                    logger.info("First complete frame received! system ready")
                    model_ready_event.set()
                    ready = True

                # update queues with the received landmarks (pops first landmarks and appends new landmarks)
                new_frame = torch.from_numpy(frame).pin_memory().to("cuda", non_blocking=True)
                s_sequence_queue[0, :, :-1, :] = s_sequence_queue[0, :, 1:, :]  # shift left
                s_sequence_queue[0, :, -1, :] = new_frame  # append new frame
                c_sequence_queue[0, :, :-1, :] = c_sequence_queue[0, :, 1:, :]  # shift left
                c_sequence_queue[0, :, -1, :] = new_frame  # append new frame

                # segment only if robot is not moving
                if not moving_flag.value:
                    if last_moving_flag:
                        # inform that robot has stopped and the models are back online
                        last_moving_flag = not last_moving_flag
                        logger.info("Robot stopped, waking models...")
                    with torch.no_grad():
                        seg_preds = []
                        # get segmentation prediction for each segmentation model
                        for model in segmentation_models:
                            pred = model(s_sequence_queue[:, :, -constants.S_SEQ_LEN:, :])
                            pred = pred.squeeze(-1)
                            pred = torch.sigmoid(pred)
                            seg_preds.append(pred)

                        # predict segmentation by averaging predictions (ensemble prediction)
                        seg_preds = torch.stack(seg_preds, dim=0)
                        mean_seg_pred = seg_preds.mean(dim=0)
                        mean_seg_pred = (mean_seg_pred > 0.5).float().cpu().item()
                        logger.debug(f"Segmentation result: {mean_seg_pred}")
                    
                    if len(segmentation_queue) < constants.TIMING_WINDOW:
                        # fill segmentation queue until it reaches full size
                        segmentation_queue.append(mean_seg_pred)

                        # update count of each window half
                        if len(segmentation_queue) <= half_window:
                            left_segmentation_sum += mean_seg_pred
                        else:
                            right_segmentation_sum += mean_seg_pred
                    else:
                        # append new segmentation prediction and pop first prediction in the queue
                        # update count of each window half
                        right_segmentation_sum -= segmentation_queue[half_window]
                        left_segmentation_sum += segmentation_queue[half_window]
                        left_segmentation_sum -= segmentation_queue.popleft()
                        right_segmentation_sum += mean_seg_pred
                        segmentation_queue.append(mean_seg_pred)

                        # metric to decide when there is a transition between human movement (0) and static (1)
                        # intuition is there must be more new static predictions (right window) and more old movement predictions (left window)
                        if right_segmentation_sum - left_segmentation_sum > constants.TIMING_THRESHOLD*half_window:
                            logger.info("Timing predicted!")
                            with torch.no_grad():
                                class_preds = []

                                # get classification predictions from all models
                                for model in classification_models:
                                    pred = model(c_sequence_queue)
                                    pred = torch.softmax(pred, dim=1)
                                    class_preds.append(pred)

                                # average predictions to get a single ensemble class prediction
                                class_preds = torch.stack(class_preds, dim=0)
                                mean_class_pred = class_preds.mean(dim=0)
                                class_final = torch.argmax(mean_class_pred, dim=1).cpu().item()
                                result_queue.put(class_final)

                            # activate robot moving flag and reset segmentation queue and window counts
                            logger.info("Trigger sent to robot, models in sleep mode!")
                            moving_flag.value = True
                            segmentation_queue = deque([])
                            left_segmentation_sum = 0
                            right_segmentation_sum = 0

            if time.time() - last_heartbeat > 5:
                logger.info("Model still processing...")
                last_heartbeat = time.time()

            time.sleep(0.01)

    except Exception as e:
        logger.error("Model worker crashed", exc_info=True)

    finally:
        logger.info("Model worker exiting")
