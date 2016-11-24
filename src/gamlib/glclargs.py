# -*- coding: utf-8 -*-

# Copyright (C) 2016 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""GAM command line argument processing

"""

class GamCLArgs(object):

  def __init__(self):
    self.argv = []
    self.argvI = 0
    self.argvLen = 0

# Initialize arguments
  def InitializeArguments(self, args):
    self.argv = args[:]
    self.argvI = 1
    self.argvLen = len(self.argv)

# Any arguments remaining
  def ArgumentsRemaining(self):
    return self.argvI < self.argvLen

# Multiple arguments remaining
  def MultipleArgumentsRemaining(self):
    return not self.argvI+1 == self.argvLen

# All arguments
  def AllArguments(self):
    return self.argv

# Specific argument
  def Argument(self, index):
    return self.argv[index]

# Current argument
  def Current(self):
    return self.argv[self.argvI]

# Previous argument
  def Previous(self):
    return self.argv[self.argvI-1]

# Remaining arguments
  def Remaining(self):
    return self.argv[self.argvI:]

# Argument location
  def Location(self):
    return self.argvI

# Advance to next argument
  def Advance(self):
    self.argvI += 1

# Backup to previous argument
  def Backup(self):
    self.argvI -= 1

# Save argument location
  def SaveLocation(self):
    self.argvIsave = self.argvI

# Reset argument location
  def ResetLocation(self, offset):
    self.argvI = self.argvIsave+offset
