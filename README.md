# wros

[![support level: community](https://img.shields.io/badge/support%20level-community-lightgray.svg)](https://rosindustrial.org/news/2016/10/7/better-supporting-a-growing-ros-industrial-software-platform)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
![repo size](https://img.shields.io/github/repo-size/Osaka-University-Harada-Laboratory/onrobot)

- ROS Noetic node examples with robot motion planners implemented in [WRS](https://github.com/wanweiwei07/wrs).

# Features

- Docker environment for ROS Noetic packages
- ROS node examples with [grasp planners (Wan et al., IEEE TRO 2021)](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9170578)

# Dependency

- [Ubuntu 20.04 PC](https://ubuntu.com/certified/laptops?q=&limit=20&vendor=Dell&vendor=Lenovo&vendor=HP&release=20.04+LTS)
  - [ROS Noetic (Python3)](https://wiki.ros.org/noetic/Installation/Ubuntu)
  - docker 20.10.12
  - docker-compose 1.29.2
  - nvidia-docker2 2.8.0-1

# Installation
```bash
git clone git@github.com:Osaka-University-Harada-Laboratory/wros.git --recursive --depth 1
sudo apt install byobu -y
cd wros
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build --no-cache --parallel 
```

# Usage

1. Make and execute the docker environment
- Run the following command in one terminal
  ```bash
  docker compose up
  ```
- Run these commands in another terminal
  ```bash
  xhost +
  docker exec -it wros_noetic_container bash
  ```
2. Revise the planning parameters described in wros_tutorials/config/XXX.yaml 
3. Execute commands in the docker container  
    ```bash
    byobu
    roslaunch wros_tutorials plan_grasp.launch config:=XXX.yaml
    # create new window by clicking F2 key
    rosservice call /plan_grasp
    ```

## [Robotiq Hand-E](https://robotiq.com/products/hand-e-adaptive-robot-gripper)
Please refer to [wros_tutorials/config/planner_params_robotiqhe_example.yaml](catkin_ws/noetic/src/wros_tutorials/config/planner_params_robotiqhe_example.yaml).
```bash
roslaunch wros_tutorials plan_grasp.launch config:=planner_params_robotiqhe_example.yaml
```  
<img src=image/robotiqhe.gif width=720>  

## [Robotiq 2F-85](https://robotiq.com/products/2f85-140-adaptive-robot-gripper)
Please refer to [wros_tutorials/config/planner_params_robotiq85_example.yaml](catkin_ws/noetic/src/wros_tutorials/config/planner_params_robotiq85_example.yaml).
```bash
roslaunch wros_tutorials plan_grasp.launch config:=planner_params_robotiq85_example.yaml
```  
<img src=image/robotiq85.gif width=720>  

## [Robotiq 2F-140](https://robotiq.com/products/2f85-140-adaptive-robot-gripper)
Please refer to [wros_tutorials/config/planner_params_robotiq140_example.yaml](catkin_ws/noetic/src/wros_tutorials/config/planner_params_robotiq140_example.yaml).
```bash
roslaunch wros_tutorials plan_grasp.launch config:=planner_params_robotiq140_example.yaml
```  
<img src=image/robotiq140.gif width=720>  

## Suction gripper
Please refer to [wros_tutorials/config/planner_params_suction_example.yaml](catkin_ws/noetic/src/wros_tutorials/config/planner_params_suction_example.yaml).
```bash
roslaunch wros_tutorials plan_grasp.launch config:=planner_params_suction_example.yaml
```  
<img src=image/suction.gif width=720>  

## [CONVUM balloon hand SGB30](https://convum.co.jp/products/en/other-en/sgb/)
Please refer to [wros_tutorials/config/planner_params_sgb30_example.yaml](catkin_ws/noetic/src/wros_tutorials/config/planner_params_sgb30_example.yaml).
```bash
roslaunch wros_tutorials plan_grasp.launch config:=planner_params_sgb30_example.yaml
```  
<img src=image/sgb30.gif width=720>  

# Contributors


# Author

[Takuya Kiyokawa](https://takuya-ki.github.io/)  
[Weiwei Wan](https://wanweiwei07.github.io/)  
[Keisuke Koyama](https://kk-hs-sa.website/)  
[Kensuke Harada](https://www.roboticmanipulation.org/members2/kensuke-harada/)  
