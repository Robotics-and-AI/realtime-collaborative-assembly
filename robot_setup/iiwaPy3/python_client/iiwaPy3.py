from .Getters import Getters
from .PTP import PTP
from .RealTime import RealTime
from .Senders import Senders
from .Setters import Setters
from .mySock import mySock


class iiwaPy3:
    getters = 0
    realtime = 0
    generalPurpose = 0

    def __init__(self, ip, trans=(0, 0, 0, 0, 0, 0)):
        # print('This is a python3 wrapper for the KUKA Sunrise Toolbox')
        # print('For more info visit:')
        # print('https://github.com/Modi1987/KST-Kuka-Sunrise-Toolbox')
        port = 30001
        self.soc = mySock((ip, port), trans)
        self.set = Setters(self.soc)
        self.get = Getters(self.soc)
        self.sender = Senders(self.soc)
        self.rtl = RealTime(self.soc)
        self.ptp = PTP(self.soc)
        self.TCPtrans = trans

    def close(self):
        self.soc.close()

    def send(self, data):
        self.soc.send(data)

    # PTP motion
    """
    Joint space motion
    """

    def movePTPJointSpace(self, jpos, relVel):
        self.ptp.movePTPJointSpace(jpos, relVel)

    def movePTPHomeJointSpace(self, relVel):
        self.ptp.movePTPHomeJointSpace(relVel)

    def movePTPTransportPositionJointSpace(self, relVel):
        self.ptp.movePTPTransportPositionJointSpace(relVel)

    """
    Cartesian linear  motion
    """

    def movePTPLineEEF(self, pos, vel):
        self.ptp.movePTPLineEEF(pos, vel)

    def movePTPLineEefRelBase(self, pos, vel):
        self.ptp.movePTPLineEefRelBase(pos, vel)

    def movePTPLineEefRelEef(self, pos, vel):
        self.ptp.movePTPLineEefRelEef(pos, vel)

    """
    Circular motion
    """

    def movePTPCirc1OrintationInter(self, f1, f2, vel):
        self.ptp.movePTPCirc1OrintationInter(f1, f2, vel)

    def movePTPArcYZ_AC(self, theta, c, vel):
        self.ptp.movePTPArcYZ_AC(theta, c, vel)

    def movePTPArcXZ_AC(self, theta, c, vel):
        self.ptp.movePTPArcXZ_AC(theta, c, vel)

    def movePTPArcXY_AC(self, theta, c, vel):
        self.ptp.movePTPArcXY_AC(theta, c, vel)

    def movePTPArc_AC(self, theta, c, k, vel):
        self.ptp.movePTPArc_AC(theta, c, k, vel)

    # realtime motion control
    def realTime_stopImpedanceJoints(self):
        self.rtl.realTime_stopImpedanceJoints()

    def realTime_startDirectServoCartesian(self):
        self.rtl.realTime_startDirectServoCartesian()

    def realTime_stopDirectServoCartesian(self):
        self.rtl.realTime_stopDirectServoCartesian()

    def realTime_stopDirectServoJoints(self):
        self.rtl.realTime_stopDirectServoJoints()

    def realTime_startDirectServoJoints(self):
        self.rtl.realTime_startDirectServoJoints()

    def realTime_startImpedanceJoints(self, weightOfTool, cOMx, cOMy, cOMz, cStiness, rStifness, nStifness):
        self.rtl.realTime_startImpedanceJoints(weightOfTool, cOMx, cOMy, cOMz, cStiness, rStifness, nStifness)

    # Joint space servo command
    def sendEEfPosition(self, x):
        self.sender.sendEEfPosition(x)

    def sendJointsPositionsGetMTorque(self, x):
        return self.sender.sendJointsPositionsGetMTorque(x)

    def sendJointsPositionsGetExTorque(self, x):
        return self.sender.sendJointsPositionsGetExTorque(x)

    def sendJointsPositionsGetActualEEFpos(self, x):
        return self.sender.sendJointsPositionsGetActualEEFpos(x)

    def sendJointsPositionsGetEEF_Force_rel_EEF(self, x):
        return self.sender.sendJointsPositionsGetEEF_Force_rel_EEF(x)

    def sendJointsPositionsGetActualJpos(self, x):
        return self.sender.sendJointsPositionsGetActualJpos(x)

    # Crtesian space servo command
    def sendEEfPosition(self, x):
        self.sender.sendEEfPosition(x)

    def sendEEfPositionGetExTorque(self, x):
        return self.sender.sendEEfPositionExTorque(x)

    def sendEEfPositionGetActualEEFpos(self, x):
        return self.sender.sendEEfPositionGetActualEEFpos(x)

    def sendEEfPositionGetActualJpos(self, x):
        return self.sender.sendEEfPositionGetActualJpos(x)

    def sendEEfPositionGetEEF_Force_rel_EEF(self, x):
        return self.sender.sendEEfPositionGetEEF_Force_rel_EEF(x)

    def sendEEfPositionGetMTorque(self, x):
        return self.sender.sendEEfPositionMTorque(x)

    def sendJointsPositions(self, x):
        return self.sender.sendJointsPositions(x)

    """
    Precise hand guiding
    """

    def preciseHandGuiding(self, weight_tool, centre_mass):
        return self.sender.preciseHandGuiding(weight_tool, centre_mass)

    # getters
    def getEEFPos(self):
        return self.get.getEEFPos()

    def getEEF_Force(self):
        return self.get.getEEF_Force()

    def getEEFCartizianPosition(self):
        return self.get.getEEFCartizianPosition()

    def getEEF_Moment(self):
        return self.get.getEEF_Moment()

    def getJointsPos(self):
        return self.get.getJointsPos()

    def getJointsExternalTorques(self):
        return self.get.getJointsExternalTorques()

    def getJointsMeasuredTorques(self):
        return self.get.getJointsMeasuredTorques()

    def getMeasuredTorqueAtJoint(self, x):
        return self.get.getMeasuredTorqueAtJoint(x)

    def getEEFCartizianOrientation(self):
        return self.get.getEEFCartizianOrientation()

    # get pin states
    def getPin3State(self):
        return self.get.getPin3State()

    def getPin10State(self):
        return self.get.getPin10State()

    def getPin13State(self):
        return self.get.getPin13State()

    def getPin16State(self):
        return self.get.getPin16State()

    # setters
    def setBlueOff(self):
        self.set.setBlueOff()

    def setBlueOn(self):
        self.set.setBlueOn()

    def setPin1Off(self):
        self.set.setPin1Off()

    def setPin1On(self):
        self.set.setPin1On()

    def setPin2Off(self):
        self.set.setPin2Off()

    def setPin2On(self):
        self.set.setPin2On()

    def setPin11Off(self):
        self.set.setPin11Off()

    def setPin11On(self):
        self.set.setPin11On()

    def setPin12Off(self):
        self.set.setPin12Off()

    def setPin12On(self):
        self.set.setPin12On()
