# Real-time Human-Robot Collaborative Assembly

## Structure
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Notes and Limitations](#notes-and-limitations)

## Overview
This system is the culmination of my PhD thesis. From it a user can perform a collaborative assembly 
with its robot counterpart and the system correctly identifies when the robot should act and what 
action to do.

The studied assembly corresponds to the previously developed
[CT-Benchmark](https://github.com/Robotics-and-AI/collaborative-tasks-benchmark). It contains a 
total of 6 sub-assemblies that can be assigned in any given order: Bridge, Dovetail, Hospital, 
Museum + Triangle, Snap and Wheel. Each sub-assembly is comprised of a series of immutable 
task modules assigned to the human or robot.

Three main modules were designed and implemented:
- Perception module;
- Timing module;
- Action classification module.

To train the timing and action classification modules the
[CT-A Dataset](https://zenodo.org/records/15491644) was used.

__Perception Module__

The perception module receives RGB data from an Intel Realsense D435i camera and converts it into 
hand landmark representations. By using hand landmarks instead of RGB frames the system requires
less data to be trained and is more robust against appearance variations such as clothing, 
lighting, background clutter, and camera noise.

__Timing Module__

The timing module consists of a segmentation ensemble of Two-Stream Adaptive Graph Convolutional 
Networks (2s-AGCN) that segments each frame as the human moving (label 0) or being static (label 1). 
Then a window technique is used to robustly identify moving to static transitions.

__Action Classification Module__

The action classification module consists of a classification ensemble of 2s-AGCN models that classify 
the current sub-assembly being performed. The required task is then selected from the current 
sub-assembly.

## System Architecture
```bash
└── settings
    ├── constants.py
    ├── max_vector.npy
    └── min_vector.npy
```

Files with system settings and vectors for landmark normalisation.

```bash
└── robot_setup
    └── iiwaPy3
```

[Library iiwaPy3](https://github.com/Modi1987/iiwaPy3) for the interface
between python and the KUKA iiwa robot.

```bash
├── io_classes
│   └── file_manager.py
└── robot_setup
    ├── sub_assemblies
    ├── robot_communication.py
    ├── robotic_system.py
    ├── task_data.py
    └── tools.json
```

Classes and tools developed to establish a connection with the robot
and to manage and run robot programs. They have been previously [developed
for the design of a GUI](https://github.com/Modi1987/iiwaPy3) to 
interact with a KUKA iiwa robot.

```bash
└── arduino_code
    └── arduino_code.ino
```
Arduino code to facilitate communication between human and robot:
- Two  buttons to send information to the robot;
- Buzzer to receive information from the robot.

```bash
└── main.py
```

Main system process. Upon start, the main process waits for a white
button press (user input to start system). 

The controller process is started after receiving the user input. If no errors occur
on startup, three buzzes are played on the arduino board with ascending frequencies. 
If the robot failed to connect but the model process is online the arduino board buzzes twice.

If a red button press is detected in the arduino board a system shutdown
is triggered and two buzzes are played on the arduino board with descending frequencies.

```bash
└── controller.py
```

File to initialise the camera, model and robot processes.

```bash
├── camera.py
└── handtracker.py
```

The camera process receives a data stream from a Realsense D435i 
camera and converts it into hand landmarks using the
[mediapipe library](https://ai.google.dev/edge/mediapipe/solutions/guide).
The hand landmarks are then passed into a queue to be used by the model
process.

```bash
├── models
│   ├── classification
│   │   ├── model_0.pt
│   │   ├── model_1.pt
│   │   ├── model_2.pt
│   │   ├── model_3.pt
│   │   └── model_4.pt
│   └── segmentation
│       ├── model_0.pt
│       ├── model_1.pt
│       ├── model_2.pt
│       ├── model_3.pt
│       └── model_4.pt
└── model.py
```

The model process loads both 2s-AGCN segmentation and classification models and starts reading 
landmarks from the queue. It keeps two buffers, one for the segmentation
and one for the classification. As explained previously, the segmentation is run at every time
step and detects whether the robot should act. In such moments, the classification models predict 
the sub-assembly being assembled. 

## Notes and Limitations

The provided code has been implemented for the specific case of a KUKA iiwa robot controlled
with the [iiwaPy3 library](https://github.com/Modi1987/iiwaPy3) for the assembly of 
the [CT-Benchmark](https://github.com/Robotics-and-AI/collaborative-tasks-benchmark), while using data collected by an Intel Realsense camera. For different
settings the code must be adapted. 
