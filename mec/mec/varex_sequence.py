#!/usr/bin/env python
#
# Module for setting up the MEC VAREX events
#
# This defines the class VarexSequence.
#
# Each VAREX sequence consists of the four subsequences of
# user defined length. 
#
# 1) skip     - no XFEL or optical laser, no DAQ readout
# 2) predark  - no XFEL or optical laser
# 3) prex     - XFEL only
#               The pulse picker is triggered 2 beams (16.67 ms) before
#               the XFEL beam
# 4) during   - XFEL and optical laser
#               The pulse picker is triggered 2 beams (16.67 ms) before
#               the XFEL and laser shot.
# 5) postdark - no XFEL or optical laser 
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

# seq = vx.seq(nskip, npredark, nprex, nduring, npostdark)
# This returns a list of 
#     (event count, delta beam, delta fiducial, burst count)
# entries for the VAREX sequence and can be passed to the 
# EventSequencer.put_seq() method.
#
# vx.report_seq()
# Output the event count, delta beam, and total delta beam
#

from mec.sequence import Sequence
import socket
import json
import pydaq

class VarexSequence(Sequence):

    def __init__(self):
        super().__init__()
        self.EC['varexreadout'] = 177

        print("These are the defined event codes:\n")
        for key, value in self.EC.items():
            print("{0:20s} {1:3d}".format(key, value))

        self.events = []

# Socket for communications with psmeclogin - defined in arm()
        self.clientsocket = None

# DAQ access
        self.daq = pydaq.Control('mec-daq', 0)

#
# Issue ARM command to VAREX PC via socket to psmeclogin
#
    def arm(self):
        if not self.clientsocket:
            try:
                self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.clientsocket.connect(('134.79.116.26', 8089))
                self.clientsocket.settimeout(10.0)
            except:
                print("Creation of socket connection to psmeclogin:8089 failed, aborting arm")
                self.clientsocket = None
                return False

        varex_payload = {
                'command': 'arm',
                'run_name' : str(self.daq.runnumber() + 1),
                'num_skip_frames' : self.nskip,
                'num_background_frames' : self.npredark,
                'num_data_frames' :  self.nprex + self.nduring,
                'includes_shot_frame' : (self.nduring > 0),
                'num_post_background_frames' : self.npostdark
                }
        vp = json.dumps(varex_payload).encode('utf-8')

        try:
            self.clientsocket.send(vp)
            resp = self.clientsocket.recv(64)
        except:
            print('Communication with psmeclogin failed')
            return False

        resp_str = resp.decode()
        if resp_str == 'NOT OK':
            print('Process on psmeclogin reported problems')
            return False

        return True

#
#
# Skip - no XFEL or optical data and no DAQ readout
#
    def skip(self, nframes):
        for i in range(nframes):
# Trigger 66.67 ms VAREX readout if first event
            if (not self.events):
                self.events.append([self.EC['varexreadout'], 0, 0, 0])
                
# VAREX readout at end of 10 Hz cycle
            self.events.append([self.EC['varexreadout'], 12, 0, 0])
#
#
# Dark - no XFEL or optical data
#
    def dark(self, nframes):
        for i in range(nframes):
# Trigger 66.67 ms VAREX readout if first event
            if (not self.events):
                self.events.append([self.EC['varexreadout'], 0, 0, 0])
                
# Perform DAQ readout at shot time (even when dark)
# and VAREX readout at end of 10 Hz cycle
            self.events.append([self.EC['daqreadout'], 10, 0, 0])
            self.events.append([self.EC['varexreadout'], 2, 0, 0])

#
# XFEL only data
#
    def xray_only(self, nframes):
        for i in range(nframes):
# Trigger 66.67 ms VAREX readout if first event
            if (not self.events):
                self.events.append([self.EC['varexreadout'], 0, 0, 0])
# Open pulse picker (takes 2 beam delays)
            self.events.append([self.EC['pulsepicker'], 8, 0, 0])
#
# XFEL beam happens in this window
            self.events.append([self.EC['daqreadout'], 2, 0, 0])
#
# Perform VAREX readout at end of 10 Hz cycle
            self.events.append([self.EC['varexreadout'], 2, 0, 0])

#
# XFEL and LPL data
# This assumes that the PFNs are already charged.
#
    def lpl_singleshot(self):
# Trigger 66.67 ms VAREX readout if first event
        if (not self.events):
            self.events.append([self.EC['varexreadout'], 0, 0, 0])
# Open pulse picker (takes 2 beam delays)
        self.events.append([self.EC['pulsepicker'], 8, 0, 0])
#
# XFEL beam and LPL shot happen here
#
        self.events.append([self.EC['longpulse'], 2, 0, 0])
        self.events.append([self.EC['daqreadout'], 0, 0, 0])

# Perform XFEL and DAQ readout at end of 10 Hz cycle
        self.events.append([self.EC['varexreadout'], 2, 0, 0])

#
# Create an event code sequence - 
# This is called by the Laser._single_shot_plan() if any Varex data 
# is requested in the Laser constructor, i.e. if
# VarexPreDark + VarexPreX + VarexDuring + VarexPostDark > 0
#
    def seq(self, nskip, npredark, nprex, nduring, npostdark):
        self.events = [] # Clear event list

# Store for future use
        self.nskip = nskip
        self.npredark = npredark
        self.nprex = nprex
        self.nduring = nduring
        self.npostdark =  npostdark

# Pre-shot skip frames
        if nskip > 0: self.skip(nskip)

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
        iframe = 0 

        for ev in self.events:
            total_bd = total_bd + ev[1]
            print("EC={0:3d} BD={1:4d} TOTAL BD={2:4d}".format(ev[0], ev[1],
                total_bd))
            if (ev[0] == 177):
                print("Finished frame {0:3d}\n".format(iframe))
                iframe = iframe + 1
