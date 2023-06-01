#!/bin/bash

# Source ROS 2 Humble
source /opt/ros/humble/setup.bash
echo "Sourced ROS 2 Humble"

# Source the base workspace, if built
if [ -f /root/moveit_ws/install/setup.bash ]
then
  source /root/moveit_ws/install/setup.bash
  echo "Sourced MoveIt workspace"
else
  echo "Please build the MoveIt workspace with:"
  echo "colcon build --symlink-install"
fi

# Execute the command passed into this entrypoint
exec "$@"
