#!/usr/bin/env python3

import os
import math
import numpy as np
from panda3d.core import *
from transforms3d.quaternions import mat2quat

import rospy
import rospkg
import tf2_ros
from std_srvs.srv import Empty, EmptyResponse
from geometry_msgs.msg import Pose, TransformStamped
from visualization_msgs.msg import Marker, MarkerArray

import modeling.geometric_model as gm
import modeling.collision_model as cm
import visualization.panda.world as wd
import grasping.planning.antipodal as gpa

import pyhiro.freesuc as fs
import pyhiro.pandactrl as pc
import pyhiro.pandageom as pg


class GraspPlanner():

    def __init__(self):
        gripper_name = rospy.get_param("~gripper_name")

        if gripper_name in ['robotiqhe', 'robotiq85', 'robotiq140']:
            self.base = wd.World(cam_pos=[1, 1, 1], lookat_pos=[0, 0, 0])
        elif gripper_name in ['suction', 'sgb30']:
            self.base = pc.World(camp=[500, 500, 500], lookatp=[0, 0, 0])
        else:
            rospy.logerr("The specified gripper is not implemented.")
        self.base.taskMgr.step()


        if gripper_name == "robotiqhe":
            import robot_sim.end_effectors.gripper.robotiqhe.robotiqhe as gr
            self.gripper = gr.RobotiqHE()
            self.body_stl_path = self.gripper.lft.lnks[0]['mesh_file']
            self.fingers_dict = {
                'gripper.lft.lnks.1': self.gripper.lft.lnks[1],
                'gripper.rgt.lnks.1': self.gripper.rgt.lnks[1]}
        elif gripper_name == "robotiq85":
            import robot_sim.end_effectors.gripper.robotiq85.robotiq85 as gr
            self.gripper = gr.Robotiq85()
            self.body_stl_path = self.gripper.lft_outer.lnks[0]['mesh_file']
            self.fingers_dict = {
                'gripper.lft_outer.lnks.1': self.gripper.lft_outer.lnks[1],
                'gripper.rgt_outer.lnks.1': self.gripper.rgt_outer.lnks[1],
                'gripper.lft_outer.lnks.2': self.gripper.lft_outer.lnks[2],
                'gripper.rgt_outer.lnks.2': self.gripper.rgt_outer.lnks[2],
                'gripper.lft_outer.lnks.3': self.gripper.lft_outer.lnks[3],
                'gripper.rgt_outer.lnks.3': self.gripper.rgt_outer.lnks[3],
                'gripper.lft_outer.lnks.4': self.gripper.lft_outer.lnks[4],
                'gripper.rgt_outer.lnks.4': self.gripper.rgt_outer.lnks[4],
                'gripper.lft_inner.lnks.1': self.gripper.lft_inner.lnks[1],
                'gripper.rgt_inner.lnks.1': self.gripper.rgt_inner.lnks[1]}
        elif gripper_name == "robotiq140":
            import robot_sim.end_effectors.gripper.robotiq140.robotiq140 as gr
            self.gripper = gr.Robotiq140()
            self.body_stl_path = self.gripper.lft_outer.lnks[0]['mesh_file']
            self.fingers_dict = {
                'gripper.lft_outer.lnks.1': self.gripper.lft_outer.lnks[1],
                'gripper.rgt_outer.lnks.1': self.gripper.rgt_outer.lnks[1],
                'gripper.lft_outer.lnks.2': self.gripper.lft_outer.lnks[2],
                'gripper.rgt_outer.lnks.2': self.gripper.rgt_outer.lnks[2],
                'gripper.lft_outer.lnks.3': self.gripper.lft_outer.lnks[3],
                'gripper.rgt_outer.lnks.3': self.gripper.rgt_outer.lnks[3],
                'gripper.lft_outer.lnks.4': self.gripper.lft_outer.lnks[4],
                'gripper.rgt_outer.lnks.4': self.gripper.rgt_outer.lnks[4],
                'gripper.lft_inner.lnks.1': self.gripper.lft_inner.lnks[1],
                'gripper.rgt_inner.lnks.1': self.gripper.rgt_inner.lnks[1]}
        elif gripper_name == "suction":
            import robot_sim.end_effectors.single_contact.suction.sandmmbs.sdmbs as gr  # noqa
            self.gripper = gr
            self.body_stl_path = str(self.gripper.Sdmbs().mbs_stlpath)
        elif gripper_name == "sgb30":
            import robot_sim.end_effectors.single_contact.suction.sgb30.sgb30 as gr  # noqa
            self.gripper = gr
            self.body_stl_path = str(self.gripper.SGB30().sgb_stlpath)
        else:
            rospy.logerr("The specified gripper is not implemented.")
        gm.gen_frame().attach_to(self.base)
        self.base.taskMgr.step()

        self.object_stl_path = rospy.get_param("~object_mesh_path")
        self.grasp_target = cm.CollisionModel(self.object_stl_path)
        self.grasp_target.set_rgba([.9, .75, .35, .3])
        self.grasp_target.attach_to(self.base)
        self.base.taskMgr.step()
        self.markers = MarkerArray()
        pose = Pose()
        pose.position.x = 0.
        pose.position.y = 0.
        pose.position.z = 0.
        pose.orientation.x = 0.
        pose.orientation.y = 0.
        pose.orientation.z = 0.
        pose.orientation.w = 1.
        scale = [1., 1., 1.]
        if gripper_name in ['robotiqhe', 'robotiq85', 'robotiq140']:
            pass
        elif gripper_name in ['suction', 'sgb30']:
            scale = [0.001, 0.001, 0.001]
        else:
            rospy.logerr("The specified gripper is not implemented.")
        self.markers.markers.append(
            self.gen_marker(
                'base_link',
                'object',
                0,
                pose,
                self.object_stl_path,
                scale=scale,
                color=[1.0, 0.5, 0.5, 0.5]))

        self.pose_dict = {}
        self.br = tf2_ros.StaticTransformBroadcaster()
        if gripper_name in ['robotiqhe', 'robotiq85', 'robotiq140']:
            self.planning_service = rospy.Service(
                'plan_grasp', Empty, self.plan_grasps)
        elif gripper_name in ['suction', 'sgb30']:
            self.planning_service = rospy.Service(
                'plan_grasp', Empty, self.plan_contacts)
        else:
            rospy.logerr("The specified gripper is not implemented.")
        self.marker_pub = rospy.Publisher(
            'grasp_pub', MarkerArray, queue_size=1)

    def update_tfs(self):
        """ Sends tfs.

            Attributes:
                pose_dict: dict{name(str): pose(geometry_msgs/Pose)}
        """

        if self.pose_dict is not {}:
            for name, data in self.pose_dict.items():
                t = TransformStamped()
                t.header.stamp = rospy.Time.now()
                t.header.frame_id = data['parent']
                t.child_frame_id = name
                t.transform.translation.x = data['pose'].position.x
                t.transform.translation.y = data['pose'].position.y
                t.transform.translation.z = data['pose'].position.z
                t.transform.rotation.x = data['pose'].orientation.x
                t.transform.rotation.y = data['pose'].orientation.y
                t.transform.rotation.z = data['pose'].orientation.z
                t.transform.rotation.w = data['pose'].orientation.w
                self.br.sendTransform(t)

    def gen_marker(
            self,
            frame_name,
            name,
            id_int,
            pose,
            stl_path,
            scale=[1., 1., 1.],
            color=[0., 0., 0., 0.]):
        """ Generates a marker.

            Attributes:
                frame_name (str): Frame name
                name (str): Unique marker name
                id_int (int): Unique id number
                pose (geometry_msgs/Pose): Pose of the marker
                stl_path (str): Stl file path
        """

        marker = Marker()
        marker.header.frame_id = frame_name
        marker.header.stamp = rospy.Time()
        marker.ns = name
        marker.id = id_int
        marker.type = marker.MESH_RESOURCE
        marker.action = marker.ADD
        marker.pose = pose
        marker.scale.x = float(scale[0])
        marker.scale.y = float(scale[1])
        marker.scale.z = float(scale[2])
        marker.color.a = float(color[0])
        marker.color.r = float(color[1])
        marker.color.g = float(color[2])
        marker.color.b = float(color[3])
        marker.mesh_resource = 'file://' + stl_path
        marker.mesh_use_embedded_materials = True

        return marker

    def plan_contacts(self, req):
        """ Plans contacts. """

        contact_planner = fs.Freesuc(
            self.object_stl_path,
            handpkg=self.gripper,
            torqueresist=100)
        contact_planner.removeBadSamples(mindist=0.1)
        contact_planner.clusterFacetSamplesRNN(reduceRadius=100)
        pg.plotAxisSelf(self.base.render, Vec3(0, 0, 0))
        contact_planner.removeHndcc(self.base)
        objnp = pg.packpandanp(
            contact_planner.objtrimesh.vertices,
            contact_planner.objtrimesh.face_normals,
            contact_planner.objtrimesh.faces,
            name='')
        objnp.setColor(.37, .37, .35, 1)
        objnp.reparentTo(self.base.render)

        rospy.loginfo(
            "Number of generated grasps: %s",
            len(contact_planner.sucrotmats))
        contact_result = []
        parent_frame = 'object'
        for i, hndrot in enumerate(contact_planner.sucrotmats):
            if i >= 1:
                tmphand = self.gripper.newHandNM(hndcolor=[.7, .7, .7, .7])
                centeredrot = Mat4(hndrot)
                tmphand.setMat(centeredrot)
                tmphand.reparentTo(self.base.render)
                tmphand.setColor(.5, .5, .5, .3)
                contact_pos = [tmphand.getPos()[i] / 1000 for i in range(3)]
                mat = tmphand.getMat()
                contact_mat = \
                    [list([mat[i][0], mat[i][1], mat[i][2]]) for i in range(3)]

                pose_b = Pose()
                pose_b.position.x = contact_pos[0]
                pose_b.position.y = contact_pos[1]
                pose_b.position.z = contact_pos[2]
                q = mat2quat(np.array(contact_mat).T)
                pose_b.orientation.x = q[1]
                pose_b.orientation.y = q[2]
                pose_b.orientation.z = q[3]
                pose_b.orientation.w = q[0]
                self.markers.markers.append(
                    self.gen_marker(
                        parent_frame,
                        'body_'+str(i),
                        0,
                        pose_b,
                        self.body_stl_path,
                        scale=[0.001, 0.001, 0.001],
                        color=[0.2, 0.8, 0.8, 0.8]))
                self.pose_dict['body_'+str(i)] = \
                    {'parent': parent_frame, 'pose': pose_b}
                self.update_tfs()

        return EmptyResponse()

    def plan_grasps(self, req):
        """ Plans grasps. """

        grasp_info_list = gpa.plan_grasps(
            self.gripper,
            self.grasp_target,
            angle_between_contact_normals=math.radians(90),
            openning_direction='loc_x',
            max_samples=4,
            min_dist_between_sampled_contact_points=.016,
            contact_offset=.016)
        rospy.loginfo("Number of generated grasps: %s", len(grasp_info_list))

        for i, grasp_info in enumerate(grasp_info_list):
            jaw_width, jaw_pos, jaw_rotmat, hnd_pos, hnd_rotmat = grasp_info
            self.gripper.grip_at_with_jcpose(jaw_pos, jaw_rotmat, jaw_width)
            self.gripper.gen_meshmodel().attach_to(self.base)

            parent_frame = 'object'
            pose_b = Pose()
            pose_b.position.x = hnd_pos[0]
            pose_b.position.y = hnd_pos[1]
            pose_b.position.z = hnd_pos[2]
            q = mat2quat(hnd_rotmat)
            pose_b.orientation.x = q[1]
            pose_b.orientation.y = q[2]
            pose_b.orientation.z = q[3]
            pose_b.orientation.w = q[0]
            self.markers.markers.append(
                self.gen_marker(
                    parent_frame,
                    'body_'+str(i),
                    0,
                    pose_b,
                    self.body_stl_path))
            self.pose_dict['body_'+str(i)] = \
                {'parent': parent_frame, 'pose': pose_b}
            self.update_tfs()

            for k, v in self.fingers_dict.items():
                pose = Pose()
                pose.position.x = v['gl_pos'][0]
                pose.position.y = v['gl_pos'][1]
                pose.position.z = v['gl_pos'][2]
                q = mat2quat(v['gl_rotmat'])
                pose.orientation.x = q[1]
                pose.orientation.y = q[2]
                pose.orientation.z = q[3]
                pose.orientation.w = q[0]
                scale = [1., 1., 1.]
                if v['scale'] is not None:
                    scale = v['scale']
                self.markers.markers.append(
                    self.gen_marker(
                        parent_frame,
                        k+'_'+str(i),
                        0,
                        pose,
                        v['mesh_file'],
                        scale))
                self.pose_dict[k+'_'+str(i)] = \
                    {'parent': parent_frame, 'pose': pose}

        return EmptyResponse()


if __name__ == '__main__':
    rospy.init_node('grasp_planning_server')
    planner = GraspPlanner()
    rate = rospy.Rate(1)
    while not rospy.is_shutdown():
        planner.marker_pub.publish(planner.markers)
        planner.base.taskMgr.step()
        planner.update_tfs()
        rate.sleep()
