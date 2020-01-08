# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Rein Appeldoorn
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the names of the authors nor the names of their
#    affiliated organizations may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Defines the main method for the nmea_socket_driver executable."""


import socket
import sys

import rospy

from libnmea_navsat_driver.driver import RosNMEADriver


def main():
    """Create and run the nmea_socket_driver ROS node.

    Creates a ROS NMEA Driver and feeds it NMEA sentence strings from a UDP socket.

    ROS parameters:
        ~ip (str): IPV4 address of the socket to open.
        ~port (int): Local port of the socket to open.
        ~buffer_size (int): The size of the buffer for the socket, in bytes.
        ~timeout (float): The time out period for the socket, in seconds.
    """
    rospy.init_node('nmea_socket_driver')

    try:
        remote_ip = rospy.get_param('~ip', '0.0.0.0')
        remote_port = rospy.get_param('~port', 10110)
        buffer_size = rospy.get_param('~buffer_size', 4096)
        timeout = rospy.get_param('~timeout_sec', 2)
    except KeyError as e:
        rospy.logerr("Parameter %s not found" % e)
        sys.exit(1)

    frame_id = RosNMEADriver.get_frame_id()

    driver = RosNMEADriver()
	
	# Look for the response
    amount_received = 0
    amount_expected = len(buffer_size)

    # Connection-loop: connect and keep receiving. If receiving fails,
    # reconnect
    while not rospy.is_shutdown():
        try:
            # Create a socket
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Bind the socket to the port
            socket_.connect((remote_ip, remote_port))

            # Set timeout
            socket_.settimeout(timeout)
        except socket.error as exc:
            rospy.logerr(
                "Caught exception socket.error when setting up socket: %s" %
                exc)
            sys.exit(1)

        # recv-loop: When we're connected, keep receiving stuff until that
        # fails
        while not rospy.is_shutdown():
            try:
                chunks = []
				data = ""
				while amount_received < amount_expected:
					chunk  = socket_.recv(buffer_size)
					chunks.append(chunk)
					amount_received += len(chunk)
					nmea_message = join(chunks)
					if (nmea_message.find('\n') != -1)
						data = nmea_message
						chunks = []
						break;
					
                # strip the data
                data_list = data.strip().split("\n")

                for data in data_list:

                    try:
                        driver.add_sentence(data, frame_id)
                    except ValueError as e:
                        rospy.logwarn(
                            "Value error, likely due to missing fields in the NMEA message. "
                            "Error was: %s. Please report this issue at "
                            "github.com/ros-drivers/nmea_navsat_driver, including a bag file with the NMEA "
                            "sentences that caused it." %
                            e)

            except socket.error as exc:
                rospy.logerr(
                    "Caught exception socket.error during recvfrom: %s" % exc)
                socket_.close()
                # This will break out of the recv-loop so we start another
                # iteration of the connection-loop
                break

        socket_.close()  # Close socket
