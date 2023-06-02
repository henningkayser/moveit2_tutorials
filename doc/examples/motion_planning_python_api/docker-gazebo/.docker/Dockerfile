FROM osrf/ros:humble-desktop-jammy

SHELL ["/bin/bash", "-c", "-o", "pipefail"]

RUN echo "deb [trusted=yes] https://raw.githubusercontent.com/moveit/moveit2_packages/jammy-humble/ ./" \
    | sudo tee /etc/apt/sources.list.d/moveit_moveit2_packages.list
RUN echo "yaml https://raw.githubusercontent.com/moveit/moveit2_packages/jammy-humble/local.yaml humble" \
    | sudo tee /etc/ros/rosdep/sources.list.d/1-moveit_moveit2_packages.list

# Bring the container up to date
RUN apt-get update && apt-get upgrade -y && rosdep update

# Install packages required to run the demo
RUN apt-get update && apt-get install -y --no-install-recommends \
    # ros-humble-moveit \
    wget \
    python3-pip

# Create Colcon workspace and clone the needed source code to run the demo
RUN mkdir -p /root/moveit_ws/src
WORKDIR /root/moveit_ws/src
RUN git clone -b panda_gz --depth 1 --single-branch https://github.com/henningkayser/moveit_resources.git
RUN git clone -b panda_gz --depth 1 --single-branch https://github.com/henningkayser/moveit2_tutorials.git
#TODO(henningkayser) remove when #2222 and #2223 are merged
RUN git clone -b panda_gz --depth 1 --single-branch https://github.com/henningkayser/moveit2.git
# COPY ./ moveit2_tutorials
WORKDIR /root/moveit_ws
# hadolint ignore=SC1091
RUN source /opt/ros/humble/setup.bash \
    && apt-get update -y \
    && rosdep install --from-paths src --ignore-src --rosdistro "$ROS_DISTRO" -y \
    && rm -rf /var/lib/apt/lists/*

# Build the Colcon workspace for the user
RUN source /opt/ros/humble/setup.bash && colcon build --symlink-install

# Set up the entrypoint for both container start and interactive terminals.
COPY ./.docker/ros_entrypoint.sh /opt/.ros/
RUN echo "source /opt/.ros/ros_entrypoint.sh" >> ~/.bashrc
ENTRYPOINT [ "/opt/.ros/ros_entrypoint.sh" ]
