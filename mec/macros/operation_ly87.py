import time
import numpy as np
# used to color the output text
from colorama import init, Fore, Back, Style
import matplotlib as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)

from datetime import datetime
import matplotlib.pyplot as plt
#from mec.laser import NanoSecondLaser
import logging
from functools import partial

#import elog
#import pickle
from mecps import *
from pcdsdevices.epics_motor import Motor

from mec.db import *
from mec.db import mec_pulsepicker as pp
from mec.beamline import *
from mec.devices import *
from mec.laser import *
from mec.laser_devices import *
from mec.spl_modes import *
from mec.sequence import *
from mec.slowcams import *
from mec.visar_bed import *

# using a function from Tyler's timing module for the VISAR streaks
#from mec.mec_timing import TimingChannel

from ophyd import EpicsSignal

# force color rest at the end of any print statement
init(autoreset = True)

# logging declaration copy/paste from the utils.py file in hutch-python. Will add new definition though
SUCCESS_LEVEL = 35
logging.addLevelName('SUCCESS', SUCCESS_LEVEL)
logger = logging.getLogger(__name__)
logger.success = partial(logger.log, SUCCESS_LEVEL)

talbot_x=Motor('MEC:PPL:MMN:21', name='talbot_x')

#thz_motor = Motor('MEC:USR:MMS:17', name='thz_motor')
#spl_motor = Motor('MEC:USR:MMS:17', name='spl_motor')
ref_y = Motor('MEC:XT1:MMS:01', name='ref_y')
tgx=Motor('MEC:USR:MMS:17', name='tgx')
hexx=EpicsSignal('MEC:HEX:01:Xpr')
hexy=EpicsSignal('MEC:HEX:01:Ypr')
hexz=EpicsSignal('MEC:HEX:01:Zpr')
s500mm=EpicsSignal('MEC:PPL:MMN:13')
tgy=EpicsSignal('MEC:PPL:MMN:07')
tgy_rbv=EpicsSignal('MEC:PPL:MMN:07.RBV')
tgz=EpicsSignal('MEC:PPL:MMN:08')
tgz_rbv=EpicsSignal('MEC:PPL:MMN:08.RBV')

# X493 attenuator motor definition
att_trans=Motor('MEC:USR:MMS:20', name='att_trans')
att_rot=EpicsSignal('MEC:PPL:MMN:20')

tg_imaging_x=Motor('MEC:PPL:MMN:16', name='tg_imaging_x')
tg_imaging_y=Motor('MEC:PPL:MMN:22', name='tg_imaging_y')
tg_imaging_z=Motor('MEC:TC1:MMS:22', name='tg_imaging_z')

delay_line=Motor('MEC:USR:MMS:25', name='delay_line')
be_lens_stack=EpicsSignal("MEC:XT2:XFLS.VAL")

# GMD PV values for the FEL pulse energy
gmd_241 = EpicsSignal('GDET:FEE1:242:ENRC')
gmd_242 = EpicsSignal('GDET:FEE1:242:ENRC')
gmd_361 = EpicsSignal('GDET:FEE1:242:ENRC')
gmd_362 = EpicsSignal('GDET:FEE1:242:ENRC')

# Be lens vertical readback value
be_y = EpicsSignal('MEC:XT2:MMS:15.RBV')
be_y_preset1 = EpicsSignal('MEC:XT2:XFLS:PACK1_SET')
be_y_preset2 = EpicsSignal('MEC:XT2:XFLS:PACK2_SET')
be_y_preset3 = EpicsSignal('MEC:XT2:XFLS:PACK3_SET')

# spl timing
spl_vitara = EpicsSignal('LAS:FS6:VIT:FS_TGT_TIME')
spl_vitara_pv = EpicsSignal('MEC:NOTE:LAS:FST0')

# laser uniblitz
# old location
#spl_uniblitz_evr_code = EpicsSignal('EVR:MEC:USR01:TRIG5:TEC')
#spl_uniblitz_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG5:TCTL')
spl_uniblitz_evr_code = EpicsSignal('MEC:LAS:EVR:01:TRIG0:TEC')
spl_uniblitz_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG0:TCTL')
# 0: negative
# 1: positive
spl_uniblitz_6mm = EpicsSignal('MEC:LAS:DDG:08:cdOutputPolarityBO')
spl_uniblitz_65mm = EpicsSignal('MEC:LAS:DDG:08:abOutputPolarityBO')
# 2: AB
# 3: AB, CD
spl_uniblitz_inh = EpicsSignal('MEC:LAS:DDG:08:triggerInhibitMO')

# GAIA dgbox channel to change the timing
gaia_dgbox = EpicsSignal('MEC:LAS:DDG:06:cDelayAO')

# filter wheel PVs
fw4inc = EpicsSignal('MEC:LAS:FW:04:IncPos.PROC')
fw4dec = EpicsSignal('MEC:LAS:FW:04:DecPos.PROC')
fw4pos = EpicsSignal('MEC:LAS:FW:04:Position')


# digitizer
dg0_wvfm = EpicsSignal("MEC:QADC:01:OUT0")
dg1_wvfm = EpicsSignal("MEC:QADC:01:OUT1")

### All the user pvs we need for the macro's below:
pinhx=EpicsSignal('MEC:NOTE:DOUBLE:01')
pinhy=EpicsSignal('MEC:NOTE:DOUBLE:02')
pinhz=EpicsSignal('MEC:NOTE:DOUBLE:03')
pintgx=EpicsSignal('MEC:NOTE:DOUBLE:04')

yaghx=EpicsSignal('MEC:NOTE:DOUBLE:05')
yaghy=EpicsSignal('MEC:NOTE:DOUBLE:06')
yaghz=EpicsSignal('MEC:NOTE:DOUBLE:07')
yagtgx=EpicsSignal('MEC:NOTE:DOUBLE:08')

tihx=EpicsSignal('MEC:NOTE:DOUBLE:09')
tihy=EpicsSignal('MEC:NOTE:DOUBLE:10')
tihz=EpicsSignal('MEC:NOTE:DOUBLE:11')
titgx=EpicsSignal('MEC:NOTE:DOUBLE:12')

gridhx=EpicsSignal('MEC:NOTE:DOUBLE:13')
gridhy=EpicsSignal('MEC:NOTE:DOUBLE:14')
gridhz=EpicsSignal('MEC:NOTE:DOUBLE:15')
gridtgx=EpicsSignal('MEC:NOTE:DOUBLE:16')

diode500mm=EpicsSignal('MEC:NOTE:DOUBLE:21')
gige4500mm=EpicsSignal('MEC:NOTE:DOUBLE:22')
zyla500mm=EpicsSignal('MEC:NOTE:DOUBLE:23')
spectro500mm=EpicsSignal('MEC:NOTE:DOUBLE:59')

pinholehx=EpicsSignal('MEC:NOTE:DOUBLE:24')
pinholehy=EpicsSignal('MEC:NOTE:DOUBLE:25')
pinholehz=EpicsSignal('MEC:NOTE:DOUBLE:26')
pinholetgx=EpicsSignal('MEC:NOTE:DOUBLE:27')

ceo2hx=EpicsSignal('MEC:NOTE:DOUBLE:28')
ceo2hy=EpicsSignal('MEC:NOTE:DOUBLE:29')
ceo2hz=EpicsSignal('MEC:NOTE:DOUBLE:30')
ceo2tgx=EpicsSignal('MEC:NOTE:DOUBLE:31')

lab6hx=EpicsSignal('MEC:NOTE:DOUBLE:32')
lab6hy=EpicsSignal('MEC:NOTE:DOUBLE:33')
lab6hz=EpicsSignal('MEC:NOTE:DOUBLE:34')
lab6tgx=EpicsSignal('MEC:NOTE:DOUBLE:35')

cuhx=EpicsSignal('MEC:NOTE:DOUBLE:17')
cuhy=EpicsSignal('MEC:NOTE:DOUBLE:18')
cuhz=EpicsSignal('MEC:NOTE:DOUBLE:19')
cutgx=EpicsSignal('MEC:NOTE:DOUBLE:20')


# zntgx=EpicsSignal('MEC:NOTE:DOUBLE:53')
# znhx=EpicsSignal('MEC:NOTE:DOUBLE:54')
# znhy=EpicsSignal('MEC:NOTE:DOUBLE:55')
# znhz=EpicsSignal('MEC:NOTE:DOUBLE:56')

epics_chi = EpicsSignal('MEC:NOTE:DOUBLE:50')
epics_phi = EpicsSignal('MEC:NOTE:DOUBLE:51')
epics_omega = EpicsSignal('MEC:NOTE:DOUBLE:52')
epics_du = EpicsSignal('MEC:NOTE:DOUBLE:53')
epics_dv = EpicsSignal('MEC:NOTE:DOUBLE:54')
epics_dw = EpicsSignal('MEC:NOTE:DOUBLE:55')
epics_sleep_time = EpicsSignal('MEC:NOTE:DOUBLE:56')


targetsavehx=EpicsSignal('MEC:NOTE:DOUBLE:37')
targetsavehy=EpicsSignal('MEC:NOTE:DOUBLE:38')
targetsavehz=EpicsSignal('MEC:NOTE:DOUBLE:39')
targetsavetgx=EpicsSignal('MEC:NOTE:DOUBLE:40')

gaiatimingsave=EpicsSignal('MEC:NOTE:DOUBLE:49')
tt_delay_motor=Motor('MEC:LAS:MMN:19', name='tt_delay_line')

# getting EVR button status for the SPL slicer
spl_slicer_evr_code = EpicsSignal('LAS:MEC:EVR:03:TRIG2:TEC')
spl_slicer_evr_btn = EpicsSignal('LAS:MEC:EVR:03:TRIG2:TCTL')

# getting EVR button status for the LPL slicer and lamps
lpl_slicer_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG7:TCTL')
lpl_lamps_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG6:TCTL')

# getting charging status from the PFN GUI
lpl_charge_status=EpicsSignal('MEC:PFN:CHARGE_OK')
lpl_charge_btn=EpicsSignal('MEC:PFN:START_CHARGE')

# getting event code and EVR button status for the VISAR laser and streak cameras
visar_streak_evt_code = EpicsSignal('EVR:MEC:USR01:TRIG4:TEC')
visar_streak_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG4:TCTL')
visar_laser_evt_code = EpicsSignal('EVR:MEC:USR01:TRIGA:TEC')
visar_laser_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIGA:TCTL')

# test solution when the MEC attenuators are stalled (it was added before each SiT commands
att1_btn=EpicsSignal('MEC:HXM:MMS:05:UPDATE_STATUS.PROC')
att2_btn=EpicsSignal('MEC:HXM:MMS:06:UPDATE_STATUS.PROC')
att3_btn=EpicsSignal('MEC:HXM:MMS:07:UPDATE_STATUS.PROC')
att4_btn=EpicsSignal('MEC:HXM:MMS:08:UPDATE_STATUS.PROC')
att5_btn=EpicsSignal('MEC:HXM:MMS:09:UPDATE_STATUS.PROC')
att6_btn=EpicsSignal('MEC:HXM:MMS:10:UPDATE_STATUS.PROC')
att7_btn=EpicsSignal('MEC:HXM:MMS:11:UPDATE_STATUS.PROC')
att8_btn=EpicsSignal('MEC:HXM:MMS:12:UPDATE_STATUS.PROC')
att9_btn=EpicsSignal('MEC:HXM:MMS:13:UPDATE_STATUS.PROC')
att10_btn=EpicsSignal('MEC:HXM:MMS:14:UPDATE_STATUS.PROC')
attClear_btn=EpicsSignal('MEC:ATT:COM:STATUS')
def att_update():
	att1_btn.put(1)
	att2_btn.put(1)
	att3_btn.put(1)
	att4_btn.put(1)
	att5_btn.put(1)
	att6_btn.put(1)
	att7_btn.put(1)
	att8_btn.put(1)
	att9_btn.put(1)
	att10_btn.put(1)
	attClear_btn.put(1)


# event seauencer control
evt_seq_btn = EpicsSignal('ECS:SYS0:6:PLYCTL')

def visar1_remote():
    '''
    Description: start a remote session of the VISAR1 PC GUI.
    '''
    os.system('vncviewer 172.21.46.71 &')
    print('Password is:')
    print('Mechutch')

def visar2_remote():
    '''
    Description: start a remote session of the VISAR2 PC GUI.
    '''
    os.system('vncviewer 172.21.46.88 &')
    print('Password is:')
    print('Mechutch')

def wfs1_remote():
    '''
    Description: start a remote session of the Phasics PC 01 GUI.
    '''
    #ssh -X mec-daq /usr/bin/vncviewer 172.21.46.218 &
    os.system('ssh -X mec-control /usr/bin/vncviewer 172.21.46.218 &')
#    os.system('ssh -X mec-control /usr/bin/vncviewer 192.168.8.101 &')
#    print('Password is:')
#    print('Mechutch')

def wfs2_remote():
    '''
    Description: start a remote session of the Phasics PC 02 GUI.
    '''
    os.system('ssh -X mec-control /usr/bin/vncviewer 172.21.46.219 &')

def scope_timing_remote():
    '''
    Description: start a remote session of the Scope Timing PC GUI.
    '''
    os.system('vncviewer 172.21.46.60 &')

def digitizer_gui():
    '''
    Description: start the digitizer GUI, it lives in Mike Browne path so to change later when stable.
    '''
    os.system('/cds/home/m/mcbrowne/trunk2/ioc/common/qadc/children/build/iocBoot/ioc-mec-qadc134/edm-ioc-mec-qadc134.cmd&')
    print('Press Enter to return to python prompt.')

def load_presets():
    '''
    Description: load the presets defined in the file stage_presets.txt located at the
    path /reg/g/pcds/pyps/apps/hutch-python/mec/mec/macros/. You need to login with your
    own unix account to modify this file.
    '''

    arr_presets = np.loadtxt('/reg/g/pcds/pyps/apps/hutch-python/mec/mec/macros/stage_presets.txt')
    return arr_presets

def fel_pulse_energy():
    '''
    Description: Get the pulse energy being the mean value of the GMD sensors in the FEE
    IN:
        NONE
    OUT:
        float with pulse energy in mJ
    '''
    arr = np.zeros(4)
    arr[0] = gmd_241.get()
    arr[1] = gmd_242.get()
    arr[2] = gmd_361.get()
    arr[3] = gmd_362.get()
    return np.mean(arr)

# method to prepare for visar alignment
def visar_mode(status = 'ready'):
    '''
    Description: get the VISAR triggering system ready for alignment or shot, changing the visar
    laser and streak camera EVR. It will force the evr button to be enabled.

    IN:
        status: 'ready' for laser shot (182), 'align' for alignment mode (43 and 44), 'daq' for
        169 used to control the VISAR in the daq, so used for both alignment and on-shot, 'move' for disabling the visar light only when ;oving from target to target
    OUT:
        set the EVR to the right value
    '''
    # look at the event code
    if (status == 'ready'):
        visar_streak_evt_code.put(182)
        visar_laser_evt_code.put(182)
    if (status == 'align'):
        visar_streak_evt_code.put(44)
        visar_laser_evt_code.put(43)
    if (status == 'daq'):
        visar_streak_evt_code.put(169)
        visar_laser_evt_code.put(43)

    # look at the button status (enabled:1 or diabled:0)
    if (visar_streak_evr_btn.get() == 0):
        visar_streak_evr_btn.put(1)
    if (visar_laser_evr_btn.get() == 0):
        visar_laser_evr_btn.put(1)
    if (status == 'move'):
        visar_laser_evr_btn.put(0)


# set the calibrant list used on the MEC calibration cartridge
calibrant_list = ['CeO2', 'ceo2', 'LaB6', 'lab6', 'Ti', 'ti', 'Cu', 'cu', 'Zn', 'zn']

# method to save multiple xray only shotsi and/or visar references
def ref_only(xray_trans=1, xray_num=10, shutters=False, dark=0, daq_end=True, calibrant='', rate=1, visar=False, save=False, slow_cam=False):
    '''
    Description: script to take xray only events and/or VISAR references.
    IN:
        xray_trans : decimal value of the xray transmission
        xray_num   : number of x-rays to send on target
        dark       : default is 0, we do not record a dark run before the reference
        shutters   : default is False, we do not need to close the shutters for references
        calibrant  : if not empty, will move to specified calibrant and take calibration run only
        visar      : True if you want to take visar references
        daq_end    : close the run at the end of a shot. Set to True allows a user to see the result of the shot for longer.
        rate       : rate used to take the reference, it is set to 1 by default bu is changed depending on the options (visar, calib)

        save       : True to save to the DAQ, False otherwise
    OUT:
        execute the plan
    '''
    x.nsl._config['rate']=rate
    x.nsl._config['slowcam'] = slow_cam
    # make sure the daq is not connected before starting the command
    if (daq.connected == True):
        daq.disconnect()
    x.nsl.configure(x.nsl._config)
    msg = '{} x-ray only shots at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_log_target)
    tags_ref = ['reference', 'xray']
    # look at the button status to make sure the VISAR triggers are disabled by default (behind overwritten later with visar option), (enabled:1 or disabled:0)
    if (visar_streak_evr_btn.get() == 1):
        visar_streak_evr_btn.put(0)
    if (visar_laser_evr_btn.get() == 1):
        visar_laser_evr_btn.put(0)

    # force VISAR to false to make sure triggers are not enabled if rate is greater than 1 Hz
    # it also means it changes the rate of acquisition to 1Hz to match VISAR capabilities only when it is set to 1
    if (rate > 1):
        visar = False
        print('Rate is not 1 Hz, so the VISAR is disabled. You should also remove the VISAR from the DAQ partition to prevent damaged events.')

    # check if there is a calibrant in the corresponding argument, needs to be done before visar test
    if (calibrant in calibrant_list):
        print('Running X-ray Calibration shots only.')
        tags_ref = ['calibration', 'xray', calibrant]
        x.nsl._config['rate']=rate
        # start by moving on target
        if ((calibrant == 'CeO2') or (calibrant == 'ceo2')):
            ceo2()
            msg_calib_target = 'on CeO2'
        if ((calibrant == 'LaB6') or (calibrant == 'lab6')):
            lab6()
            msg_calib_target = 'on LaB6'
        if ((calibrant == 'Ti') or (calibrant == 'ti')):
            ti()
            msg_calib_target = 'on Ti'
        if ((calibrant == 'Cu') or (calibrant == 'cu')):
            cu()
            msg_calib_target = 'on Cu 5 mic'
        if ((calibrant == 'Zn') or (calibrant == 'zn')):
            zn()
            msg_calib_target = 'on Zn 2.5 mic'
        # use 10Hz rep rate to get calibration shots only when visar is not triggered
        # use 1Hz rep rate to get calibration shots and move in between shots manually
        if (rate == 1):
            print('You can move between shots (rate = 1 Hz).')
        msg = '{} x-ray only calibration shots at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_calib_target)

    if (visar == True):
        # make sure the visar event codes are properly set
        visar_mode(status='daq')
        print('Visar reference is being saved in the DAQ.')
        tags_ref = tags_ref + ['visar']
        msg = '{} x-ray only shots at {:.4f}% and {} visar reference image(s) {}.'.format(xray_num, 100.0 * xray_trans, xray_num, msg_log_target)
        if (calibrant in calibrant_list):
            msg = '{} x-ray only, calibration shots at {:.4f}% and {} visar reference image(s) {}.'.format(xray_num, 100.0 * xray_trans, xray_num, msg_calib_target)

    # check if a dark is necessary
    if (dark > 0):
         x.nsl.predark=dark
         print('Taking a dark reference image.')
    else:
         x.nsl.predark=0
         print('No dark reference image taken.')

    # check if shutters are necessary
    if (shutters == True):
         x.nsl.shutters=[1, 2, 3, 4, 5, 6]
    else:
         x.nsl.shutters=[]
         print('Shutters are left open.')
    pp.flipflop()
    x.nsl.prex=xray_num
    x.nsl.during=0
    att_update()
    SiT(xray_trans)
    if (daq_end == True):
        p=x.nsl.shot(record=save, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=save, end_run=False)
    RE(p)
    if (save == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        mecl.post(msg, run=RunNumber, tags=tags_ref)
    # restore laser rep rate in case the next action does not involve the use of the following scripts (like shots from the hutch)
    x.nsl._config['rate']=10

# method to perform a pump-probe LPL shot
def optical_shot(shutter_close=[1, 2, 3, 4, 5, 6], lpl_ener=1.0, timing=0.0e-9, xray_threshold=0.1, xray_trans=1, prex=0, save=True, daq_end=True, msg='', ps_opt=True, arms='all', tags_words=['optical', 'sample'], uxi=False, auto_trig=False, auto_charge=False, visar=True, slow_cam=False, debug=True):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        shutter_close   : array of shutters in front of viewport to close during laser shots
        lpl_ener        : waveplate settings for the lpl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        timing          : moves absolute, in s
        xray_threshold  : threshold energy in mJ below which the shot is NOT proceeding and loop until FEL energy is back
        xray_trans      : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        prex            : when True, allows to take one Xray or visar reference
        save            : save the run when True (default).
        daq_end         : if True, it will allow the DAQ to keep the data on screen until daq.disconnect() is used.
        msg             : message to post to the elog
        ps_opt          : if True, enable the optimization of the pulse shaping routine
        arms            : all, ABGH, EFIJ are valid
        tags_words      : accompagnying tags to the elog
        uxi             : when True, it sets the repetition rate of the sequencer to 0.5 Hz so that the pulse picker delta beam are properly calculated
        auto_trig       : True to make sure the triggers are enabled, False otherwise (simulation test for example).False by default.
        auto_charge     : True to charge automatically the PFN. False by default.
        visar           : True to check that the VISAR triggers are set properly.
        slow_cam        : Change the state of the configuration file for slow devices like cameras or gas jets
        debug           : True to enable debugging functions
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # make sure the daq is not connected before starting the command
    x.nsl._config['slowcam'] = slow_cam
    # debugging flags for various subsystems
    if (debug == True):
        # displays the status of the internal shutters of the optical laser to help debugging interaction issues
        print('Start debugging functions ---')
        TTL_shutter_status(display=True)
        print('End debugging functions ---')
    # force disconnect the DAQ before starting a new sequence
    if (daq.connected == True):
        daq.disconnect()
    x.nsl.configure(x.nsl._config)
    # charging process
    if ((arms == 'all') or (arms == 'ABGH') or (arms == 'EFIJ') or (arms=='AB') or (arms=='ABEF')or(arms=='GHIJ') or (arms=='EF') or (arms=='GH') or (arms=='IJ')):
        ARMonly(arms, set_T=lpl_ener)
        time.sleep(5)
        if (auto_charge == True):
            print("Waiting until charging is authorized ...")
            while lpl_charge_status.get()==0:
               time.sleep(1)
            if (lpl_charge_status.get() == 1):
                lpl_charge_btn.put(1)
                print('Auto charging the laser, waiting 15 sec to be completed...')
                time.sleep(15)
                print('Laser should be charged, check it!')
        else:
            print('Auto charging is disabled, make sure to press the button on the GUI!')
    # VISAR checks
    if (visar == True):
        # make sure the visar event codes are properly set
        visar_mode(status='daq')
    # to change and display the timing of the Xrays vs the LPL
    nstiming.mv(timing)
    nstiming.get_delay()
    # to change the Xray transmission for the driven shot
    att_update()
    SiT(xray_trans)
    # check the trigger status
    if (auto_trig == True):
        if (lpl_slicer_evr_btn.get() == 0):
            lpl_slicer_evr_btn.put(1)
        if (lpl_lamps_evr_btn.get() == 0):
            lpl_lamps_evr_btn.put(1)
        print('NS slicer and Lamps trigger buttons are Enabled.')
    else:
        print('NS slicer and Lamps trigger buttons are not being checked by the script.')
    if (uxi == True):
        # to setup the plan for a driven shot where the UXI detector are being used
        x.nsl._config['rate']=0.5
    else:
        # to setup the plan for a driven shot, and make sure the rate for the drive laser is 10 Hz
        x.nsl._config['rate']=10
    # force the use of the shutters as you are driving the target
    x.nsl.shutters=shutter_close
    x.nsl.predark=0
    x.nsl.prex=prex
    x.nsl.during=1
    # to set the plan with the new configuration
    if (daq_end == True):
        p=x.nsl.shot(record=save, ps=ps_opt, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=save, ps=ps_opt, end_run=False)
    # loop before the shot to check that FEL pulse energy is above a threshold: if the FEL drops within 10 sec, then we cannot do much with this moethod
    # getting the energy value once to evaluate what to do otherwise might be using a different pulse. Still might be unprecise since this is a BLD value which is refreshed faster than the epics feedback I guess.
    fel_ener = fel_pulse_energy()
    while (fel_ener < xray_threshold):
        time.sleep(1)
        logger.critical('FEL pulse energy too low!')
        logger.critical('waiting to recover or call ACR at x2151...')
        fel_ener = fel_pulse_energy()
    else:
        logger.success('FEL pulse energy is {:.3f} mJ.'.format(fel_ener))
    # to run the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = msg + '{} arms, laser shot {}: laser energy is at {:.1f} % from max, delay is {:.2f} ns, SiT at {:.1f} %.'.format(arms, msg_log_target, 100.0 * lpl_ener, 1.0e9 * timing, 100.0 * xray_trans)
    mecl.post(msg, run=RunNumber, tags=tags_words)
    # make sure the event sequencer is getting ready for the alignment mode of the VISAR by starting the event sequencer at 1Hz, and no need to touch the trigger as they are ready for this task
    x.start_seq(1)
    # restore the number of prex shots after the driven shot. Could restore the entire default config at some point.
    x.nsl.prex=0


# For delay line in the chamber:
# delay_line_t0 to change manually for now
# mm
delay_line_t0 = 36.616
# mm/ps
delay_line_calib = 0.149896229

def spl_timing_save_t0():
    '''
    Description : saving the current VITARA position to a PV
    '''
    global spl_timing_tmp
    spl_timing_tmp = spl_vitara_pv.put(spl_vitara.get())
    print('The timing is set at {} ns.'.format(spl_timing_tmp))

def spl_timing(mono='out', timing=0.0e-9):
    '''
    Description : setting a new pump-probe delay
    IN          :
        mono    : defines if you want timing between mono IN or OUT
        timing  : value for the Xrays to arrive 'timing' ns later than optical laser when positive.
    '''
    global delay_line_t0, delay_line_calib
    if (mono == 'out'):
        spl_vitara.put(spl_vitara_pv.get() - (timing / 1.0e-9))
        print('Timing done with Mono OUT.')
    if (mono == 'in'):
        spl_vitara.put((spl_vitara_pv.get() + (1.116)) - (timing / 1.0e-9))
        print('Timing done with Mono IN.')
    # moving delay line:
    tt_delay_offset = (timing / 1.0e-12) * delay_line_calib
    tt_delay_motor.umv(delay_line_t0 - tt_delay_offset)
    print('Moved delay line to compensate for drive timing.')
    print('New timing is {} ns after the optical laser.'.format(timing/ 1.0e-9))

def spl_mode(mode='alignment'):
    '''
    Description: Set the uniblitz and inhibit configuration for single shot (ss), continuous 5Hz (5Hz) and alignment mode (alignment).
    IN:
        mode: ss, 5Hz, alignment
    '''
    # disable the spl slicer before changing mode
    spl_slicer_evr_btn.put(0)
    print('SPL slicer trigger button is Disabled.')
    # force disable the uniblitz triggering
    spl_uniblitz_evr_btn.put(0)
    print('SPL uniblitz trigger button is Disabled.')
    # setting uniblitz event code
    spl_uniblitz_evr_code.put(177)
    if (mode == 'alignment'):
        spl_uniblitz_65mm.put(1)
        # waiting for the 65mm uniblitz to open
        time.sleep(0.2)
        print('Setting polarity on 65 mm uniblitz to open (positive).')
        spl_uniblitz_6mm.put(1)
        print('Setting polarity on 6 mm uniblitz to open (positive).')
        spl_uniblitz_inh.put(3)
        print('Setting inhibit channels for the 6 and 65 mm uniblitz.')
#    if (mode == '5Hz'):
#        spl_uniblitz_6mm.put(0)
#        print('Setting polarity on 6 mm uniblitz to close (negative).')
#        spl_uniblitz_65mm.put(0)
#        print('Setting polarity on 65 mm uniblitz to close (negative).')
#        spl_uniblitz_inh.put(0)
#        print('Setting inhibit channels for the 65 mm uniblitz.')
    if (mode == 'single_shot'):
        spl_uniblitz_6mm.put(0)
        # waiting for the 6mm uniblitz to close\
        time.sleep(0.2)
        print('Setting polarity on 6 mm uniblitz to close (negative).')
        spl_uniblitz_65mm.put(0)
        print('Setting polarity on 65 mm uniblitz to close (negative).')
        spl_uniblitz_inh.put(0)
        print('Setting inhibit triggers off.')
    # force enable the uniblitz triggering
    spl_uniblitz_evr_btn.put(1)
    print('Force enabling the triggering of the uniblitz.')


spl_sequence = [[177, 12, 0, 0],
                [168, 10, 0, 0],
                [176,  2, 0, 0],
                [169,  0, 0, 0]]

def spl_shot(nshot=1, gaia_offset=0., delay=0.0e-9, xray_trans=1, msg='', tags_words=['optical', 'sample'], auto_trig=True, save_data=True, freeze_daq=False):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        nshot      : defines the nu;ber of shots, less than 10 for bluesky3 script, otherwise evt sequencer is used
        spl_ener   : gaia timing to control the spl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        delay      : moves absolute, in s
        xray_trans : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        msg        : message to post to the elog
        tags_words : accompagnying tags to the elog
        auto_trig  : True to make sure the triggers are enabled, False otherwise (simulation test for example)
        save_data  : save the data in teh DAQ if True, otherwise don't
        freeze_daq : allows to see the last run. Requires a daq.disconnect() after the shot to preprare for the next shot.
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # to change the Xray transmission for the driven shot
    att_update()
    SiT(xray_trans)
    # set the uniblitz mode to provide 5Hz but protected by the uniblitz. Used for all DAQ modes.
    spl_mode(mode='single_shot')
    time.sleep(0.2)
    gaia_timing_offset(gaia_offset)
    # set probe timing
    spl_timing(timing=delay)
    # check the trigger status
    if (auto_trig == True):
        # look at the event code
        spl_slicer_evr_code.put(176)
        # sleep time necessary to make sure the trigger is properly enabled
        time.sleep(0.2)
        if (spl_slicer_evr_btn.get() == 0):
            spl_slicer_evr_btn.put(1)
        print('SPL slicer trigger button is Enabled.')
    else:
        print('SPL slicer trigger button is not being checked by the script.')
    if (nshot < 10):
        # to setup the plan for a driven shot, and make sure the rate for the drive laser is 10 Hz
        x.fsl._config['rate']=5
        # force the use of the shutters as you are driving the target
        x.fsl.shutters=[1, 3]
        x.fsl.prelasertrig=12 #24
        x.fsl.predark=0
        x.fsl.prex=0
        x.fsl.during=nshot
        # to set the plan with the new configuration
        p=x.fsl.shot(record=save_data, end_run=freeze_daq)
        # to run the plan
        RE(p)
        # make sure the event sequencer is getting ready for the 'continuous' shot mode'
        time.sleep(0.2)
        #x.start_seq(5)
    else:
        shutter1.close()
        shutter3.close()
        seq.sequence.put_seq(spl_sequence)
        seq.play_mode.put(1)
        seq.rep_count.put(nshot)
        daq.begin(record=save_data, events=nshot)
        seq.start()
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    if (save_data == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg = msg + '{} laser shot(s): gaia timing is {:.1f} ns from max, delay is {:.2f} ps, SiT at {:.1f} %.'.format(nshot, gaia_offset, 1.0e12 * delay, 100.0 * xray_trans)
        mecl.post(msg, run=RunNumber, tags=tags_words)



sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}

def pulse_picker(rate = 5):
        '''
        Description:
            Set the event sequencer to allow for the pulse picker to run at a dedicated rate while the DAQ is also set to run (for the cameras to trigger).
        IN:
            rate : default 5 Hz, but can be anything between 0.5, 1, 5, 10, 30, 60, 120, 360 Hz.
        OUT:
            set a sequence in the event sequence and run it
        '''
        # reset the mode for the pp
        pp.reset()
        # set the flip/flop mode
        pp.flipflop()
        # calculate the delta beam coresponding to the rate
        bd = int(120/rate) # Beam deltas per laser shot
        # create a simple sequence based on the rate qnd devices of interest: pulse picker and DAQ only
        alignment_mode = [[168, bd-2, 0, 0],[169,  2, 0, 0]]
        print('Using simple sequence: {}'.format(alignment_mode))
        # set the syn ;qrker in teh event sequencer
        sync_mark = int(sync_markers[rate])
        seq.sync_marker.put(sync_mark)
        # push the sequence
        seq.sequence.put_seq(alignment_mode)
        seq.play_mode.put(2)
        seq.start()
        logger.success('Pulse Picker running at {} Hz.'.format(rate))

# rolling status definitions
def ps():
    if (mec_bxl_valve.position == 'OUT'):
        logger.success('Gatevalve BXL:VGC:01 (XRT DCO) is OUT')
    elif (mec_bxl_valve.position == 'IN'):
        logger.critical('Gatevalve BXL:VGC:01 (XRT DCO) is IN')
    if (mec_hxm_valve.position == 'OUT'):
        logger.success('Gatevalve HXN:VGC:01 (XRT S6) is OUT')
    elif (mec_hxm_valve.position == 'IN'):
        logger.critical('Gatevalve HXM:VGC:01 (XRT S6) is IN')
    if (sh2.position == 'OUT'):
        logger.success('Stopper 2 (SH2) is OUT')
    elif (sh2.position == 'IN'):
        logger.critical('Stopper 2 (SH2) is IN')
    if (sh6.position == 'OUT'):
        logger.success('Stopper 6 (MEC) is OUT')
    elif (sh6.position == 'IN'):
        logger.critical('Stopper 6 (MEC) is IN')
    print("reflaser (1.0 is IN) :" +str(ref_y.position))
    if (yag0.position == 'OUT'):
        logger.success('Yag 0 is OUT')
    elif (yag0.position == 'YAG'):
        logger.critical('Yag 0 is IN')
    if (yag1.position == 'OUT'):
        logger.success('Yag 1 is OUT')
    elif (yag1.position == 'YAG'):
        logger.critical('Yag 1 is IN')
    if (yag2.position == 'OUT'):
        logger.success('Yag 2 is OUT')
    elif (yag2.position == 'YAG'):
        logger.critical('Yag 2 is IN')
    if (yag3.position == 'OUT'):
        logger.success('Yag 3 is OUT')
    elif (yag3.position == 'YAG'):
        logger.critical('Yag 3 is IN')
    if (pp.get()[0] == 'CLOSE'):
        logger.critical('Pulse Picker is CLOSED.')
    else:
        logger.success('Pulse Picker is OPEN.')
    print("at1l0 transmission : " +str(at1l0.position))
    print("at2l0 transmission : " +str(at2l0.position))
    print("Si transmission : "+str(SiT()))
    print("slit 1 : "+str(slit1.position))
    print("slit 2 : "+str(slit2.position))
    print("slit 3 : "+str(slit3.position))
    print("slit 4 : "+str(slit4.position))
    print("IPMs : UNKNOWN POSITION")
    be_stack = be_lens_stack.get()
    if ((be_stack == 1) or (be_stack == 2) or (be_stack == 3)):
        logger.warning('Be lens stack {} is IN.'.format(be_stack))
    else:
        logger.error('Be lens stack OUT.')
    print("HRM : UNKNOWN POSITION")
    print("******************************************************")
    if (shutter1.isopen):
        logger.warning('Shutter 1 is Open, proceed with caution.')
    elif (shutter1.isclosed):
        logger.success('Shutter 1 is Closed.')
    if (shutter2.isopen):
        logger.warning('Shutter 2 is Open, proceed with caution.')
    elif (shutter2.isclosed):
        logger.success('Shutter 2 is Closed.')
    if (shutter3.isopen):
        logger.warning('Shutter 3 is Open, proceed with caution.')
    elif (shutter3.isclosed):
        logger.success('Shutter 3 is Closed.')
    if (shutter4.isopen):
        logger.warning('Shutter 4 is Open, proceed with caution.')
    elif (shutter4.isclosed):
        logger.success('Shutter 4 is Closed.')
    if (shutter5.isopen):
        logger.warning('Shutter 5 is Open, proceed with caution.')
    elif (shutter5.isclosed):
        logger.success('Shutter 5 is Closed.')
    if (shutter6.isopen):
        logger.warning('Shutter 6 is Open, proceed with caution.')
    elif (shutter6.isclosed):
        logger.success('Shutter 6 is Closed.')

def rs():
    while True:
        time.sleep(1)
        print("STATUS at "+str(datetime.now()))
        print("******************************************************")
        ps()
        print("******************************************************")

# presets definitions
#def motor_wait(motor=None, value=None):
#    delta = 0.1
#    print('Moving...')
#    if (motor == tgx):
#        while ((motor.position <= (value - delta)) and (motor.position >= (value + delta))):
#            time.sleep(0.2)
#    else:
#        while ((motor.get() <= (value - delta)) and (motor.get() >= (value + delta))):
#            print('in')
#            time.sleep(0.2)
#        print('out', motor, motor.get())
#    print('Motor {} reached destination.'.format(motor))

def tg_pin():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[0])
    if (tgx.position != arr[0]):
        time.sleep(10)
        print('Motor X reached destination.')
        #motor_wait(motor=tgx, value = arr[0])
    tgy.put(arr[1])
    if (tgy_rbv.get() != arr[1]):
        time.sleep(10)
        print('Motor Y reached destination.')
        #motor_wait(motor=tgy_rbv, value = arr[1])
    tgz.put(arr[2])
    print('Motor Z reached destination.')
    #motor_wait(motor=tgz_rbv, value = arr[2])

def catcher():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[3])
    if (tgx.position != arr[3]):
        time.sleep(10)
        print('Motor X reached destination.')
    tgy.put(arr[4])
    if (tgy_rbv.get() != arr[4]):
        time.sleep(10)
        print('Motor Y reached destination.')
    tgz.put(arr[5])
    print('Motor Z reached destination.')

def tg_gold():
    arr = load_presets()
    # force going down before any motion
    tgy.put(0)
    time.sleep(7)
    tgx.mv(arr[6])
    if (tgx.position != arr[6]):
        time.sleep(10)
        print('Motor X reached destination.')
    tgy.put(arr[7])
    if (tgy_rbv.get() != arr[7]):
        time.sleep(10)
        print('Motor Y reached destination.')
    tgz.put(arr[8])
    print('Motor Z reached destination.')

def pin():
    """ move to the pin. Uses the User pvs."""
    tgx.mv(pintgx.get())
    tc_hexapod.x.mv(pinhx.get())
    tc_hexapod.y.mv(pinhy.get())
    tc_hexapod.z.mv(pinhz.get())

def pin_s():
    """ saves current position in pin user pv. Uses the User pvs."""
    pintgx.put(tgx())
    pinhx.put(tc_hexapod.x.get()[2])
    pinhy.put(tc_hexapod.y.get()[2])
    pinhz.put(tc_hexapod.z.get()[2])

def pinhole():
    """ move to the pinhole. Uses the User pvs."""
    tgx.mv(pinholetgx.get())
    tc_hexapod.x.mv(pinholehx.get())
    tc_hexapod.y.mv(pinholehy.get())
    tc_hexapod.z.mv(pinholehz.get())

def pinhole_s():
    """ saves current position in pinhole user pv. Uses the User pvs."""
    pinholetgx.put(tgx())
    pinholehx.put(tc_hexapod.x.get()[2])
    pinholehy.put(tc_hexapod.y.get()[2])
    pinholehz.put(tc_hexapod.z.get()[2])

def ceo2():
    """ move to the CeO2 calibrant. Uses the User pvs."""
    tgx.mv(ceo2tgx.get())
    tc_hexapod.x.mv(ceo2hx.get())
    tc_hexapod.y.mv(ceo2hy.get())
    tc_hexapod.z.mv(ceo2hz.get())

def ceo2_s():
    """ saves current position in CeO2 user pv. Uses the User pvs."""
    ceo2tgx.put(tgx())
    ceo2hx.put(tc_hexapod.x.get()[2])
    ceo2hy.put(tc_hexapod.y.get()[2])
    ceo2hz.put(tc_hexapod.z.get()[2])

def lab6():
    """ move to the LaB6 calibrant. Uses the User pvs."""
    tgx.mv(lab6tgx.get())
    tc_hexapod.x.mv(lab6hx.get())
    tc_hexapod.y.mv(lab6hy.get())
    tc_hexapod.z.mv(lab6hz.get())

def lab6_s():
    """ saves current position in LaB6 user pv. Uses the User pvs."""
    lab6tgx.put(tgx())
    lab6hx.put(tc_hexapod.x.get()[2])
    lab6hy.put(tc_hexapod.y.get()[2])
    lab6hz.put(tc_hexapod.z.get()[2])

def cu():
    """ move to the Cu 5 mic calibrant. Uses the User pvs."""
    tgx.mv(cutgx.get())
    tc_hexapod.x.mv(cuhx.get())
    tc_hexapod.y.mv(cuhy.get())
    tc_hexapod.z.mv(cuhz.get())

def cu_s():
    """ saves current position in Cu 5 mic user pv. Uses the User pvs."""
    cutgx.put(tgx())
    cuhx.put(tc_hexapod.x.get()[2])
    cuhy.put(tc_hexapod.y.get()[2])
    cuhz.put(tc_hexapod.z.get()[2])

def zn():
    """ move to the Zn 2.5 mic calibrant. Uses the User pvs."""
    tgx.mv(zntgx.get())
    tc_hexapod.x.mv(znhx.get())
    tc_hexapod.y.mv(znhy.get())
    tc_hexapod.z.mv(znhz.get())

def zn_s():
    """ saves current position in Zn 2.5 mic user pv. Uses the User pvs."""
    zntgx.put(tgx())
    znhx.put(tc_hexapod.x.get()[2])
    znhy.put(tc_hexapod.y.get()[2])
    znhz.put(tc_hexapod.z.get()[2])

def ti():
    """ move to the ti sample. Uses the User pvs."""
    tgx.mv(titgx.get())
    tc_hexapod.x.mv(tihx.get())
    tc_hexapod.y.mv(tihy.get())
    tc_hexapod.z.mv(tihz.get())

def ti_s():
    """ saves current position in ti user pv. Uses the User pvs."""
    titgx.put(tgx())
    tihx.put(tc_hexapod.x.get()[2])
    tihy.put(tc_hexapod.y.get()[2])
    tihz.put(tc_hexapod.z.get()[2])

def grid():
    """ move to the grid sample. Uses the User pvs."""
    tgx.mv(gridtgx.get())
    tc_hexapod.x.mv(gridhx.get())
    tc_hexapod.y.mv(gridhy.get())
    tc_hexapod.z.mv(gridhz.get())

def grid_s():
    """ saves current position in grid user pv. Uses the User pvs."""
    gridtgx.put(tgx())
    gridhx.put(tc_hexapod.x.get()[2])
    gridhy.put(tc_hexapod.y.get()[2])
    gridhz.put(tc_hexapod.z.get()[2])

def yag():
    """ move to the yag."""
    tgx.mv(yagtgx.get())
    tc_hexapod.x.mv(yaghx.get())
    tc_hexapod.y.mv(yaghy.get())
    tc_hexapod.z.mv(yaghz.get())

def yag_s():
    """ saves current position in the yag user pv. Uses the User pvs."""
    yagtgx.put(tgx())
    yaghx.put(tc_hexapod.x.get()[2])
    yaghy.put(tc_hexapod.y.get()[2])
    yaghz.put(tc_hexapod.z.get()[2])

def rc_grid():
    """ move to the ronchi Grid target."""
    print('Moving to Ronchi Grid target.')
    tgx.mv(141.62)
    tc_hexapod.x.mv(-0.1)
    tc_hexapod.y.mv(3.080)
    tc_hexapod.z.mv(-0.220)

def rc_siemens():
    """ move to the ronchi Siemens target."""
    print('Moving to Ronchi Siemens target.')
    tgx.mv(141.62)
    tc_hexapod.x.mv(-0.1)
    tc_hexapod.y.mv(2.780)
    tc_hexapod.z.mv(-0.210)

def xray_pm():
    """ move to the Power Meter."""
    print('Moving to the Power Meter from XPP.')
    s500mm.put(53.0)

def diode_air():
    """ moves the 500mm stage to the in air Diode position in user pv."""
    s500mm.put(diode500mm.get())

def diode_air_s():
    """ Saves current position of the diode in user pvs."""
    diode500mm.put(s500mm.get())

def spectro_air():
    """ moves the 500mm stage to the in air spectrometer position in user pv."""
    s500mm.put(spectro500mm.get())

def spectro_air_s():
    """ Saves current position of the in air spectrometer in user pvs."""
    spectro500mm.put(s500mm.get())

def gige4():
    """ moves the 500mm stage to the in air gige4 position in user pv."""
    s500mm.put(gige4500mm.get())

def gige4_s():
    """ Saves current position of the gige4 in user pvs."""
    gige4500mm.put(s500mm.get())

def zyla():
    """ moves the 500mm stage to the NEO position in user pv."""
    s500mm.put(zyla500mm.get())

def zyla_s():
    """ Saves current position of NEO in user pvs."""
    zyla500mm.put(s500mm.get())

# ----
def gaia_timing_s():
    """ Saves current GAIA timing value."""
    gaiatimingsave.put(gaia_dgbox.get())

def gaia_timing_offset(offset = 0):
    """ Offset the gAIA timing to detune the amplificaiton.
        IN:
            offset : value in ns
    """
    ch_gaia_val = gaiatimingsave.get() + (1.0e-9 * offset)
    gaia_dgbox.set(ch_gaia_val)
    if (offset == 0):
        print('GAIA is timed IN.')
    else:
        print('GAIA is timed off by {} ns.'.format(offset))


def gaia_detune():
    """ Function to offset the gaia timing by 100 ns to not amplify MPA anymore """
    gaia_timing_offset(100)
# ----

def talbot_in():
    """ moves the 500mm stage to the NEO position in user pv."""
    talbot_x.umv(34.15)

def talbot_out():
    """ moves the 500mm stage to the NEO position in user pv."""
    talbot_x.umv(-35)

# target motion definition (TO DO: add target.tweakxy)
def target_up(n=1):
    """ moves up n spaces, spacing is 3.5mm"""
    tc_hexapod.y.mv(tc_hexapod.y.get()[2]+(n*3.5))

def target_down(n=1):
    """ moves down n spaces, spacing is 3.5mm"""
    target_up(-n)

def target_next(n=1):
    """ moves next n spaces, spacing is 3.7mm"""
    tgx(tgx()+(n*3.7))

def target_prev(n=1):
    """ moves previous n spaces, spacing is 3.7mm"""
    target_next(-n)

def target_return():
    """ returns target stage position to previous saved values"""
    tc_hexapod.x.mv(targetsavehx.get())
    tc_hexapod.y.mv(targetsavehy.get())
    tc_hexapod.z.mv(targetsavehz.get())
    tgx(targetsavetgx.get())

def target_save():
    """ saves current target stage position in userpvs. You can go back with target_return() """
    targetsavehx.put(tc_hexapod.x.get()[2])
    targetsavehy.put(tc_hexapod.y.get()[2])
    targetsavehz.put(tc_hexapod.z.get()[2])
    targetsavetgx.put(tgx())

def scan(offset=4., align=0.22, att=1.):
    """ get a white field set of images and then take a set of images with a target in"""
    print('White field, 100 images.')
    tc_hexapod.z.mv(-offset+align)
    time.sleep(5)
    ref_only(xray_trans=1, xray_num=100, dark=False, visar=False, save=True, daq_end=True, rate=10)
    daq.disconnect()
    print('X-ray only on target, 1 image at {}%.'.format(att*100.))
    tc_hexapod.z.mv(align)
    time.sleep(5)
    ref_only(xray_trans=att, xray_num=10, dark=False, visar=False, save=True, daq_end=True, rate=1)
    daq.disconnect()

def scan_n(offset=3., att=.1):
    """ get a white field set of images and then take a set of images with a target in"""
    print('White field, 100 images.')
    hz_t=tc_hexapod.z.get()[2]
    tc_hexapod.z.mv(hz_t+offset)
    time.sleep(5)
    ref_only(xray_trans=1, xray_num=100, dark=False, visar=False, save=True, daq_end=True, rate=10)
    daq.disconnect()
    print('X-ray only on target, 1 image at {}%.'.format(att*100.))
    tc_hexapod.z.mv(hz_t)
    time.sleep(5)
    ref_only(xray_trans=att, xray_num=10, dark=False, visar=False, save=True, daq_end=True, rate=1)
    daq.disconnect()

def references(xray_target=0.1):
    """ produce a set of references with white field and target in and moving the Talbot grating in and out of the beam."""
    x.start_seq(5)
    print('Moving Talbot OUT')
    talbot_out()
    scan(offset=1., align=tc_hexapod.z.get()[2], att=xray_target)
    print('Moving Talbot IN')
    talbot_in()
    scan(offset=1., align=tc_hexapod.z.get()[2], att=xray_target)
    x.start_seq(5)

# -- Definitions for the target motion using letters -------------------------
# up to I for colinear configuration, up to L for the perpendicular
letter_arr = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
# width of a frame in mm
one_u = 40.2
half_u = 19.5
# look from the back of the target holder, 1 is for a full U, 0.5 is for a half U, start from the left
# defining a global variable to store the current target position
msg_log_target = ''

def move_to_target(config='colinear', frame_cfg=[1, 'F1', 1, 'F2', 1, 'F3'], frame=1, target='A1', visar_disable=True):
    '''
    Description: script to move to a predefined target in the target holder. Assuming
    for now that columns are letters, and raws are numbers. Columns start from A and
    finish at I from left to right and raws start from 1 to 7 from top to bottom. All
    these while looking at the target holder from the back (opposite view from questar 1).

    Since every target frame is position a few 100um differt due to screw slop, there are two
    epics user pv that can be set as a correction for each target. These corrections should be
    small (<1mm), and are best reset when going to a different frame. They are the user PVs
    57 and 58.

    IN:
        config          : set the experimental configuration to use. It will enable or disable arguments accordingly.
        frame_cfg       : the configuration of the frames on the target holder as viewed from
                          the back, meaning the opposite view of Q1. TO DO: need to confirm size
                          of the half-U frame.
        frame           : the number of the frame where the targets are located. Can be full size
                          or half size U frame. TO DO: need to confirm size of the half-U frame.
        target          : the number of the target to go to within this frame.
        visar_disable   : disable the visar laser between shots if True to not burn the streak whn gain/energy are increased due to poor target reflectivity
    OUT:
        move to target
    '''
    global msg_log_target

    # extract the values used to correct the aligned position vs the default position
    xcorr=EpicsSignal('MEC:NOTE:DOUBLE:57').get()
    ycorr=EpicsSignal('MEC:NOTE:DOUBLE:58').get()

    # turn off VISAR light before moving to target to prevent damage on the cameras
    if (visar_disable == True):
        visar_mode('move')

    # if the configuration is colinear, use frames
    if (config == 'colinear'):
        print('Configuration: colinear.')
        # 1U is 40mm large, 0.5U is 20mm, starting from just after the calibration cartridge
        # x_start_pos is pin+pos - position of the first frame A1 column value
        # when using the perpendicular beam delivery with target holder perpendicular
        pin_pos = 154.938
        # when using the colinear configuration with the target holder perpendicular to the FEL
        #pin_pos = 154.5
        x_start_pos = 35.81
        y_start_pos = -12.0
        x_step = 3.7
        y_step = 3.5
#        tc_hexapod.x.mv(0.240)
#        tc_hexapod.z.mv(0.590)
        frame_pos = x_start_pos
        if (frame > 1):
    	# -1 to not account for the first frame, and count for the other position in the array
            for idx in np.arange(0, 2*(frame-1), 2):
                if (frame_cfg[idx] == 1):
                    frame_pos = frame_pos + one_u
                else:
                    frame_pos = frame_pos + half_u
        else:
            # the spacing of old half U cartridge is off. Need to check if this is an old or new cartridge.
            if (frame_cfg[0] == 0.5):
                x_step = 4.3
        # starting position from where the target value will be evaluated
        # +1 because the array start
        target_col = letter_arr.index(target[0])+1
        target_raw = int(target[1])
        # initialisation of x and y target positions
        y_target_pos = y_start_pos
        x_target_pos = 0.0
        # calculating the y position of the target
        if (target_raw > 1):
            y_target_pos = y_target_pos + ((target_raw - 1) * y_step)
        # calculatinf the x position of the target
        if (target_col > 1):
            x_target_pos = x_target_pos + ((target_col - 1) * x_step)
        # execute the motion
        tgx.umv(pin_pos - (x_target_pos + frame_pos) + xcorr)
        #tc_hexapod.y.mv(y_target_pos + ycorr)
        tc_hexapod.y.umv(y_target_pos + ycorr)
        print('Moving to Frame {}, target {}.'.format(frame, target))
        print('Tweak position as appropriate.')
        print('The frame configuration is {}.'.format(frame_cfg))
        # print in the eLog only the naming used by the users to avoid confusion
        msg_log_target = 'on frame {}, target {}'.format(frame_cfg[(2*frame)-1], target)

    # if the configuration is perpendicular, use pillars
    if (config == 'perp'):
        print('Configuration: perpendicular.')
        # +1 because the array start
        target_col = letter_arr.index(target[0])+1
        target_raw = int(target[1])
        # initialisation of x and y target positions: reference is first pillar
        x_target_pos = 130.317
        y_target_pos = -12.1
        x_step = 11.303
        y_step = 3.0
        # not sure why these two lines where here so commented them out E.G. 02/
        #tc_hexapod.x.mv(-0.230)
        #tc_hexapod.z.mv(-0.110)
        # calculating the y position of the target
        if (target_raw > 1):
            y_target_pos = y_target_pos + ((target_raw - 1) * y_step)
        # calculatinf the x position of the target
        if (target_col > 1):
            x_target_pos = x_target_pos - ((target_col - 1) * x_step)
        # execute the motion
        tgx.umv(x_target_pos + xcorr)
        tc_hexapod.y.umv(y_target_pos + ycorr)
        print('Moving to target {}.'.format(target))
        print('Tweak position as appropriate.')
        # print in the eLog only the naming used by the users to avoid confusion
        msg_log_target = 'on target {}'.format(target)

    # restore DAQ status for VISAR readiness to see visar light
    if (visar_disable == True):
        visar_mode('daq')


# -----------------------------------------------------------------------------

# shutters definitions
def shutters_close():
    shutter1.close()
    shutter2.close()
    shutter3.close()
    shutter4.close()
    shutter5.close()
    shutter6.close()

def shutters_open():
    shutter1.open()
    shutter2.open()
    shutter3.open()
    shutter4.open()
    shutter5.open()
    shutter6.open()

# dictionary for visar 1 and 2 PV names used to store the streak window timing. Gives the window in sec.
visar_window_pv = {\
'visar1_2ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY2d0'),
'visar1_5ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY5d0'),
'visar1_10ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY10d'),
'visar1_20ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY20d'),
'visar1_50ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY50d'),
'visar1_100ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY100'),
'visar1_200ns':EpicsSignal('MEC:NOTE:VIS:CAM1_DELAY200'),
'visar2_2ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY2d0'),
'visar2_5ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY5d0'),
'visar2_10ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY10d'),
'visar2_20ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY20d'),
'visar2_50ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY50d'),
'visar2_100ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY100'),
'visar2_200ns':EpicsSignal('MEC:NOTE:VIS:CAM2_DELAY200')}

# dictionnary of the streak window as per the GUI. Second number is streak window in ns.
visar_window_remote = {0:0.5, 1:1, 2:2, 3:5, 4:10, 5:20, 6:50, 7:100, 8:200, 9:500, 10:1000, 11:2000, 12:5000, 13:10000, 14:20000, 15:50000}

# getting the visar streak windows and the values from the timing box
visar1_window = EpicsSignal('MEC:STREAK:01:TimeRange')
visar2_window = EpicsSignal('MEC:STREAK:02:TimeRange')
visar1_dgbox = EpicsSignal('MEC:LAS:DDG:05:aDelayAO')
visar2_dgbox = EpicsSignal('MEC:LAS:DDG:05:eDelayAO')

def streak_timing_status(verbose=False, save=False):
    '''
    Description: displays the status of the timing configuration for both VISAR system. It will require to have the Xremote up and running.
    IN:
        verbose : add some more info on the timing configuration.
        save    : push the entire current configuration to the elog.
    OUT:
        displays timing info for the VISAR system
    '''
    # getting the visar streak window
    visar1_current_window = visar1_window.get()
    visar2_current_window = visar2_window.get()

    msg = ''
    # getting the saved delays for eah visar windows.
    for j in range(1, 3):
        tmp_chr = 'Visar {} timing:'.format(str(j))
        msg = msg + '\n' + tmp_chr
        if (verbose == True):
            print(tmp_chr)
        for i in range(2, 9):
            val = visar_window_remote[i]
            tmp_chr = '{:3d} ns window, {:.12f} ns delay'.format(val, visar_window_pv['visar'+str(j)+'_'+str(val)+'ns'].get())
            msg = msg + '\n' + tmp_chr
            if (verbose == True):
                print(tmp_chr)
        if (verbose == True):
            print('')
        msg = msg + '\n'

    # get the current streak delay, if any, at the current streak window
    visar1_delay = visar1_dgbox.get() - visar_window_pv['visar1_'+str(visar_window_remote[visar1_current_window])+'ns'].get()
    visar2_delay = visar2_dgbox.get() - visar_window_pv['visar2_'+str(visar_window_remote[visar2_current_window])+'ns'].get()

    # get the current windows used in the streak cameras. It reauires the xremote to be running.
    tmp_chr = 'VISAR 1 current streak window configuration:'
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Window length: {} ns.'.format(visar_window_remote[visar1_current_window])
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Timing offset: {:.2f} ns.'.format(1.0e9*visar1_delay)  # convert from s to ns
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ''
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = 'VISAR 2 current streak window configuration:'
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Window length: {} ns.'.format(visar_window_remote[visar2_current_window])
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)
    tmp_chr = ' > Timing offset: {:.2f} ns.'.format(1.0e9*visar2_delay)  # convert from s to ns
    msg = msg + '\n' + tmp_chr
    print(tmp_chr)

    # push the current status to the elog
    if (save == True):
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        mecl.post(msg, run=None, tags=['visar', 'configuration', 'timing'])


def streak_window(visar=1, window=None, offset=0):
    '''
    Description: allows to change the VISAR streak window and/or add an offset to the current visar streak window.
    IN:
        visar   : the number of the visar to consider, 1 and 2.
        window  : set the visar window, in ns, valid entries are 2, 5, 10, 20, 50, 100 and 200. If no window is provided, the current window is used.
        offset  : delay in ns to add to the current window settings.
    OUT:
        push the offset to the DGbox
    '''
    # get the current visar streak window, in ns
    visar1_window_saved = visar_window_remote[visar1_window.get()]
    visar2_window_saved = visar_window_remote[visar2_window.get()]
    # get the current offset
    visar1_offset_saved = visar1_dgbox.get() - visar_window_pv['visar1_' + str(visar1_window_saved)+ 'ns'].get()
    visar2_offset_saved = visar2_dgbox.get() - visar_window_pv['visar2_' + str(visar2_window_saved)+ 'ns'].get()

    if (window is not None):
    # if a number is used, set the window to this value
        key_list = list(visar_window_remote.keys())
        val_list = list(visar_window_remote.values())
        position = val_list.index(window)
        if (visar == 1):
            visar1_window_selected = window
            try:
                daq.disconnect()
                daq.stop()
            except:
                print('If the DAQ is running, failed to put it in "Shutdown" mode. Please do it manually, otherwise ignore.')
            visar1_window.set(key_list[position])
        if (visar == 2):
            visar2_window_selected = window
            try:
                daq.disconnect()
                daq.stop()
            except:
                print('If the DAQ is running, failed to put it in "Shutdown" mode. Please do it manually, otherwise ignore.')
            visar2_window.set(key_list[position])

    if (visar == 1):
        print('VISAR 1 previous configuration:')
        print(' > Window length: {:.2f} ns.'.format(visar1_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(1.0e9*visar1_offset_saved)) # convert from s to ns
        print('')
        if (window is not None):
            channel_val = visar_window_pv['visar1_'+str(visar1_window_selected)+'ns'].get()
        else:
            channel_val = visar_window_pv['visar1_'+str(visar1_window_saved)+'ns'].get()
        channel_val = channel_val + (1.0e-9 * offset)
        visar1_dgbox.set(channel_val)
        print('VISAR 1 new configuration:')
        if (window is not None):
            print(' > Window length: {:.2f} ns.'.format(window))
        else:
            print(' > Window length: {:.2f} ns.'.format(visar1_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(offset)) # convert from s to ns
    if (visar == 2):
        print('VISAR 2 previous configuration:')
        print(' > Window length: {:.2f} ns.'.format(visar2_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(1.0e9*visar2_offset_saved)) # convert from s to ns
        print('')
        if (window is not None):
            channel_val = visar_window_pv['visar2_'+str(visar2_window_selected)+'ns'].get()
        else:
            channel_val = visar_window_pv['visar2_'+str(visar2_window_saved)+'ns'].get()
        channel_val = channel_val + (1.0e-9 * offset)
        visar2_dgbox.set(channel_val)
        print('VISAR 2 new configuration:')
        if (window is not None):
            print(' > Window length: {:.2f} ns.'.format(window))
        else:
            print(' > Window length: {:.2f} ns.'.format(visar2_window_saved))
        print(' > Timing offset: {:.2f} ns.'.format(offset)) # convert from s to ns

def streak_save(visar=1, window=10):
    '''
    Description: use this command to save timing information for the VISAR window into a designated PV value.
    IN:
        visar   : number of the visar, valid values are 1 and 2.
        window  : the window size for which the timing is being added, in ns, valid entries are 2, 5, 10, 20, 50, 100 and 200.
    OUT:
        push the current timing from a DGbox channel to the right PV value.
    '''
    if (visar == 1):
        visar_window_pv['visar' + str(visar) + '_' + str(window) + 'ns'].set(visar1_dgbox.get())
        print('{:.12f} s has been saved for VISAR 1, window {} ns.'.format(visar1_dgbox.get(), window))
    if (visar == 2):
        visar_window_pv['visar' + str(visar) + '_' + str(window) + 'ns'].set(visar2_dgbox.get())
        print('{:.12f} s has been saved for VISAR 2, window {} ns.'.format(visar2_dgbox.get(), window))


def get_image(camera_pv, save = True):
    '''
    extract the image corresponding to a camera and provides an array that can be further manipulated
    '''
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    print('Experiment {}, run {}.'.format(experimentName, RunNumber))
    # get the image from the epics variable. IMAGE1 is for data stream while IMAGE2 is for viewer stream. No difference between both from the config point of view.
    arr = EpicsSignal(camera_pv + ':IMAGE1:ArrayData')
    arr_x = EpicsSignal(camera_pv + ':ArraySizeX_RBV')
    arr_y = EpicsSignal(camera_pv + ':ArraySizeY_RBV')
    # reshape the array from linear to 2D, has to invert the raws and columns to make an actual image
    arr = np.reshape(arr.get(), (arr_y.get(), arr_x.get()))
    plt.imshow(arr)
    return arr


def check_folder():
    '''
    checking the availability of a folder where target pictures and raw data will be saved
    '''
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    RunNumber = get_run_number(hutch='mec', timeout=10)
    try:
        path.exists('/cds/home/opr/mecopr/experiments/' + experimentName + '/target')
    except:
        print('Folder ~mecopr/{}/target already exists.'.format(experimentName))
        os.system('mkdir /cds/home/opr/mecopr/experiments/' + experimentName + '/target')
        print('Created ~mecopr/{}/target folder.'.format(experimentName))


def visar_align():
    '''
    test algorithm for auto alignment or at least checks of alignments
    '''
    # actual image
    #:ArrayData
    # size of the image in X
    #:ArraySizeX_RBV
    # size of the image in Y
    #:ArraySizeY_RBV
    #vis_dat = EpicsSignal('MEC:GIGE:18:IMAGE2:ArrayData')
    vis_dat = EpicsSignal('MEC:STREAK:02:IMAGE1:ArrayData')
    # reshape the array from linear to 2D, has to invert the raws and columns to make an actual image
    #vis_dat2d = np.reshape(vis_dat.get(), (580, 780))
    vis_dat2d = np.reshape(vis_dat.get(), (1024, 1344))
    plt.imshow(vis_dat2d)


# ---   LX35 temp functions   ---
tg_im_x_out_min = 3.0
tg_im_x_out_max = 6.0
tg_im_y_out_min = -35.0
tg_im_y_out_max = -30.0
tg_im_z_out_min = -42.0
tg_im_z_out_max = -40.0

tg_im_x_in_min = 3.0
tg_im_x_in_max = 6.0
tg_im_y_in_min = 45.0
tg_im_y_in_max = 47.0
tg_im_z_in_min = 43.0
tg_im_z_in_max = 45.0

def check_tg_im_in():
    status = False
    if ((tg_im_z_in_min < tg_imaging_z.get()[0] < tg_im_z_in_max) and (tg_im_y_in_min < tg_imaging_y.get()[0] < tg_im_y_in_max) and (tg_im_x_in_min < tg_imaging_x.get()[0] < tg_im_x_in_max)):
        status = True
    return status

def check_tg_im_out():
    status = False
    if ((tg_im_z_out_min < tg_imaging_z.get()[0] < tg_im_z_out_max) and (tg_im_y_out_min < tg_imaging_y.get()[0] < tg_im_y_out_max) and (tg_im_x_out_min < tg_imaging_x.get()[0] < tg_im_x_out_max)):
        status = True
    return status

def imaging_system(position = 'OUT'):
    """
    Check the position of the imaging system before inserting or removing the system
    INPUT:
        position : IN or OUT
    """
    if (position == 'OUT'):
        #if ((tg_imaging_z.get()[0] > 43) and (tg_imaging_z.get()[0] < 45)) and ((tg_imaging_y.get()[0] > 45) and (tg_imaging_y.get()[0] < 47)) and ((tg_imaging_x.get()[0] > 3) and (tg_imaging_x.get()[0] < 6)):
        if (check_tg_im_in() is True):
            print('Current X IN position is {} mm.'.format(tg_imaging_x.get()[0]))
            print('Current Y IN position is {} mm.'.format(tg_imaging_y.get()[0]))
            print('Current Z IN position is {} mm.'.format(tg_imaging_z.get()[0]))
            tg_imaging_z.umvr(-85)
            tg_imaging_y.umvr(-80)
            print('Imaging system is OUT')
        else:
            print('Imaging system is NOT IN, movement not allowed, proceed carefully.')
    if (position == 'IN'):
        #if ((tg_imaging_z.get()[0] > -42) and (tg_imaging_z.get()[0] < -40)) and ((tg_imaging_y.get()[0] > -35) and (tg_imaging_y.get()[0] < -30)) and ((tg_imaging_x.get()[0] > 3) and (tg_imaging_x.get()[0] < 6)):
        if (check_tg_im_out() is True):
            print('Current X OUT position is {} mm.'.format(tg_imaging_x.get()[0]))
            print('Current Y OUT position is {} mm.'.format(tg_imaging_y.get()[0]))
            print('Current Z OUT position is {} mm.'.format(tg_imaging_z.get()[0]))
            tg_imaging_y.umvr(80)
            tg_imaging_z.umvr(85)
            print('Imaging system is IN')
        else:
            print('Imaging system is NOT OUT, movement not allowed, proceed carefully.')

def wire_next_row(n=1):
    """ moves up n spaces, spacing is 7 mm """
    tc_hexapod.y.mv(tc_hexapod.y.get()[2]+(n*7.0))

def wire_next_column(n=1):
    """ moves next n spaces, spacing is 7 mm """
    tgx(tgx()+(n*7.0))

def wire_new_column():
    """ move to 1st position of next column from last position in a column """
    wire_next_column(1)
    wire_next_row(-3)
    print('Starting a new column of wires')


def next_wire():
    if (tgx() < 71.0):
        print('You are not on the target frame, move to Target X > 71')
    elif ((tgx() > 146.5) and (tgx() < 153.5)):
        print('You are about to move to the last column...')
        print('Too close to end switch for automated motion!')
        print('Proceed carefully to Target X = 157.0 (end swith at 157.8)')
        print('and use op.wire_next_row(-3) to move to the 1st row')
    elif (tgx() > 153.5):
        print('You are on the last column...')
        print('Motion not allowed!')
    else:
        if ((tc_hexapod.y.get()[2] > 8.0) and (tc_hexapod.y.get()[2] < 12.4)):
            wire_new_column()
        else:
            wire_next_row()


powermeter_stage=Motor('MEC:USR:MMS:21', name='powermeter_stage')
vacuum_iris=Motor('MEC:USR:MMS:24', name='vacuum_iris')

def pm(position = 'IN', wait_mvt = True):
    if (position == 'IN'):
        powermeter_stage.umv(60)
        print('Power meter is IN')
    if (position == 'OUT'):
        powermeter_stage.umv(120)
        print('Power meter is OUT')

def iris_move(position = 'CLOSE'):
    if (position == 'CLOSE'):
        vacuum_iris.umv(0.74)
        print('Vacuum Iris is CLOSED')
    if (position == 'OPEN'):
        vacuum_iris.umv(-5)
        print('Vacuum Iris is OPEN')

def fw4set(position=6):
    """
    Function to move the filter wheel to a desired value in absolute
    IN:
        position : 6 is OD4, 1 is empty
    """
    cur_pos = fw4pos.get()
    # extract the number of times we will need to move the FW to get in position
    tmp_inc = position - cur_pos
    for i in np.arange(abs(tmp_inc)):
        if (tmp_inc > 0):
            fw4inc.put(1)
        if (tmp_inc < 0):
            fw4dec.put(1)
        time.sleep(2)
    print('Filter Wheel 4 is in position {}.'.format(fw4pos.get()))

def spl_focus_alignment():
    """
    Procedure to check the laser spot size.
    """
    pm('IN')
    spl_mode('alignment')
    gaia_timing_offset(0)
    x.start_seq(5)
    print('You can BEGIN RUNNING the DAQ')
    print('Check if RP attenuators are OUT')
    input("Press Enter to continue...")
    spl_slicer_evr_btn.put(1)
    print('Align FF_NF on opal 1 --> cross (768,256)')
    input("Press Enter when aligned...")
    gaia_detune()
    spl_slicer_evr_btn.put(0)
    iris_move('OPEN')
    pin()
    print('Waiting 10s for the pin to move IN')
    time.sleep(10)
    tc_hexapod.y.mv(tc_hexapod.y.get()[2]-3.0)
    fw4set(position = 6)
    imaging_system('IN')
    print('Ready to send the focused beam')
    print('opal 5 --> cross (1168,876)')
    input("Press Enter to continue...")
    pm('OUT')
    spl_slicer_evr_btn.put(1)

def spl_target_alignment():
    """
    Alignment procedure for a target or to back illuminate a pin.
    """
    spl_slicer_evr_btn.put(0)
    print('SPL slicer trigger DISABLE')
    pm('IN')
    iris_move('CLOSE')
    gaia_timing_offset(0)
    spl_mode('alignment')
    x.start_seq(5)
    print('You can BEGIN RUNNING the DAQ')
    fw4set(position = 1)
    imaging_system('IN')
    pm('OUT')
    print('You can start aligning a new target using op.next_wire().')

def spl_shot_readiness():
    """
    Getting ready for a shot on target.
    """
    spl_slicer_evr_btn.put(0)
    print('SPL slicer trigger DISABLE')
    pm('IN')
    imaging_system('OUT')
    if (check_tg_im_out() is False):
        print('IMAGING SYSTEM NOT OUT ... DO NOT SHOOT')
    elif (check_tg_im_out() is True):
        fw4set(position = 6)
        spl_mode('single_shot')
        evt_seq_btn.put('Stop')
        iris_move('OPEN')
        pm('OUT')
        print('You can proceed with a shot on target after the announcement:')
        print('"WE ARE READY FOR A SHOT ON TARGET"')
        print('"ARE ALL DIAGNOSTICS READY FOR TRIGGER?"')


def uxi_shot(save_run=True, target_out_dark=10, target_out_white=10, target_in_white=10, post_dark=5, offset = 0.5, lpl_ener_val=1.0, timing_val=0.0e-9, arms_val='all'):
    '''
    Description:
        Creates a complexe sequence of dark/white fields with and without the target when using the UXI detectors.
    IN:
        save_run            : True if run is to be saved. Default is True.
        target_out_dark     : number of dark images with target OUT. Default is 10.
        target_out_white    : number of white field images with target OUT. Default is 10.
        target_in_white     : number of white field images with target IN. Default is 10.
        post_dark           : number of dark images after the driven shot. Default is 5.
        lpl_ener_val        : LPL total energy output. Default 1.0 (full energy).
        timing_val          : delay between the LPL and the FEL. Default is 0.0e-9 s.
        arms_val            : laser arms to shoot. Default is 'all'.
        offset              : offset in mm to move the sample from its current position. Default is -0.5mm on hexapod Z.
    OUT:
        Runs the complex sequence, saving 4 runs, one with dark and white and target out, then white with target in, driven shot and dark after shot.
    '''
    # target OUT
    logger.critical('Moving target OUT for {} dark and {} white fields.'.format(target_out_dark, target_out_white))
    target_save()
    tc_hexapod.z.umvr(offset)
    ref_only(xray_trans=1, xray_num=target_out_white, shutters=False, dark=target_out_dark, daq_end=True, calibrant='', rate=0.5, visar=True, save=save_run, slow_cam=False)
    # target IN
    logger.success('Moving target IN for {} white fields.'.format(target_in_white))
    target_return()
    ref_only(xray_trans=1, xray_num=target_in_white, shutters=False, dark=0, daq_end=True, calibrant='', rate=0.5, visar=True, save=save_run, slow_cam=False)
    # take the driven shot
    logger.success('Preparing for laser driven shot at {} % of the laser energy and {} ns delay with the FEL.'.format(lpl_ener_val*100., timing_val*1.0e9))
    optical_shot(shutter_close=[1, 2, 3, 4, 5, 6], lpl_ener=lpl_ener_val, timing=timing_val, xray_threshold=0.1, xray_trans=1, prex=0, save=save_run, daq_end=True, msg='', ps_opt=True, arms=arms_val, tags_words=['optical', 'sample'], uxi=True, auto_trig=True, auto_charge=True, visar=True, slow_cam=False, debug=True)
    # post X-ray only
    logger.success('Target post shot for {} dark fields.'.format(post_dark))
    ref_only(xray_trans=1, xray_num=0, shutters=False, dark=post_dark, daq_end=True, calibrant='', rate=1, visar=True, save=save_run, slow_cam=False)

def digitizer_plot(xmin=0, xmax=32000):
    '''
    Range to zoom:
        xmin = 5400
        xmax = 6400
    '''
    fig, ax = plt.subplots()
    ax.plot(dg1_wvfm.get(), label='Time Tool', color='Green')
    ax.plot(dg0_wvfm.get(), label='Upstream TCC', color='Blue')
    ax.set_xlabel('Samples (#)')
    ax.set_ylabel('Voltage (V)')
    ax.set_xlim(xmin, xmax)
#    ax.xaxis.set_major_locator(MultipleLocator(50))
#    ax.xaxis.set_minor_locator(MultipleLocator(10))
#    ax.yaxis.set_major_locator(MultipleLocator(0.1))
#    ax.yaxis.set_minor_locator(MultipleLocator(0.01))
#    plt.grid(True)
    plt.legend(loc = 'upper right')
    plt.tight_layout()
    plt.show()

#def att_uxi():
#    '''
#    '''
#    if (att_trans.position )

###########################################################################################################
####################################### phi and chi for goniometer ########################################
###########################################################################################################

import numpy as np
import scipy.spatial.transform




def relative_phi_scan(du, dv, dw, min_phi, max_phi, steps):
    ''' creates a phi scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in radians (floats)
        min_phi, max_phi: minimum and maximum of the phi scan in degrees (floats)
        steps: number of steps (integer)
    return:
        uvw_array: a (n,3) matrix of u,v,w positions in the scan (degrees)
        phi_array: a (n) matrix of phi values (degrees)
    '''
    du = du*np.pi/180
    dv = dv*np.pi/180
    dw = dw*np.pi/180
    min_phi = min_phi*np.pi/180
    max_phi = max_phi*np.pi/180
    # 3D rotational matrix
    phi_array = np.linspace(min_phi, max_phi, steps)

    out = np.empty((len(phi_array),3))

    for i, phi in enumerate(phi_array):
        # initialize identity matrix
        matrix = np.eye(3)
        # rotate theta = phi = v # sample mount
        theta = 43.065/2
        sample_mount = (90-theta)*np.pi/180
        rot_theta = np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount))))
        matrix = np.dot(rot_theta, matrix)
        # rotate the matrix phi = v
        rot_phi = np.array(((np.cos(phi),0,np.sin(phi)),
                 (0,1,0),
                 (-np.sin(phi),0,np.cos(phi))))
        matrix = np.dot(rot_phi,matrix)
        # rotate theta = phi = v # sample mount
        rot_theta = np.linalg.inv(np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount)))))
        matrix = np.dot(rot_theta, matrix)
        # rotate the matrix du
        rot_u = np.array(((1,0,0),
                         (0,np.cos(du),-np.sin(du)),
                         (0,np.sin(du),np.cos(du))))
        matrix = np.dot(rot_u,matrix)
        # rotate the matrix dv
        rot_v = np.array(((np.cos(dv),0,np.sin(dv)),
                 (0,1,0),
                 (-np.sin(dv),0,np.cos(dv))))
        matrix = np.dot(rot_v,matrix)
        # rotate the matrix dw
        rot_w = np.array(((np.cos(dw),-np.sin(dw),0),
                         (np.sin(dw),np.cos(dw),0),
                         (0,0,1)))
        matrix = np.dot(rot_w,matrix)
        # get back euler angles
        rotation = scipy.spatial.transform.Rotation.from_matrix(matrix)
        uvw = rotation.as_euler('xyz', degrees = True)
        out[i,:] = uvw
    return out, phi_array*180/np.pi


def relative_chi_scan(du, dv, dw, min_chi, max_chi, steps):
    ''' creates a chi scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in degrees (floats)
        min_chi, max_chi: minimum and maximum of the chi scan in degrees (floats)
        steps: number of steps (integer)
    return:
        uvw_array: a (n,3) matrix of u,v,w positions in the scan (degrees)
        chi_array: a (n) matrix of chi values (degrees)
    '''
    du = du*np.pi/180
    dv = dv*np.pi/180
    dw = dw*np.pi/180
    min_chi = min_chi*np.pi/180
    max_chi = max_chi*np.pi/180
    # 3D rotational matrix
    chi_array = np.linspace(min_chi, max_chi, steps)

    out = np.empty((len(chi_array),3))

    for i, chi in enumerate(chi_array):
        # initialize identity matrix
        matrix = np.eye(3)
        # rotate theta = phi = v # sample mount
        theta = 43.065/2
        sample_mount = (90-theta)*np.pi/180
        rot_theta = np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount))))
        matrix = np.dot(rot_theta, matrix)
        # rotate the matrix chi
        rot_chi = np.array(((1,0,0),
                         (0,np.cos(chi),-np.sin(chi)),
                         (0,np.sin(chi),np.cos(chi))))

        matrix = np.dot(rot_chi,matrix)
        # rotate theta = phi = v # sample mount
        rot_theta = np.linalg.inv(np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount)))))
        matrix = np.dot(rot_theta, matrix)

        # rotate the matrix du
        rot_u = np.array(((1,0,0),
                         (0,np.cos(du),-np.sin(du)),
                         (0,np.sin(du),np.cos(du))))
        matrix = np.dot(rot_u,matrix)
        # rotate the matrix dv
        rot_v = np.array(((np.cos(dv),0,np.sin(dv)),
                 (0,1,0),
                 (-np.sin(dv),0,np.cos(dv))))
        matrix = np.dot(rot_v,matrix)
        # rotate the matrix dw
        rot_w = np.array(((np.cos(dw),-np.sin(dw),0),
                         (np.sin(dw),np.cos(dw),0),
                         (0,0,1)))
        matrix = np.dot(rot_w,matrix)
        # get back euler angles
        rotation = scipy.spatial.transform.Rotation.from_matrix(matrix)
        uvw = rotation.as_euler('xyz', degrees = True)
        out[i,:] = uvw
    return out, chi_array*180/np.pi



def relative_omega_scan(du, dv, dw, min_omega, max_omega, steps):
    ''' creates a omega scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in degrees (floats)
        min_omega, max_omega: minimum and maximum of the omega scan in degrees (floats)
        steps: number of steps (integer)
    return:
        uvw_array: a (n,3) matrix of u,v,w positions in the scan (degrees)
        omega_array: a (n) matrix of omega values (degrees)
    '''
    du = du*np.pi/180
    dv = dv*np.pi/180
    dw = dw*np.pi/180
    min_omega = min_omega*np.pi/180
    max_omega = max_omega*np.pi/180
    # 3D rotational matrix
    omega_array = np.linspace(min_omega, max_omega, steps)

    out = np.empty((len(omega_array),3))

    for i, omega in enumerate(omega_array):
        # initialize identity matrix
        matrix = np.eye(3)
        # rotate theta = phi = v # sample mount
        theta = 43.065/2
        sample_mount = (90-theta)*np.pi/180
        rot_theta = np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount))))
        matrix = np.dot(rot_theta, matrix)
        # rotate the matrix omega
        rot_omega = np.array(((np.cos(omega),-np.sin(omega),0),
                         (np.sin(omega),np.cos(omega),0),
                         (0,0,1)))
        matrix = np.dot(rot_omega,matrix)

        # rotate theta = phi = v # sample mount
        rot_theta = np.linalg.inv(np.array(((np.cos(sample_mount),0,np.sin(sample_mount)),
                 (0,1,0),
                 (-np.sin(sample_mount),0,np.cos(sample_mount)))))
        matrix = np.dot(rot_theta, matrix)

        # rotate the matrix du
        rot_u = np.array(((1,0,0),
                         (0,np.cos(du),-np.sin(du)),
                         (0,np.sin(du),np.cos(du))))
        matrix = np.dot(rot_u,matrix)
        # rotate the matrix dv
        rot_v = np.array(((np.cos(dv),0,np.sin(dv)),
                 (0,1,0),
                 (-np.sin(dv),0,np.cos(dv))))
        matrix = np.dot(rot_v,matrix)
        # rotate the matrix dw
        rot_w = np.array(((np.cos(dw),-np.sin(dw),0),
                         (np.sin(dw),np.cos(dw),0),
                         (0,0,1)))
        matrix = np.dot(rot_w,matrix)
        # get back euler angles
        rotation = scipy.spatial.transform.Rotation.from_matrix(matrix)
        uvw = rotation.as_euler('xyz', degrees = True)
        out[i,:] = uvw
    return out, omega_array*180/np.pi


def move_to_uvw(u,v,w):
    tc_hexapod.u.umv(u) # op.tc_hexapod.u.mv() to not wait...
    tc_hexapod.v.umv(v)
    tc_hexapod.w.umv(w)
    check_hexpod_u(u)
    check_hexpod_v(v)
    check_hexpod_w(w)

def get_uvw_from_phi(du,dv,dw, phi, move = True):
    uvw_array, _ = relative_phi_scan(du, dv, dw, phi, phi, 2)
    if move:
        move_to_uvw(*uvw_array[0])
    return uvw_array[0]

def get_uvw_from_chi(du,dv,dw, chi, move = True):
    uvw_array, _ = relative_chi_scan(du, dv, dw, chi, chi, 2)
    if move:
        move_to_uvw(*uvw_array[0])
    return uvw_array[0]

def get_uvw_from_omega(du,dv,dw, omega, move = True):
    uvw_array, _ = relative_omega_scan(du, dv, dw, omega, omega, 2)
    if move:
        move_to_uvw(*uvw_array[0])
    return uvw_array[0]

##################### do scans ########################
movement_error_threshold = 0.01
angle_error_threshold = 0.01

def eprint(s):
    print('###################################################\n'+s+'###################################################\n')

def check_hexpod_x(x):
    got = tc_hexapod.x.get()[2]
    if abs(got-x) > movement_error_threshold:
        eprint(f'Requested movement to x = {x}, but actual position is x = {got}')

def check_hexpod_y(y):
    got = tc_hexapod.y.get()[2]
    if abs(got-y) > movement_error_threshold:
        eprint(f'Requested movement to y = {y}, but actual position is y = {got}')

def check_hexpod_z(z):
    got = tc_hexapod.z.get()[2]
    if abs(got-z) > movement_error_threshold:
        eprint(f'Requested movement to z = {z}, but actual position is z = {got}')

def check_hexpod_u(u):
    got = tc_hexapod.u.get()[2]
    if abs(got-u) > movement_error_threshold:
        eprint(f'Requested rotation to u = {u}, but actual position is u = {got}')

def check_hexpod_v(v):
    got = tc_hexapod.v.get()[2]
    if abs(got-v) > movement_error_threshold:
        eprint(f'Requested rotation to v = {v}, but actual position is v = {got}')

def check_hexpod_w(w):
    got = tc_hexapod.w.get()[2]
    if abs(got-w) > movement_error_threshold:
        eprint(f'Requested rotation to w = {w}, but actual position is w = {got}')

def cycle_u(u = 0, n = 100, amplitude = 1.0, sleep_time = 1):
    for i in range(n):
        tc_hexapod.u.umv(u+amplitude)
        tc_hexapod.u.umv(u)
        time.sleep(sleep_time)

def cycle_v(v = 0, n = 100, amplitude = 1.0, sleep_time = 1):
    for i in range(n):
        tc_hexapod.v.umv(v+amplitude)
        tc_hexapod.v.umv(v)
        time.sleep(sleep_time)

def cycle_w(w = 0, n = 100, amplitude = 1.0, sleep_time = 1):
    for i in range(n):
        tc_hexapod.w.umv(w+amplitude)
        tc_hexapod.w.umv(w)
        time.sleep(sleep_time)

def do_phi_scan(du, dv, dw, min_phi, max_phi, steps, sleep_time):
    ''' performs a phi scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in degrees (floats)
        max_phi, max_phi: minimum and maximum of the phi scan in degrees (floats)
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    uvw_array, phi_array = relative_phi_scan(du, dv, dw, min_phi, max_phi, steps)

    epics_du.put(float(du))
    epics_dv.put(float(dv))
    epics_dw.put(float(dw))
    epics_sleep_time.put(float(sleep_time))

    for uvw, phi in zip(uvw_array, phi_array):
        tc_hexapod.u.umv(uvw[0]) # op.tc_hexapod.u.mv() to not wait...
        tc_hexapod.v.umv(uvw[1])
        tc_hexapod.w.umv(uvw[2])
        check_hexpod_u(uvw[0])
        check_hexpod_v(uvw[1])
        check_hexpod_w(uvw[2])
        epics_phi.put(float(phi))
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        print(f'phi = {phi:.3f}')
        time.sleep(sleep_time)

def do_chi_scan(du, dv, dw, min_chi, max_chi, steps, sleep_time):
    ''' performs a chi scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in degrees (floats)
        min_chi, max_chi: minimum and maximum of the chi scan in degrees (floats)
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    uvw_array, chi_array = relative_chi_scan(du, dv, dw, min_chi, max_chi, steps)

    epics_du.put(float(du))
    epics_dv.put(float(dv))
    epics_dw.put(float(dw))
    epics_sleep_time.put(float(sleep_time))

    for uvw, chi in zip(uvw_array, chi_array):
        tc_hexapod.u.umv(uvw[0]) # op.tc_hexapod.u.mv() to not wait...
        tc_hexapod.v.umv(uvw[1])
        tc_hexapod.w.umv(uvw[2])
        check_hexpod_u(uvw[0])
        check_hexpod_v(uvw[1])
        check_hexpod_w(uvw[2])
        epics_chi.put(float(chi))
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        print(f'chi = {chi:.3f}')
        time.sleep(sleep_time)

def do_omega_scan(du, dv, dw, min_omega, max_omega, steps, sleep_time):
    ''' performs a omega scan centered around du, dv, and dw
    input:
        du, dv, dw: euler angles of goniometer in degrees (floats)
        min_omega, max_omega: minimum and maximum of the omega scan in degrees (floats)
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    uvw_array, omega_array = relative_omega_scan(du, dv, dw, min_omega, max_omega, steps)

    epics_du.put(float(du))
    epics_dv.put(float(dv))
    epics_dw.put(float(dw))
    epics_sleep_time.put(float(sleep_time))

    for uvw, omega in zip(uvw_array, omega_array):
        tc_hexapod.u.umv(uvw[0]) # op.tc_hexapod.u.mv() to not wait...
        tc_hexapod.v.umv(uvw[1])
        tc_hexapod.w.umv(uvw[2])
        check_hexpod_u(uvw[0])
        check_hexpod_v(uvw[1])
        check_hexpod_w(uvw[2])
        epics_omega.put(float(omega))
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        print(f'omega = {omega:.3f}')
        time.sleep(sleep_time)



def do_x_scan(min_x, max_x, steps, sleep_time):
    ''' performs a x scan
    input:
        min_x, max_x: min and max x
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    epics_sleep_time.put(float(sleep_time))
    x_array = np.linspace(min_x, max_x, steps)
    for x in x_array:
        tc_hexapod.x.umv(x) # op.tc_hexapod.u.mv() to not wait...
        check_hexpod_x(x)
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        time.sleep(sleep_time)

def do_y_scan(min_y, max_y, steps, sleep_time):
    ''' performs a y scan
    input:
        min_y, max_y: min and max y
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    epics_sleep_time.put(float(sleep_time))
    y_array = np.linspace(min_y, max_y, steps)
    for y in y_array:
        tc_hexapod.y.umv(y) # op.tc_hexapod.u.mv() to not wait...
        check_hexpod_y(y)
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        time.sleep(sleep_time)

def do_z_scan(min_z, max_z, steps, sleep_time):
    ''' performs a z scan
    input:
        min_z, max_z: min and max z
        steps: number of steps (integer)
        sleep_time: time to sleep at each step
    return:
        None
    '''
    epics_sleep_time.put(float(sleep_time))
    z_array = np.linspace(min_z, max_z, steps)
    for z in z_array:
        tc_hexapod.z.umv(z) # op.tc_hexapod.u.mv() to not wait...
        check_hexpod_z(z)
        print(f'sleep {sleep_time:.3f}, x = {tc_hexapod.x.get()[2]:.3f}, y = {tc_hexapod.y.get()[2]:.3f}, z = {tc_hexapod.z.get()[2]:.3f}, u = {tc_hexapod.u.get()[2]:.3f}, v = {tc_hexapod.v.get()[2]:.3f}, w = {tc_hexapod.w.get()[2]:.3f}')
        time.sleep(sleep_time)
