# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# random code that helps with debugging/testing the python interfaces and examples
# this is not meant to be run by normal users
from __future__ import with_statement # for python 2.5
__copyright__ = 'Copyright (C) 2009-2010'
__license__ = 'Apache License, Version 2.0'

from openravepy import *
from numpy import *

def RetractionConstraint(self,prev,cur,thresh=1e-4):
    """jacobian gradient descent"""
    new = array(cur)
    robot.SetActiveDOFValues(prev)
    distprev = sum((prev-cur)**2)
    distcur = 0
    lasterror = 0
    for iter in range(10):
        Jrotation = robot.CalculateActiveAngularVelocityJacobian(manip.GetEndEffector().GetIndex())
        Jtranslation = robot.CalculateActiveJacobian(manip.GetEndEffector().GetIndex(),manip.GetEndEffectorTransform()[0:3,3])
        J = r_[Jrotation,Jtranslation]
        JJt = dot(J,transpose(J))+eye(6)*1e-8
        invJ = dot(transpose(J),linalg.inv(JJt))
        Terror = dot(dot(targetframematrix,linalg.inv(Tee)),manip.GetEndEffectorTransform())
        poseerror = poseFromMatrix(Terror)
        error = r_[Terror[0:3,3],[2.0*arctan2(poseerror[i],poseerror[0]) for i in range(1,4)]]
        error *= array([1,0,0,1,1,1])
        print 'error: ', sum(error**2)
        if sum(error**2) < thresh**2:
            return True
        if sum(error**2) > lasterror and distcur > distprev:
            return False;
        qdelta = dot(invJ,error)
        vnew -= qdelta
        robot.SetActiveDOFValues(vnew)
        distcur = sum((vnew-vcur)**2)
        print manip.GetEndEffectorTransform()

def test_jacobianconstraints():
    env = Environment()
    robot = env.ReadRobotXMLFile('robots/barrettwam.robot.xml')
    env.AddRobot(robot)
    manip = robot.GetActiveManipulator()
    taskmanip = TaskManipulation(robot)
    robot.SetActiveDOFs(manip.GetArmJoints())
    vorg = robot.GetActiveDOFValues()
    
    freedoms = [1,1,1,1,1,1]
    v = array(vorg)
    v[1] += 0.2
    configs = [v]
    targetframematrix = eye(4)
    env.SetDebugLevel(DebugLevel.Debug)

    robot.SetActiveDOFValues(vorg)
    Tee = manip.GetEndEffectorTransform()
    print manip.GetEndEffectorTransform()
    errorthresh = 1e-3
    iters,newconfigs = taskmanip.EvaluateConstraints(freedoms=freedoms,targetframematrix=targetframematrix,configs=configs,errorthresh=errorthresh)
    print 'iters: ',iters
    robot.SetActiveDOFValues(configs[0])
    print 'old: ', manip.GetEndEffectorTransform()
    robot.SetActiveDOFValues(newconfigs[0])
    print 'new: ', manip.GetEndEffectorTransform()

def test_jacobian():
    """tests if jacobians work"""
    env = Environment()
    robot = env.ReadRobotXMLFile('robots/barretthand.robot.xml')
    env.AddRobot(robot)
    fingertip_global = array([-0.15,0,0.2])
    # get a link name
    link = robot.GetLink('Finger2-2')
    fingertip_local = dot(linalg.inv(link.GetTransform()),r_[fingertip_global,1])[0:3]
    J = robot.CalculateJacobian(link.GetIndex(),fingertip)
    
    # move each joint a little
    curvalues = robot.GetJointValues()
    for iter in range(100):
        robot.SetJointValues(curvalues + (random.randint(0,2,len(curvalues))-0.5)*0.03)
        fingertip_realdir = dot(link.GetTransform(),r_[fingertip_local,1])[0:3] - fingertip_global
        deltavalues = robot.GetJointValues()-curvalues
        fingertip_estimatedir = dot(J,deltavalues)
        dreal = fingertip_realdir/sqrt(sum(fingertip_realdir**2))
        destimate = fingertip_estimatedir/sqrt(sum(fingertip_estimatedir**2))
        if dot(dreal,destimate) < 0.99:
            print deltavalues
            raise ValueError('bad jacobian: %f'%dot(dreal,destimate))

def test_hash():
    env = Environment()
    robot = env.ReadRobotXMLFile('robots/barrettsegway.robot.xml')
    env.AddRobot(robot)
    s = robot.serialize(SerializationOptions.Kinematics)
    hash = robot.GetKinematicsGeometryHash()
    print hash

def test_geometrychange():
    """changed geometry and tests if changed are updated"""
    env = Environment()
    env.Load('data/lab1.env.xml')
    robot = env.GetRobots()[0]
    link = robot.GetLinks()[-1]
    link