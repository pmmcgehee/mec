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
from pcdsdaq.ext_scripts import *

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

        self.nskip = 0 
        self.npredark = 0 
        self.nprex = 0 
        self.nduring = 0 
        self.npostdark = 0 

        self.set_beampos(pp=10, daqshot=12, varex=12)

# Summary counts
        self.daq_frames = 0
        self.total_frames = 0

#
# Convenience function to define frame sequences using
# delta beams only.
#
    def set_beampos(self, pp=10, daqshot=12, varex=12):
# Initialize sequence parameters
        self.skip_frame = [['varexreadout',varex,0]]
        self.dark_frame = [['daqreadout',daqshot,0],
                           ['varexreadout',varex,0]]
        self.xray_frame = [['pulsepicker',pp,0],
                           ['daqreadout',daqshot,0],
                           ['varexreadout',varex,0]]
        self.shot_frame = [['pulsepicker',pp,0],
                           ['longpulse',daqshot,0],
                           ['daqreadout',daqshot,0],
                           ['varexreadout',varex,0]]
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

# This returns the number of the last run since we haven't run the plan yet.
        run_no = get_run_number(hutch='mec', timeout=10) + 1

        varex_payload = {
                'command': 'arm',
                'run_name' : str(run_no),
                'num_skip_frames' : self.nskip+1,
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
        if resp_str != 'OK':
            print('Process on psmeclogin reported a problem: {}.'.format(resp_str))
            return False

        return True

#
# Define a sequence with delta beams
#
    def gendeltas(self, seq):
        d1 = sorted(seq, key=lambda tup: tup[1]*3 + tup[2])
        last_event_fiducial = 0
        delseq = []
        
        for sd in d1: 
            if not sd[0] in self.EC:
                raise ValueError("Invalid event code name: {}".format(sd[0]))
            if (sd[1] < 0) or (sd[2] < 0):
                raise ValueError("Requested beam or fiducial position < 0")

            dfid = sd[1]*3 + sd[2]
            d2 = dfid - last_event_fiducial
            delseq.append([self.EC[sd[0]], d2//3, d2%3])
            last_event_fiducial = dfid

        return delseq

#
# Create an event code sequence - 
# This is called by the Laser._single_shot_plan() if any Varex data 
# is requested in the Laser constructor, i.e. if
# VarexPreDark + VarexPreX + VarexDuring + VarexPostDark > 0
#
    def seq(self, nskip=0, npredark=0, nprex=0, nduring=0, npostdark=0):

# Store for future use
        self.nskip = nskip
        self.npredark = npredark
        self.nprex = nprex
        self.nduring = nduring
        self.npostdark = npostdark

        try:
            self.events = [[self.EC['varexreadout'],0,0]] + \
                nskip * self.gendeltas(self.skip_frame) + \
                npredark * self.gendeltas(self.dark_frame) + \
                nprex * self.gendeltas(self.xray_frame) + \
                nduring * self.gendeltas(self.shot_frame) + \
                npostdark * self.gendeltas(self.dark_frame)

            self.daq_frames = npredark + nprex + nduring + npostdark
            self.total_frames = self.daq_frames + nskip
        except Exception as e:
            print(e)
            print("Sequence creation failed, returning null events")
            self.events = []
        
        return self.events

#
# Output the event count, delta beam, and total delta beam
#
    def report_seq(self):
        total_fid = 0
        iframe = 0 

        for ev in self.events:
            total_fid = total_fid + ev[1]*3 + ev[2]
            print("EC={0:3d} BD={1:4d} FD={2:3d} POSITION={3:4d}+{4:1d}".format(ev[0], ev[1], ev[2], total_fid//3, total_fid%3)) 
            if (ev[0] == 177):
                print("Finished frame {0:3d}\n".format(iframe))
                iframe = iframe + 1
