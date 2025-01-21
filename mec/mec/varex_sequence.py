#!/usr/bin/env python
#
# Module for setting up the MEC VAREX events
#
# This defines the class VarexSequence.
#
# Each VAREX sequence consists of the four subsequences of
# user defined length. 
#
# 1) predark  - no XFEL or optical laser
# 2) prex     - XFEL only
#               The pulse picker is triggered 2 beams (16.67 ms) before
#               the XFEL beam
# 3) during   - XFEL and optical laser
#               The pulse picker is triggered 2 beams (16.67 ms) before
#               the XFEL and laser shot.
# 4) postdark - no XFEL or optical laser 
#
# Each subsequence takes 12 beams (10 Hz rep rate) and begin with the
# VAREX being triggered using EC 177. Upon receipt of the trigger
# the device begins a 66.67 ms (8 beams) readout. During the remaining
# 33.33 ms (4 beams) window the VAREX is acquiring signal.
#
# Usage:
#
# from mec.varex_sequence import VarexSequence
# vx = VarexSequence()

# seq = vx.seq(npredark, nprex, nduring, npostdark)
# This returns a list of 
#     (event count, delta beam, delta fiducial, burst count)
# entries for the VAREX sequence and can be passed to the 
# EventSequencer.put_seq() method.
#
# vx.report_seq()
# Output the event count, delta beam, and total delta beam
#

from mec.sequence import Sequence

class VarexSequence(Sequence):

    def __init__(self):
        super().__init__()
        self.EC['varexreadout'] = 177

        print("These are the defined event codes:\n")
        for key, value in self.EC.items():
            print("{0:20s} {1:3d}".format(key, value))

        self.events = []

    def dark(self, nframes):
        for i in range(nframes):
# Trigger 66.67 ms VAREX readout
            self.events.append([self.EC['varexreadout'], 0, 0, 0])
# Perform DAQ readout at end of 10 Hz cycle
            self.events.append([self.EC['daqreadout'], 12, 0, 0])

    def xray_only(self, nframes):
        for i in range(nframes):
# Trigger 66.67 ms VAREX readout
            self.events.append([self.EC['varexreadout'], 0, 0, 0])
# Open pulse picker (takes 2 beam delays)
            self.events.append([self.EC['pulsepicker'], 8, 0, 0])
#
# XFEL beam happens in this window
#
# Perform DAQ readout at end of 10 Hz cycle
            self.events.append([self.EC['daqreadout'], 4, 0, 0])

# This assumes that the PFNs are already charged.
    def lpl_singleshot(self):
# Trigger 66.67 ms VAREX readout
        self.events.append([self.EC['varexreadout'], 0, 0, 0])
# Open pulse picker (takes 2 beam delays)
        self.events.append([self.EC['pulsepicker'], 8, 0, 0])
#
# XFEL beam and LPL shot happen here
#
        self.events.append([self.EC['longpulse'], 2, 0, 0])
# Perform DAQ readout at end of 10 Hz cycle
        self.events.append([self.EC['daqreadout'], 2, 0, 0])

#
# This list is returned by the VarexSequence constructor.
#
    def seq(self, npredark, nprex, nduring, npostdark):
        self.events = [] # Clear event list

# Pre-shot background frames
        if npredark > 0: self.dark(npredark)

# Pre-shot ambient frames
        if nprex > 0: self.xray_only(nprex)

# Do the shot!
        if nduring == 1: self.lpl_singleshot()

# Post-shot background frames
        if npostdark > 0: self.dark(npostdark)

        return self.events

#
# Output the event count, delta beam, and total delta beam
#
    def report_seq(self):
        total_bd = 0
        for ev in self.events:
            total_bd = total_bd + ev[1]
            print("EC={0:3d} BD={1:4d} TOTAL BD={2:4d}".format(ev[0], ev[1],
                total_bd))
