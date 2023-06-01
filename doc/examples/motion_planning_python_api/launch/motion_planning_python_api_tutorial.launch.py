"""
A launch file for running the motion planning python api tutorial
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import (
    IfCondition,
    UnlessCondition,
    LaunchConfigurationNotEquals,
    LaunchConfigurationEquals,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    ros2_control_hardware_type = DeclareLaunchArgument(
        "ros2_control_hardware_type",
        default_value="mock_components",
        description="ROS2 control hardware interface type to use for the launch file",
        choices=["mock_components", "isaac", "sim_ignition"],
    )

    declare_initial_positions_file = DeclareLaunchArgument(
        "initial_positions_file",
        default_value="initial_positions.yaml",
        description="Initial joint positions to use for ros2_control fake components and simulation -- expected to be a yaml file inside the config directory",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="False",
        description="Use simulation (Gazebo) clock if True",
    )

    moveit_config = (
        MoveItConfigsBuilder(
            robot_name="panda", package_name="moveit_resources_panda_moveit_config"
        )
        .planning_scene_monitor(publish_robot_description=True)
        .robot_description(file_path="config/panda.urdf.xacro",
                           mappings={
                               "ros2_control_hardware_type": LaunchConfiguration(
                                   "ros2_control_hardware_type"
                               ),
                               "initial_positions_file": LaunchConfiguration("initial_positions_file"),
                           },)
        .trajectory_execution(file_path="config/gripper_moveit_controllers.yaml")
        .moveit_cpp(
            file_path=get_package_share_directory("moveit2_tutorials")
            + "/config/motion_planning_python_api_tutorial.yaml"
        )
        .to_moveit_configs()
    )

    example_file = DeclareLaunchArgument(
        "example_file",
        default_value="motion_planning_python_api_tutorial.py",
        description="Python API tutorial file name",
    )

    moveit_py_node = Node(
        name="moveit_py",
        package="moveit2_tutorials",
        executable=LaunchConfiguration("example_file"),
        output="both",
        arguments=[
            "--ros-args",
            "--log-level",
            "fatal",
        ],  # MoveIt is spamming the log because of unknown '*_mimic' joints
        parameters=[moveit_config.to_dict(),
                    {"use_sim_time": use_sim_time}],
    )

    rviz_config_file = os.path.join(
        get_package_share_directory("moveit2_tutorials"),
        "config",
        "motion_planning_python_api_tutorial.rviz",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": use_sim_time},
        ],
    )

    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "panda_link0"],
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="log",
        parameters=[moveit_config.robot_description, {"use_sim_time": use_sim_time}],
    )

    ros2_controllers_path = os.path.join(
        get_package_share_directory("moveit_resources_panda_moveit_config"),
        "config",
        "ros2_controllers.yaml",
    )
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[moveit_config.robot_description, ros2_controllers_path],
        output="log",
        condition=LaunchConfigurationNotEquals(
            "ros2_control_hardware_type", "sim_ignition"
        ),
    )

    ignition_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="log",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "panda",
            "-allow-renaming",
            "true",
        ],
        condition=LaunchConfigurationEquals(
            "ros2_control_hardware_type", "sim_ignition"
        ),
    )

    # Clock Bridge
    sim_clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock"],
        output="screen",
        condition=LaunchConfigurationEquals(
            "ros2_control_hardware_type", "sim_ignition"
        ),
    )

    load_controllers = []
    for controller in [
        "joint_state_broadcaster",
        "panda_arm_controller",
        "panda_hand_controller",
    ]:
        load_controllers += [
            ExecuteProcess(
                cmd=["ros2 control load_controller --set-state active {}".format(controller)],
                shell=True,
                output="log",
            )
        ]

    return LaunchDescription(
        [
            ros2_control_hardware_type,
            declare_use_sim_time_cmd,
            declare_initial_positions_file,
            sim_clock_bridge,
            # Launch gazebo environment
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        os.path.join(
                            get_package_share_directory("ros_gz_sim"),
                            "launch",
                            "gz_sim.launch.py",
                        )
                    ]
                ),
                launch_arguments=[("gz_args", [" -r -v 4 empty.sdf"])],
                condition=LaunchConfigurationEquals(
                    "ros2_control_hardware_type", "sim_ignition"
                ),
            ),
            ignition_spawn_entity,
            example_file,
            moveit_py_node,
            robot_state_publisher,
            ros2_control_node,
            rviz_node,
            static_tf,
        ]
        + load_controllers
    )
