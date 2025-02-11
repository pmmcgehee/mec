import time
import numpy as np
# used to color the output text
from colorama import init, Fore, Back, Style
import matplotlib as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)

from datetime import datetime
import matplotlib.pyplot as plt
import meclas
#from mec.laser import NanoSecondLaser
import logging
from functools import partial

#import elog
#import pickle
from mecps import *
from pcdsdevices.epics_motor import Motor
from pcdsdevices.slits import JJSlits 
# for mouse trap functions
import tkinter
from tkinter import messagebox

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
from ophyd.utils.epics_pvs import AlarmSeverity

# force color rest at the end of any print statement
init(autoreset = True)

# logging declaration copy/paste from the utils.py file in hutch-python. Will add new definition though
SUCCESS_LEVEL = 35
logging.addLevelName('SUCCESS', SUCCESS_LEVEL)
logger = logging.getLogger(__name__)
logger.success = partial(logger.log, SUCCESS_LEVEL)


#thz_motor = Motor('MEC:USR:MMS:17', name='thz_motor')
#spl_motor = Motor('MEC:USR:MMS:17', name='spl_motor')
ref_y = Motor('MEC:XT1:MMS:01', name='ref_y')
tgx=Motor('MEC:USR:MMS:17', name='tgx')
hexx=EpicsSignal('MEC:HEX:01:Xpr')
hexy=EpicsSignal('MEC:HEX:01:Ypr')
hexz=EpicsSignal('MEC:HEX:01:Zpr')
s500mm=EpicsSignal('MEC:PPL:MMN:20')
tgy=EpicsSignal('MEC:PPL:MMN:07')
tgy_rbv=EpicsSignal('MEC:PPL:MMN:07.RBV')
tgz=EpicsSignal('MEC:PPL:MMN:08')
tgz_rbv=EpicsSignal('MEC:PPL:MMN:08.RBV')

# RP energylimiter
rpel_in = EpicsSignal('MEC:RIS:SAT:01:IN_LS_A')
rpel_out = EpicsSignal('MEC:RIS:SAT:01:OUT_LS_A')
rpel_button = EpicsSignal("MEC:USR:DOUT8")

#MXI axis
mxi_x = EpicsSignal("MEC:HEX:02:Xpr")
mxi_y = EpicsSignal("MEC:HEX:02:Ypr")
mxi_z = EpicsSignal("MEC:HEX:02:Zpr")

# X493 attenuator motor definition
att_trans=Motor('MEC:USR:MMS:20', name='att_trans')
att_rot=EpicsSignal('MEC:PPL:MMN:20')

# GUI fix for attenuator
clear_att = EpicsSignal("MEC:ATT:COM:STATUS")
all_att_out = EpicsSignal("MEC:ATT:COM:GO")

tg_imaging_x=Motor('MEC:PPL:MMN:16', name='tg_imaging_x')
tg_imaging_y=Motor('MEC:PPL:MMN:22', name='tg_imaging_y')
tg_imaging_z=Motor('MEC:TC1:MMS:22', name='tg_imaging_z')

#delay_line=Motor('MEC:USR:MMS:25', name='delay_line')
be_lens_stack=EpicsSignal("MEC:XT2:XFLS.VAL")

# GMD PV values for the FEL pulse energy
gmd_241 = EpicsSignal('GDET:FEE1:361:ENRC')
gmd_242 = EpicsSignal('GDET:FEE1:361:ENRC')
gmd_361 = EpicsSignal('GDET:FEE1:361:ENRC')
gmd_362 = EpicsSignal('GDET:FEE1:361:ENRC')
#gmd_241 = EpicsSignal('GDET:FEE1:242:ENRC')
#gmd_242 = EpicsSignal('GDET:FEE1:242:ENRC')
#gmd_361 = EpicsSignal('GDET:FEE1:242:ENRC')
#gmd_362 = EpicsSignal('GDET:FEE1:242:ENRC')

# beckhoff input
beckhoff_ch9 = EpicsSignal('MEC:USR:AIN:9')

# Be lens vertical readback value
be_y = EpicsSignal('MEC:XT2:MMS:15.RBV')
be_y_preset1 = EpicsSignal('MEC:XT2:XFLS:PACK1_SET')
be_y_preset2 = EpicsSignal('MEC:XT2:XFLS:PACK2_SET')
be_y_preset3 = EpicsSignal('MEC:XT2:XFLS:PACK3_SET')

# spl timing
spl_vitara = EpicsSignal('LAS:FS6:VIT:FS_TGT_TIME')
spl_vitara_pv = EpicsSignal('MEC:NOTE:LAS:FST0')
spl_locking = EpicsSignal('LAS:FS6:VIT:PHASE_LOCKED')

# laser uniblitz
# old location
#spl_uniblitz_evr_code = EpicsSignal('EVR:MEC:USR01:TRIG5:TEC')
#spl_uniblitz_evr_btn = EpicsSignal('EVR:MEC:USR01:TRIG5:TCTL')
#spl_uniblitz_evr_code = EpicsSignal('MEC:LAS:EVR:01:TRIG0:TEC')
#spl_uniblitz_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG0:TCTL')
spl_uniblitz_evr_code = EpicsSignal('MEC:LAS:EVR:01:TRIG4:TEC')
spl_uniblitz_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG4:TCTL')
# 0: negative
# 1: positive
spl_uniblitz_6mm = EpicsSignal('MEC:LAS:DDG:08:cdOutputPolarityBO')
spl_uniblitz_65mm = EpicsSignal('MEC:LAS:DDG:08:abOutputPolarityBO')
# 2: AB
# 3: AB, CD
spl_uniblitz_inh = EpicsSignal('MEC:LAS:DDG:08:triggerInhibitMO')

# GAIA dgbox channel to change the timing
gaia_dgbox = EpicsSignal('MEC:LAS:DDG:06:cDelayAO')

# PV used for checking back reflection issue with the mouse trap diag
back_ref = EpicsSignal("MEC:GIGE:16:Stats1:Total_RBV")

# filter wheel PVs
fw3inc = EpicsSignal('MEC:LAS:FW:03:IncPos.PROC')
fw3dec = EpicsSignal('MEC:LAS:FW:03:DecPos.PROC')
fw3pos = EpicsSignal('MEC:LAS:FW:03:Position')

fw4inc = EpicsSignal('MEC:TC:FW:05:IncPos.PROC')
fw4dec = EpicsSignal('MEC:TC:FW:05:DecPos.PROC')
fw4pos = EpicsSignal('MEC:TC:FW:05:Position')

fw_vac_mot = Motor('MEC:USR:MMS:26', name = 'fw_vac_mot')
fw_vac_mot.tolerated_alarm = AlarmSeverity.MINOR

fw_pv = dict(
        position = [
            EpicsSignal('MEC:LAS:FW:01:Position'),
            EpicsSignal('MEC:LAS:FW:02:Position'),
            EpicsSignal('MEC:LAS:FW:03:Position'),
            EpicsSignal('MEC:TC:FW:05:Position')
            ],
        increase = [
            EpicsSignal('MEC:LAS:FW:01:IncPos.PROC'),
            EpicsSignal('MEC:LAS:FW:02:IncPos.PROC'),
            EpicsSignal('MEC:LAS:FW:03:IncPos.PROC'),
            EpicsSignal('MEC:TC:FW:05:IncPos.PROC')
            ],
        decrease = [
            EpicsSignal('MEC:LAS:FW:01:DecPos.PROC'),
            EpicsSignal('MEC:LAS:FW:02:DecPos.PROC'),
            EpicsSignal('MEC:LAS:FW:03:DecPos.PROC'),
            EpicsSignal('MEC:TC:FW:05:DecPos.PROC')
            ]
        )

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

yag90hx=EpicsSignal('MEC:NOTE:DOUBLE:09')
yag90hy=EpicsSignal('MEC:NOTE:DOUBLE:10')
yag90hz=EpicsSignal('MEC:NOTE:DOUBLE:11')
yag90tgx=EpicsSignal('MEC:NOTE:DOUBLE:12')

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

siemenshx=EpicsSignal('MEC:NOTE:DOUBLE:17')
siemenshy=EpicsSignal('MEC:NOTE:DOUBLE:18')
siemenshz=EpicsSignal('MEC:NOTE:DOUBLE:19')
siemenstgx=EpicsSignal('MEC:NOTE:DOUBLE:20')


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
spl_slicer_evr_code = EpicsSignal('MEC:LAS:EVR:01:TRIG3:TEC')
spl_slicer_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG3:TCTL')

# getting EVR button status for the LPL slicer and lamps
lpl_slicer_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG8:TCTL')
lpl_slicer_evr_code = EpicsSignal('MEC:LAS:EVR:01:TRIG8:TEC')
lpl_lamps_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG7:TCTL')

# getting charging status from the PFN GUI
lpl_charge_status=EpicsSignal('MEC:PFN:CHARGE_OK')
lpl_charge_btn=EpicsSignal('MEC:PFN:START_CHARGE')

# getting event code and EVR button status for the VISAR laser and streak cameras
visar_streak_evt_code = EpicsSignal('MEC:LAS:EVR:01:TRIG9:TEC')
visar_streak_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIG9:TCTL')
visar_laser_evt_code = EpicsSignal('MEC:LAS:EVR:01:TRIGA:TEC')
visar_laser_evr_btn = EpicsSignal('MEC:LAS:EVR:01:TRIGA:TCTL')

# temporary settings to check LPL timing using SLAC EVR USR01 channel 1
lpl_tcc_diode_evt_code = EpicsSignal('EVR:MEC:USR01:TRIG1:TEC')
lpl_tcc_diode_delay = EpicsSignal('EVR:MEC:USR01:CTRL.DG1D')

# test solution when the MEC attenuators are stalled (it was added before each SiT commands)
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

# XPP monochromator PV for IN/OUT status
xpp_lodcm = EpicsSignal("XPP:MON:MMS:09.RBV")
xpp_ccm1 = EpicsSignal("XPP:MON:MMS:22.RBV")
xpp_ccm2 = EpicsSignal("XPP:MON:MMS:23.RBV")

# XCS YAG1 PV
xcs_yag1 = EpicsSignal("HXX:UM6:PIM.VAL")

# SPL specific motors
spl_powermeter_stage=Motor('MEC:USR:MMS:21', name='spl_powermeter_stage')
spl_filter_stage=Motor('MEC:USR:MMS:23', name='spl_filter_stage')
# this stage is a VT50 which has errors when motion finishes. Next line remove errors causing motion to crash.
spl_filter_stage.tolerated_alarm = AlarmSeverity.MINOR
vacuum_iris=Motor('MEC:USR:MMS:20', name='vacuum_iris')
imaging_syst=Motor('MEC:PPL:MMN:12', name='imaging_syst')
disp_sens_bs_mot=Motor('MEC:PPL:MMN:25', name='disp_sens_bs_mot')
fsi=Motor('MEC:USR:MMS:25', name='fsi')
fsi.tolerated_alarm = AlarmSeverity.MINOR

###############

# to check the status of a PV
def pv_status(pv = ''):
    '''
        Description: check the detailed status of a PV or set of PVs.
        IN:
            pv: string, PV itself, can use global pattern
        OUT:
            status in tuple    
    '''
    resp = requests.get("http://pscaa01.slac.stanford.edu:17665/mgmt/bpl/getPVStatus?pv=" + pv + "")
    dict_pv = resp.json()
    for pv_val in range(len(dict_pv)):
        # +1 to start coutning from 1 and not 0
        print('PV {}:'.format(pv_val + 1))
        for key in dict_pv[pv_val]:
            print('{:26s} : {}'.format(key, dict_pv[pv_val][key]))
        print('')

# to resume archiving a PV
def pv_resume(pv = ''):
    '''
        Description: check the detailed status of a PV or set of PVs.
        IN:
            pv: string, PV itself, can use global pattern
        OUT:
            status in tuple    
    '''
    resp = requests.get("http://pscaa01.slac.stanford.edu:17665/mgmt/bpl/resumeArchivingPV?pv=" + pv + "")
    pv_status(pv)

# adding PV names to the archiver
#def 
def pv_add(pv = ''):
    '''
        Description: add a PV or set of PVs.
        IN:
            pv: string, PV itself, can use global pattern
        OUT:
            status in tuple    
    '''
    resp = requests.get("http://pscaa01.slac.stanford.edu:17665/mgmt/bpl/archivePV?pv=" + pv + "")
    pv_status(pv)
# nedd to add all the options to register multi varianbles
#http://pscaa01.slac.stanford.edu:17665/mgmt/bpl/changeArchivalParameters?pv=MEC:TC1:GPI:01:PMON&samplingmethod=SCAN&samplingperiod=5


#
# VAREX sequencer methods
#
def varex_test():

    print("Test 1: Creating a test sequence to pass to the event sequencer.")
    print("0 skip, 1 predark, 1 prex, 1 during, 0 postdark")
    print("Using default event positions:")
    print("\tpulse picket at 10 beams")
    print("\tlaser and DAQ at 12 beams")
    print("\tVarex readout at 12 beams")

    x.nsl._config['varex'] = True
    x.nsl._config['varexskip'] = 0
    x.nsl._config['varexpredark'] = 1 
    x.nsl._config['varexprex'] = 1 
    x.nsl._config['varexduring'] =  1
    x.nsl._config['varexpostdark'] = 0 
    print("calling x.nsl._fake_varex_shot()")
    x.nsl._fake_varex_shot()

    print("\nTest 2: Customizing event positions")
    print("pp=8 daqshot=10 varex=12")
    print("1 during")
    x.nsl._varex_seq.set_beampos(pp=8, daqshot=10, varex=12)
    s = x.nsl._varex_seq.seq(nduring=1)
    x.nsl._varex_seq.report_seq()

    print("\nTest 3: Customizing a frame")
    print("Changing a x-ray frame - see Example 3 on Confluence")
    x.nsl._varex_seq.shot_frame = \
    [['longpulse',12,0],['daqreadout',12,0],['varexreadout',12,0]]
    s = x.nsl._varex_seq.seq(nduring=1)
    x.nsl._varex_seq.report_seq()

#jj slit usage example:
#    width = gap
#    center = offset

#mec_jj_1.xwidth.get()
#mec_jj_1.xcenter.get()

#mec_jj_1.xwidth.put(2)
#mec_jj_1.xcenter.put(2)
#
#mec_jj_1.ywidth.get()
#mec_jj_1.ycenter.get()

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

def jj_slits(size=1):
    '''
        size = opening in mm
    '''
    mec_jj_1.xwidth.umvr(size)
    mec_jj_1.ywidth.umvr(size)

# event sequencer control
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

def lpl_check_timing(rate='10Hz'):
    '''
    Description: set the EVR settings of the photodiode at TCC to check the 10Hz signal (LPL and/or X-rays) or be ready for the single shot and check the arrival time is consistant with expectations.
    IN:
        rate: '10Hz' or 'single' (for single shot)
    '''
    if rate == '10Hz':
        lpl_tcc_diode_evt_code.put(43)
        lpl_tcc_diode_delay.put(105315)
        logger.success("TCC diode ready for 10 Hz timing check. Confirm the scope is set to 10 mV/div.")
    if rate == 'single':
        lpl_tcc_diode_evt_code.put(182)
        lpl_tcc_diode_delay.put(106267)
        logger.success("TCC diode ready for single shot timing check. Don't forget to set the scope to 1V/div.")

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

def fireset_input_state():
    '''
    Description: Get the voltage from channel 9 of the beckhoff.
    IN:
        NONE
    OUT:
        float in V
    '''
    return beckhoff_ch9.get()

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
    time.sleep(1)
    if (visar_streak_evr_btn.get() == 0):
        visar_streak_evr_btn.put(1)
        print('Streak button status')
        print('       Read Access is {}.'.format(visar_streak_evr_btn.read_access))
        print('       Connection Timeout at {}.'.format(visar_streak_evr_btn.connection_timeout))
    time.sleep(1)
    if (visar_laser_evr_btn.get() == 0):
        visar_laser_evr_btn.put(1)
        print('VISAR button status:')
        print('       Read Access is {}.'.format(visar_laser_evr_btn.read_access))
        print('       Connection Timeout at {}.'.format(visar_laser_evr_btn.connection_timeout))
    time.sleep(1)

    if (status == 'move'):
        visar_laser_evr_btn.put(0)

# set the mateiral list used for visar window material
visar_window_spec = dict(lif = 1.393, LiF = 1.393, sio2 = 1.4607, SiO2 = 1.4607, sapp = 1.772, Sapp = 1.772, ptfe = 1.519, PTFE = 1.519)

def visar_window_compensation(material="LiF", thickness=200e-6):
    '''
    Description: script to return the amount to move the visar lens in Z as a function of the material and its thickness.
    IN:
        material : type of material of the window, either LiF, SiO2, Sapphire or PTFE
        thickness: thickness of hte material, in mm
    OUT:
        amount to move the visar Z axis (to do: move the visar axis of the coresponding amount), in mm
    '''
    offset = thickness * ( (visar_window_spec[material] / 1.0 ) - 1.0 )
    return print('Offset is {:.1f} um AWAY from current position.'.format(offset*1e6))

# set the calibrant list used on the MEC calibration cartridge
calibrant_list = ['CeO2', 'ceo2', 'LaB6', 'lab6', 'Ti', 'ti', 'Cu', 'cu', 'Zn', 'zn']

talbotStage = Motor('MEC:PPL:MMN:29', name='talbotStage')
talbotIN = -5.5
talbotOUT = 50.5

# method to take postshot reference Talbot IN/OUT
def post_ref_talbot(nEvent=20, SiT=1.0):
    pulse_picker(1)
    print('Rate is set to 1 Hz because VISAR streak cameras are fickle b**ches.')
    talbotStage.umv(talbotIN)
    ref_only(xray_trans=SiT, rate=1, xray_num=nEvent, visar=True, save=True, calibrant='white-field/Talbot_IN')
    talbotStage.umv(talbotOUT)
    ref_only(xray_trans=SiT, rate=1, xray_num=nEvent, visar=True, save=True, calibrant='white-field/Talbot_OUT')

# method to take preshot reference Talbot OUT/IN
def pre_ref_talbot(nEvent=20, SiT=1.0):
    pulse_picker(1)
    print('Rate is set to 1 Hz because VISAR streak cameras are fickle b**ches.')
    talbotStage.umv(talbotOUT)
    ref_only(xray_trans=SiT, rate=1, xray_num=nEvent, visar=True, save=True, calibrant='cold-sample/Talbot_OUT')
    talbotStage.umv(talbotIN)
    ref_only(xray_trans=SiT, rate=1, xray_num=nEvent, visar=True, save=True, calibrant='cold-sample/Talbot_IN')

def fw(num=1, position=3):
    """
    Description: Function to move a filter wheel to a desired value in absolute
    IN:
        position : 6 is OD4, 1 is empty
    """
    # array starts at 0 but filter wheel numbering starts at 1
    num = num - 1
    cur_pos = fw_pv['position'][num].get()
    # extract the number of times we will need to move the FW to get in position
    tmp_inc = position - cur_pos
    for i in np.arange(abs(tmp_inc)):
        if (tmp_inc > 0):
            fw_pv['increase'][num].put(1)
        if (tmp_inc < 0):
            fw_pv['decrease'][num].put(1)
        time.sleep(3)
    logger.success('Filter Wheel {0:} is in position {1:}.'.format(num+1, fw_pv['position'][num].get()))

def lpl_check_front_alignment():
    '''
    Description: provides a simple command which set the system in a mode to check the alignment of hte drive lasers in the front of the target with the LPL beam. This techniaue ensure consistant and accurate alignment of the beams to TCC.
    IN:
        NA
    OUT:
        System in a state ready for checking the LPL alignment at the front of the sample
    '''
    if (lpl_slicer_evr_btn.get() == 1):
        lpl_slicer_evr_btn.put(0)
    HWPon('all', set_T = 0.0)
    logger.warning('Setting HWP to 45 degree...')
    logger.warning('Waiting 15 seconds until complete...')
    time.sleep(15)
    logger.success('LPL energy set to 0.')
    fw(num=1, position=2)
    logger.success('No filter in front of Questar 1.')
    fw(num=2, position=4)
    logger.success('No filter in front of Questar 2.')
    # force trig the 43 ns slicer
    lpl_slicer_evr_code.put(43)
    if (lpl_slicer_evr_btn.get() == 0):
        lpl_slicer_evr_btn.put(1)
    time.sleep(2)
    logger.warning('NS slicer set to 10 Hz and enabled.')   
    logger.success('You can check the allignment by moving hex X axis.')   



def spl_check_front_alignment():
    '''
    Description: provides a simple command which set the system in a mode to check the alignment of the SPL lasers in the front of the target. This technique ensures consistant and accurate alignment of the beams to TCC.
    IN:
        NA
    OUT:
        System in a state ready for checking the SPL alignment at the front of the sample
    '''
    # force no light on target
    spl_slicer_evr_btn.put(0)
    logger.success('SPL slicer trigger DISABLE')
    vacuum_iris.umv(0.1)
    gaia_detune()
    spl_mode(mode='alignment')
    logger.warning('Vacuum Iris is not entirely CLOSED')
    spl_slicer_evr_code.put(44)
    time.sleep(0.2)
    #if (spl_slicer_evr_btn.get() == 0):
    #    spl_slicer_evr_btn.put(1)
    logger.success('SPL slicer trigger button is Enabled.')
    # check that the energy limiter is out, put it out if not
    if (rpel_in.get() == 1  and rpel_out.get() == 0):
        rpel_button.put(1)
        logger.warning('RP Energy Limiter is now OUT.')
    else:
        logger.warning('RP Energy Limiter is already OUT.')
    pm(position='OUT')
    filter(position='OUT')
    logger.success('Confirm Gige 1 at Gain 5 and acq time at 0.5 s.')
    logger.success('You can tweak the hex X value to align on the red cross.')


# method to save multiple xray only shotsi and/or visar references
def ref_only(xray_trans=1, xray_num=10, shutters=False, dark=0, daq_end=True, calibrant='', rate=1, 
        visar=False, save=False, slow_cam=False,
        varex=False,
        varex_skip=0, varex_predark=0, varex_prex=0, varex_postdark=0,
        varex_gain=1, varex_binning=1):
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
        varex           : True to use the VAREX sequencing
        varex_skip     : Number of dark frames, no DAQ readout
        varex_predark     : Number of dark frames, with DAQ readout
        varex_prex        : Number of x-ray only frames
        varex_postdark  : Number of postshot dark frames, with DAQ readout
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
    time.sleep(1)
    if (visar_streak_evr_btn.get() == 1):
        visar_streak_evr_btn.put(0)
    time.sleep(1)
    if (visar_laser_evr_btn.get() == 1):
        visar_laser_evr_btn.put(0)

    # force VISAR to false to make sure triggers are not enabled if rate is greater than 1 Hz
    # it also means it changes the rate of acquisition to 1Hz to match VISAR capabilities only when it is set to 1
    if (rate > 1):
        visar = False
        print('Rate is not 1 Hz, so the VISAR is disabled. You should also remove the VISAR from the DAQ partition to perevent damaged events.')

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
    # addition for talbot commands above: pre_ref_talbot and post_ref_talbot
    elif (calibrant == 'white-field_IN'):
        msg = '{} White Field images Talbot IN at {:.4f}%.'.format(xray_num, 100.0 * xray_trans)
        tags_ref = ['reference', 'white_field']
        calibrant = 'ok'
    elif (calibrant == 'white-field_OUT'):
        msg = '{} White Field images Talbot OUT at {:.4f}%.'.format(xray_num, 100.0 * xray_trans)
        tags_ref = ['reference', 'white_field']
        calibrant = 'ok'
    elif (calibrant == 'cold-sample_IN'):
        msg = '{} x-ray only shots Talbot IN at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_log_target)
        tags_ref = ['reference', 'sample']
        calibrant = 'ok'
    elif (calibrant == 'cold-sample_OUT'):
        msg = '{} x-ray only shots Talbot OUT at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_log_target)
        tags_ref = ['reference', 'sample']
        calibrant = 'ok'

    if (calibrant == 'ok'):
        visar_mode(status='daq')
        print('Visar reference is being saved in the DAQ')
        tags_ref = tags_ref + ['visar']

    # VISAR exception
    if (visar == True and calibrant != 'ok' ):
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
    # Setup for VAREX ref-only sequence
    x.nsl._varex_seq.set_gain(varex_gain)
    x.nsl._varex_seq.set_binning(varex_binning)
    x.nsl._config['varex'] =  varex
    x.nsl._config['varexskip'] =  varex_skip
    x.nsl._config['varexpredark'] =  varex_predark
    x.nsl._config['varexprex'] =  varex_prex
    x.nsl._config['varexduring'] = 0 
    x.nsl._config['varexpostdark'] = varex_postdark 
#    att_update()
    SiT(xray_trans)
    if (daq_end == True):
        p=x.nsl.shot(record=save, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=save, end_run=False)
    RE(p)
    if (save == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        if (varex == True):
            msg = msg + 'Varex in use, ref parameters: skip={} predark={} prex={} postdark={} gain={} binning={}'.format(varex_skip, varex_predark, 
                    varex_prex, varex_postdark, varex_gain, varex_binning)
        mecl.post(msg, run=RunNumber, tags=tags_ref)
    # restore laser rep rate in case the next action does not involve the use of the following scripts (like shots from the hutch)
    x.nsl._config['rate']=10

# method to perform a pump-probe LPL shot
def optical_shot(shutter_close=[1, 2, 3, 4, 5, 6], lpl_ener=1.0, timing=0.0e-9,
        xray_threshold=0.1, xray_trans=1, prex=0, save=True, daq_end=True,
        msg='', ps_opt=True, arms='all', tags_words=['optical', 'sample'],
        uxi=False, auto_trig=False, auto_charge=False, visar=True,
        slow_cam=False, debug=True,
        varex=False,
        varex_skip=0, varex_predark=0, varex_prex=0, varex_during=0,
        varex_postdark=0, varex_gain=1, varex_binning=1):
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
        varex           : True to use the VAREX sequencing
        varex_skip      : Number of preshot dark frames, no DAQ readout
        varex_predark   : Number of preshot dark frames, with DAQ readout
        varex_prex      : Number of preshot x-ray only frames
        varex_during    : Number of x-ray+LPL frames  (0 or 1)
        varex_postdark  : Number of postshot dark frames, with DAQ readout

    OUT:
        execute the plan and post a comment to the elog.
    '''
    # switching to single mode
    lpl_slicer_evr_code.put(182)
    # close 2w WEST & EAST shutters
    TTL_shutter.Toggle("closewwxx")
    logger.success('2w shutters closed during shot setup!')
    # set LPL slicer and lamps to safe trigger mode
    if (auto_trig == True):
          time.sleep(1)
          if (lpl_slicer_evr_btn.get() == 0):
              lpl_slicer_evr_btn.put(1)
          time.sleep(1)
          if (lpl_lamps_evr_btn.get() == 0):
              lpl_lamps_evr_btn.put(1)
          print('NS slicer and Lamps trigger buttons are Enabled.')
    # hide drive from GigE 1 & 2
    fw_pv['decrease'][2-1].put(1)
    # make sure the daq is not connected before starting the command
    x.nsl._config['slowcam'] = slow_cam
    # debugging flags for various subsystems
    if (debug == True):
        # displays the status of the internal shutters of the optical laser to help debugging interaction issues
        print('Start debugging functions ---')
        TTL_shutter.Status(display=True)
        print('End debugging functions ---')
    # force disconnect the DAQ before starting a new sequence
    if (daq.connected == True):
        daq.disconnect()
    x.nsl.configure(x.nsl._config)
    # charging process
    if ((arms == 'all') or (arms == 'ABGH') or (arms == 'EFIJ') or (arms=='AB') or (arms=='ABEF')or(arms=='GHIJ') or (arms=='EF') or (arms=='GH') or (arms=='IJ')):
        PFN.ArmOnly(arms, set_T=lpl_ener)
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
#    att_update()
    SiT(xray_trans)
    # check the trigger status
    if (auto_trig == True):
        time.sleep(1)
        if (lpl_slicer_evr_btn.get() == 0):
            lpl_slicer_evr_btn.put(1)
        time.sleep(1)
        if (lpl_lamps_evr_btn.get() == 0):
            lpl_lamps_evr_btn.put(1)
        print('NS slicer and Lamps trigger buttons are Enabled.')   
    # debugging the button issue
        print('Slicer button status:')
        print('       Read Access is {}.'.format(lpl_slicer_evr_btn.read_access))
        print('       Connection Timeout at {}.'.format(lpl_slicer_evr_btn.connection_timeout))
        print('Lamps button status:')
        print('       Read Access is {}.'.format(lpl_lamps_evr_btn.read_access))
        print('       Connection Timeout at {}.'.format(lpl_lamps_evr_btn.connection_timeout))
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
    # Setup for VAREX sequence
    if (varex == True):
        x.nsl.during = 0 # VAREX sequence sets when the LPL shot occurs
    x.nsl._varex_seq.set_gain(varex_gain)
    x.nsl._varex_seq.set_binning(varex_binning)
    x.nsl._config['varex'] =  varex
    x.nsl._config['varexskip'] =  varex_skip
    x.nsl._config['varexpredark'] =  varex_predark
    x.nsl._config['varexprex'] =  varex_prex
    x.nsl._config['varexduring'] =  varex_during
    x.nsl._config['varexpostdark'] = varex_postdark

    # to set the plan with the new configuration
    if (daq_end == True):
        p=x.nsl.shot(record=save, ps=ps_opt, end_run=True)
    if (daq_end == False):
        p=x.nsl.shot(record=save, ps=ps_opt, end_run=False)
    # loop before the shot to check that FEL pulse energy is above a threshold: if the FEL drops within 10 sec, then we cannot do much with this moethod
    # getting the energy value once to evaluate what to do otherwise might be using a different pulse. Still might be unprecise since this is a BLD value which is refreshed faster than the epics feedback I guess.
    # need to uncomment when we take beam again
    fel_ener = fel_pulse_energy()
    while (fel_ener < xray_threshold):
        time.sleep(1)
        logger.critical('FEL pulse energy too low!')
        logger.critical('waiting to recover or call ACR at x2151...')
        fel_ener = fel_pulse_energy()
    else:
        logger.success('FEL pulse energy is {:.3f} mJ.'.format(fel_ener))
    # reopen 2w WEST & EAST shutters
    TTL_shutter.Toggle("openwwxx")
    logger.success('2w shutters reopened before the shot.')
    # to run the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    RunNumber = get_run_number(hutch='mec', timeout=10)
    mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
    msg = msg + '{} arms, laser shot {}: laser energy is at {:.1f} % from max, delay is {:.2f} ns, SiT at {:.1f} %.'.format(arms, msg_log_target, 100.0 * lpl_ener, 1.0e9 * timing, 100.0 * xray_trans)
    if (varex == True):
        msg = msg + 'Varex in use, shot parameters: skip={} predark={} prex={} during={} postdark={} gain={} binning={}'.format(varex_skip, varex_predark, varex_prex,
        varex_during, varex_postdark, varex_gain, varex_binning)
    mecl.post(msg, run=RunNumber, tags=tags_words)
    # make sure the event sequencer is getting ready for the alignment mode of the VISAR by starting the event sequencer at 1Hz, and no need to touch the trigger as they are ready for this task
    x.start_seq(1)
    # restore the number of prex shots after the driven shot. Could restore the entire default config at some point.
    x.nsl.prex=0
    # Unhide drive from GigE 2
    fw_pv['increase'][2-1].put(1)

def single_shot(debug = True, ps = False, pspostsave = True, auto_trig = True, auto_charge = True, arms = 'all', lpl_ener = 1):
    '''
        Description:
          Fires a single shot checking the event sequencer, the triggers and the charging status without having the DAQ in teh way.
        IN:
            debug       : True, set the TTL shutter status
            ps          : False, for pulse shape optimization routines
            auto_trig   : True, set the triggers automatically for the laser shot
            auto_charge : True, set 
            arms        : all, ABGH, EFIJ are valid
            lpl_ener    : 1 is full energy, 0.5 is 50% of the total expected energy (waveplate set accordingly)
    '''   
    # runs the pre shot optimization routine
    if (ps == True):
        logger.success("Running preshot pulse shaping routine...")
        meclas.LPL.pspreshot()
 
    # stop the sequence to make sure we don't blow up a fuse
    seq.stop()
    # defining the basic LPL event sequencer set of events for 1 shot
    lpl_sequence = [[182, 12, 0, 0]]
    seq.sequence.put_seq(lpl_sequence)

    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    if (debug == True):
        # displays the status of the internal shutters of the optical laser to help debugging interaction issues
        logger.info('Start debugging functions ---')
        TTL_shutter_status(display=True)
        logger.info('End debugging functions ---')

    # check the trigger status
    if (auto_trig == True):
        time.sleep(1)
        if (lpl_slicer_evr_btn.get() == 0):
            lpl_slicer_evr_btn.put(1)
        time.sleep(1)
        if (lpl_lamps_evr_btn.get() == 0):
            lpl_lamps_evr_btn.put(1)
            logger.warning('NS slicer and Lamps trigger buttons are Enabled.')   
    # debugging the button issue
        logger.info('Slicer button status:')
        logger.info('       Read Access is {}.'.format(lpl_slicer_evr_btn.read_access))
        logger.info('       Connection Timeout at {}.'.format(lpl_slicer_evr_btn.connection_timeout))
        logger.info('Lamps button status:')
        logger.info('       Read Access is {}.'.format(lpl_lamps_evr_btn.read_access))
        logger.info('       Connection Timeout at {}.'.format(lpl_lamps_evr_btn.connection_timeout))
    else:
        logger.warning('NS slicer and Lamps trigger buttons are not being checked by the script.')

    # charging process
    if ((arms == 'all') or (arms == 'ABGH') or (arms == 'EFIJ') or (arms=='AB') or (arms=='ABEF')or(arms=='GHIJ') or (arms=='EF') or (arms=='GH') or (arms=='IJ')):
        ARMonly(arms, set_T=lpl_ener)
        time.sleep(5)
        if (auto_charge == True):
            logger.warning("Waiting until charging is authorized ...")
            while lpl_charge_status.get()==0:
               time.sleep(1)
            if (lpl_charge_status.get() == 1):
                lpl_charge_btn.put(1)
                logger.info('Auto charging the laser, waiting 15 sec to be completed...')
                time.sleep(15)
                logger.success('Laser should be charged, check it!')
        else:
            logger.warning('Auto charging is disabled, make sure to press the button on the GUI!')

    # start the shot sequence for a single shot
    logger.warning('Starting single shot laser sequence, please remove hands from the enclosure!!')
    seq.play_mode.put(0)
    seq.start()

    # runs the post shot optimization routine, waiting 5s for the shot to execute (to optimize)
    time.sleep(5)
    if (ps == True):
        logger.success("Running postshot pulse shaping routine...")
        meclas.LPL.pspostshot(save_flag = pspostsave, display = True)

    logger.success('Laser shot sequence complete.')

# set the firing sequence on the event sequencer
firing_sequence = [[168, 118, 0, 0],
                [167, 2, 0, 0],
                [169, 0, 0, 0]]
# method to save multiple xray only shotsi and/or visar references
def firing_seq(xray_trans=1, nshot=1, shutters=False, dark=0, daq_end=True, rate=1, save=False, msg_log_target='', tags_det=['det', 'xray'], slow_cam=False):
    '''
    Description: script to take xray only events and/or VISAR references.
    IN:
        xray_trans : decimal value of the xray transmission
        nshot      : number of shots to perform, should be only 1
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
    # make sure the copper target is in at TCC for timing
    cu()
    time.sleep(3)
    # set slits to %) mic but not super import ant
    slit4.move(0.5)
    # set the MXI IN
    mxi(state = 'IN')
    # to change the Xray transmission for the driven shot and set the flipflop mode
    seq.stop()
    pp.flipflop()
    att_update()
    SiT(xray_trans)
    if (xray_trans == 1):
        logger.warning('Forcing attenuators out in case GUI is stuck')
        clear_att.put(0)
        time.sleep(1)
        all_att_out.put(0)

    # prepare the sequence
    seq.sequence.put_seq(firing_sequence)
    seq.play_mode.put(1)
    seq.rep_count.put(nshot)
    # make sure the daq is not connected before starting the command
    if (daq.connected == True):
        daq.disconnect()
    daq.begin(record=save, events=nshot)

    fireset_input = fireset_input_state()
    logger.critical('Waiting for input...')
    while (fireset_input < 2.0):
#        time.sleep(1)
        fireset_input = fireset_input_state()
    else:
        logger.success('Fireset button has been preset! Detonation is happening! {:.3f} V.'.format(fireset_input))
    # execute the sequence 
    seq.start()
    logger.success('Shot has been executed! After shot-checklist time')

    msg = '{} x-ray shot at {:.4f}% with full firing sequence. {}'.format(nshot, 100.0 * xray_trans, msg_log_target)

    if (save == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        mecl.post(msg, run=RunNumber, tags=tags_det)
# saving the scope traces in local folder e.g. /cds/home/opr/mecopr/experiments/mecl1016522/lecroy_xray
        time.sleep(15)
        logger.success('Saving the scope trace now.')
        LOSC('1').save_scope_to_eLog(2)

#
#    x.nsl._config['rate']=rate
#    x.nsl._config['slowcam'] = slow_cam
#    # make sure the daq is not connected before starting the command
#    if (daq.connected == True):
#        daq.disconnect()
#    x.nsl.configure(x.nsl._config)
#    msg = '{} x-ray only shots at {:.4f}% {}.'.format(xray_num, 100.0 * xray_trans, msg_log_target)
#    tags_ref = ['firing', 'xray']
#
#    # check if a dark is necessary
#    if (dark > 0):
#         x.nsl.predark=dark
#         print('Taking a dark reference image.')
#    else:
#         x.nsl.predark=0
#         print('No dark reference image taken.')
#
#    # check if shutters are necessary
#    if (shutters == True):
#         x.nsl.shutters=[1, 2, 3, 4, 5, 6]
#    else:
#         x.nsl.shutters=[]
#         print('Shutters are left open.')
#    pp.flipflop()
#    x.nsl.prex=xray_num
#    x.nsl.during=0
#    att_update()
#    SiT(xray_trans)
#    if (daq_end == True):
#        p=x.nsl.shot(record=save, end_run=True)
#    if (daq_end == False):
#        p=x.nsl.shot(record=save, end_run=False)
#    # loop waiting for the input from the mechanical button
#    fireset_input = fireset_input_state()
#    logger.critical('Waiting for input...')
#    while (fireset_input < 2.0):
##        time.sleep(1)
#        fireset_input = fireset_input_state()
#    else:
#        logger.success('Fireset button has been preset! Detonation is happening! {:.3f} V.'.format(fireset_input))
#    # to run the plan
#    RE(p)
#    if (save == True):
#        RunNumber = get_run_number(hutch='mec', timeout=10)
#        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
#        mecl.post(msg, run=RunNumber, tags=tags_ref)
#    # restore laser rep rate in case the next action does not involve the use of the following scripts (like shots from the hutch)
#    x.nsl._config['rate']=10





# For delay line in the chamber:
# delay_line_t0 to change manually for now
# mm
# for LY27 mm, Mono OUT
#delay_line_t0 = -85.43
# for LY27 mm, Mono IN
delay_line_t0 = 11.002  #was 86.59
# mm/ps, 299792458 m/s
delay_line_calib = 0.149896229

def spl_timing_save_t0():
    '''
    Description : saving the current VITARA position to a PV
    '''
    global spl_timing_tmp
    # get the vitara value
    spl_timing_tmp = spl_vitara.get()
    # store vitara value in a PV
    spl_vitara_pv.put(spl_timing_tmp)
    logger.success('The timing is set at {} ns.'.format(spl_timing_tmp))

def spl_timing_update_t0(post_to_elog=True, offset=0e-15):
    '''
    Description : updating the current VITARA position with an offset in fs experienced with the timetool 
    IN:
        post_to_elog : True to send the value of offset and new t0 to the elog.
        offset : offset in fs to compensate the VITARA t0.
    '''
    # get the original PV vitara value
    spl_original_vitara = spl_vitara_pv.get()
    # set the new t0 in PV, 1e-9 to convert from fs to ns but in PV unit
    spl_vitara_pv.put(spl_original_vitara + (offset * 1e-9))
    logger.success('The timing is offset by {:.2f} fs, from {:.6f} ns to {:.6f} ns.'.format(offset * 1e-15, spl_original_vitara, spl_vitara_pv.get()))
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    if (post_to_elog == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg = 'New t0 value is {}, which is an offset of {} fs compared to original t0.'.format(spl_vitara_pv.get(), offset*1e15)
        mecl.post(msg, run=RunNumber, tags=['timing', 'offset'])


def spl_timing(tt_delay_t0, mono=[False, 'out'], timing=0.0e-9):
    '''
    Description : setting a new pump-probe delay
    IN          :
        tt_delay_t0: value of the delay line stage of the time tool in mm
        mono    : defines if you want the mono and if you want it IN or OUT
        timing  : value for the Xrays to arrive 'timing' ns later than optical laser when positive.
    '''
    global delay_line_t0, delay_line_calib
    if (mono[0] == True):
        if (mono[1] == 'out'):
            spl_vitara.put(spl_vitara_pv.get() - (timing / 1.0e-9))
            logger.success('Timing done with Mono OUT.')
        if (mono[1] == 'in'):
            spl_vitara.put((spl_vitara_pv.get() + (1.116)) - (timing / 1.0e-9))
            logger.success('Timing done with Mono IN.')
    else:
        spl_vitara.put(spl_vitara_pv.get() - (timing / 1.0e-9))
        logger.success('Timing of the vitara has been adjusted from {} ns to {} ns.'.format(spl_vitara_pv.get(), spl_vitara_pv.get() - (timing / 1.0e-9)))
    # moving delay line if delay requested is not larger than 500ps:
    if (timing < 0.5e-9):
        tt_delay_offset = (timing / 1.0e-12) * delay_line_calib
        tt_delay_motor.umv(tt_delay_t0 - tt_delay_offset)
        logger.info('Moved delay line to compensate for drive timing.')
    else:
        logger.warning('Requested delay of {} ns is too large to compensate the time tool delay line!'.format(timing / 1e-9))
    logger.success('New timing is {} ps after the optical laser.'.format(timing/ 1.0e-12))

def spl_scan(msg='', tags_words=['optical', 'sample', 'scan'], save_data = True, use_xrays = True, shot_rate = 1, nshot = 50, nrow = 1, delay = 0.0e-9):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        msg        : set a message in the elog
        tag_words  : set tag words for the elog 
        save_data  : True if you want to save the data in the DAQ, False otherwise 
        use_xrays  : True if you want to raster with the xrays, False otherwise
        shot_rate  : SPL shot rate, use 1 or 5 for 1Hz and 5Hz
        nshot      : defines the number of shots per row
        nrow       : defines the nu;ber of row to raster 
        delay      : delay between Xrays and optical laser in s
    '''
    # set the timing (mono is IN...)
    spl_timing(mono = 'out', timing = delay)
    # create plan
    p = x.xy_fly_scan(nshots=nshot, nrows=nrow, record=save_data, xrays=use_xrays, rate=shot_rate)
    # execute the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is exhausted otehrwise post in t3he wrong run number
    if (save_data == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg = msg + '{} laser shot(s) per row, and {} row(s) total: delay is {:.2f} ps.'.format(nshot, nrow, 1.0e12 * delay)
        mecl.post(msg, run=RunNumber, tags=tags_words)
    logger.success('End of the scan.')

def spl_mode(mode='alignment'):
    '''
    Description: Set the uniblitz and inhibit configuration for single shot (ss), continuous 5Hz (5Hz) and alignment mode (alignment).
    IN:
        mode: single_shot, alignment, (5Hz not available yet)
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
#        SPL.gige_trig_5Hz()
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
        SPL.gige_trig_ss()
    # force enable the uniblitz triggering
    spl_uniblitz_evr_btn.put(1)
    print('Force enabling the triggering of the uniblitz.')

def mouse_trapped():
    '''
    Description: check if mouse trapped sees signal and interupt operation to force check the back reflection camera signal
    '''
    tot_count = back_ref.get()
    hit_threshold = 5264789
#    hit_threshold = 264789
    answer = 'No'
    if tot_count > hit_threshold:
        while answer != 'Yes':
            answer = input('We are hit! Check MEC SPL 8/gige16 for the amount, report to the laser team for ok to proceed, then type "Yes" to complete.')
        logger.critical('Back reflection was detected.')
    else:
        logger.success('No back reflection detected.')
#    if tot_count > hit_threshold:
#        root = tkinter.Tk()
#        tkinter.messagebox.askokcancel(title='Back reflection', message='We are hit! Check MEC SPL 8/gige 16 camera to proceed!')
#        tkinter.Button(root, text="Ok", command=root.destroy).pack()
#        root.mainloop()
    return tot_count

def spl_backlight():
    '''
    Description: set the experimental system to provide backillumination for sample alignment or timing
    IN : NA
    OUT: NA
    '''
    # force no light on target
    spl_slicer_evr_btn.put(0)
    logger.success('SPL slicer trigger DISABLE')
    gaia_detune()
    shutter4.close()
    spl_mode(mode='single_shot')
    # move devices IN
    iris_move(position='CLOSE') 
    fw_vac(position=6)
    # check that the energy limiter is out, put it out if not
    if (rpel_in.get() == 1  and rpel_out.get() == 0):
        rpel_button.put(1)
        logger.warning('RP Energy Limiter is now OUT.')
    else:
        logger.warning('RP Energy Limiter is already OUT.')
    foc_img_move(position='IN')
    fsi_move_fast(position='OPEN')
    pm_fast(position='OUT')
    filter_fast(position='OUT')
    fw3set(position=6)
    fw_vac(position=1)
    shutter4.open()
    spl_mode(mode='alignment')
    # set the trigger to 5Hz
    spl_slicer_evr_code.put(44)
    # sleep time necessary to make sure the trigger is properly enabled
    time.sleep(0.2)
    if (spl_slicer_evr_btn.get() == 0):
        spl_slicer_evr_btn.put(1)
    logger.success('SPL slicer trigger button is Enabled.')
    x.start_seq(1)
    logger.success('You can BEGIN RUNNING the DAQ to check timing or alignment of a target.')

def spl_laser_focus_imaging():
    '''
    Description: set the experimental system to check the laser spot focus shape and alignment 
    IN : NA
    OUT: NA
    '''
    # force no light on target
    spl_slicer_evr_btn.put(0)
    logger.success('SPL slicer trigger DISABLE')
    gaia_detune()
    spl_mode(mode='single_shot')
    fw3set(position=5)
    fw_vac(position=4)
    pm(position='OUT')
    filter(position='IN')
    # check that the energy limiter is out, put it out if not
    if (rpel_in.get() == 1  and rpel_out.get() == 0):
        rpel_button.put(1)
        logger.warning('RP Energy Limiter is now OUT.')
    else:
        logger.warning('RP Energy Limiter is already OUT.')
    ## move to empty space just above the pin
    # commented because it is wrong for the pillar target holder
    #target_save()
    #pin_slow()
    #tc_hexapod.y.umv(tc_hexapod.y.position-2.0)
    # move devices IN
    foc_img_move(position='IN')
    iris_move(position='OPEN')
    x.start_seq(1)
    spl_mode(mode='alignment')
    # set the trigger to 5Hz
    spl_slicer_evr_code.put(44)
    # sleep time necessary to make sure the trigger is properly enabled
    time.sleep(0.2)
    if (spl_slicer_evr_btn.get() == 0):
        spl_slicer_evr_btn.put(1)
    logger.success('SPL slicer trigger button is Enabled.')
    logger.success('You can BEGIN RUNNING the DAQ')
    logger.success('Align FF_NF on opal 4 --> cross (1168,876)')
    input("Press Enter when aligned...")

def spl_ready_for_shot():
    '''
    Description: set the experimental system to be ready for a laser shot 
    IN : NA
    OUT: NA
    '''
    # force no light on target
    spl_slicer_evr_btn.put(0)
    logger.success('SPL slicer trigger DISABLE')
    spl_mode(mode='single_shot')
    # setting the devices out
    foc_img_move(position='OUT')
    #disp_sens_bs(position='IN')
    pm_fast(position='OUT')
    iris_move_fast(position='OPEN')
    fsi_move(position='CLOSE')
    filter(position='OUT')
    fw3set(position=6)
   # fw_vac(position=6)
    # check that the energy limiter is out, put it out if not
    if (rpel_in.get() == 1  and rpel_out.get() == 0):
        rpel_button.put(1)
        logger.warning('RP Energy Limiter is now OUT.')
    else:
        logger.warning('RP Energy Limiter is already OUT.')
    logger.success('You are ready for a SPL shot on target.')
    logger.success('Are the diagnostics ready for a shot?')

spl_sequence = [[177, 12, 0, 0],
                [168, 10, 0, 0],
                [176,  2, 0, 0],
                [169,  0, 0, 0]]

def spl_shot(tt_delay, nshot=1, gaia_offset=0., delay=0.0e-9, xray_threshold=0.1, xray_trans=1, msg='', tags_words=['optical', 'sample'], auto_trig=True, save_data=True, freeze_daq=False):
    '''
    Description: script to shoot the optical laser and time it with the xrays. It automatically push to the elog the laser energy, the timing and the xray SiT transmission.
    IN:
        nshot           : defines the nu;ber of shots, less than 10 for bluesky3 script, otherwise evt sequencer is used
        spl_ener        : gaia timing to control the spl energy, decimal value, meaning 1. = 100%, 0.5 = 50%
        delay           : moves absolute, in s
        xray_threshold  : xray energy threshold below which laser shot shall not take place
        tt_delay        : position of the time tool delay line in mm
        xray_trans      : X ray transmission, meaning 1. = 100%, 0.5 = 50%
        msg             : message to post to the elog
        tags_words      : accompagnying tags to the elog
        auto_trig       : True to make sure the triggers are enabled, False otherwise (simulation test for example)
        save_data       : save the data in teh DAQ if True, otherwise don't
        freeze_daq      : allows to see the last run. Requires a daq.disconnect() after the shot to preprare for the next shot.
    OUT:
        execute the plan and post a comment to the elog.
    '''
    # to change the Xray transmission for the driven shot and set the flipflop mode
    seq.stop()
    pp.flipflop()
    lights_off()
    att_update()
    SiT(xray_trans)
    # set the uniblitz mode to provide 5Hz but protected by the uniblitz. Used for all DAQ modes.
    spl_mode(mode='single_shot')
    time.sleep(0.2)
    gaia_timing_offset(gaia_offset)
    # set probe timing
    # check if the laser is locked before progressing in the shot
    while True:
        if (spl_locking == 0):
            logger.error('Laser is NOT locked.')
            logger.warning('Follow the timing relocking procedure.')
            user_input = input('Press "L" and Enter once locking is confirmed to continue.')
            if (user_input.lower() == 'L'):
                break
        else:
            logger.success('Laser is locked.')
            break
# to reenable after test is done
    spl_timing(tt_delay_t0 = tt_delay, timing=delay)
    # check the trigger status
    if (auto_trig == True):
        # look at the event code
        spl_slicer_evr_code.put(176)
        # sleep time necessary to make sure the trigger is properly enabled
        time.sleep(0.2)
        if (spl_slicer_evr_btn.get() == 0):
            spl_slicer_evr_btn.put(1)
        logger.success('SPL slicer trigger button is Enabled.')
    else:
        logger.warning('SPL slicer trigger button is not being checked by the script.')
    if (nshot < 10):
        # to setup the plan for a driven shot, and make sure the rate for the drive laser is 10 Hz
        x.fsl._config['rate']=5
        # force the use of the shutters as you are driving the target
        x.fsl.shutters=[1, 2, 3, 4, 5, 6]
#        x.fsl.shutters=[1, 3, 5, 6]
        x.fsl.prelasertrig=12 #24
        x.fsl.predark=0
        x.fsl.prex=0
        x.fsl.during=nshot
        # to set the plan with the new configuration
        p=x.fsl.shot(record=save_data, end_run=freeze_daq)
        # loop until Xrays are back
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
    # checks for back reflection problem
    mouse_trapped()
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
#    if ((xpp_lodcm.get() >= -10.5) and (xpp_lodcm.get() <= -9.5)):
#        logger.success('XPP LODCM is OUT')
#    elif ((xpp_lodcm.get() >= -0.5) and (xpp_lodcm.get() <= 0.5)):
#        logger.warning('XPP LODCM is IN')
#    if (((xpp_ccm1.get() >= -0.5) and (xpp_ccm1.get() <= 0.5)) and ((xpp_ccm2.get() >= -0.5) and (xpp_ccm2.get() <= 0.5))):
#        logger.success('XPP CCM is OUT')
#    elif (((xpp_ccm1.get() >= -9.5) and (xpp_ccm1.get() <= -8.5)) and ((xpp_ccm2.get() >= -9.5) and (xpp_ccm2.get() <= -8.5))):
#        logger.critical('XPP CCM is IN')
#    logger.warning('XPP CCM state unknown')
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
    if (xcs_yag1.get() == 3):
        logger.success('XCS YAG1 is OUT')
    elif (xcs_yag1.get() == 2):
        logger.critical('XCS YAG1 is IN')
    if (ref_y.position > -1 and ref_y.position < 1): 
        logger.critical("Reference laser is IN, at {:.3} mm".format(ref_y.position))
    else:
        logger.success('Reference laser is OUT, at {:.3} mm'.format(ref_y.position))
    if (yag0.position == 'OUT'):
        logger.success('Yag 0 is OUT')
    elif (yag0.position == 'YAG'):
        logger.critical('Yag 0 is IN')
    elif (yag0.position == 'Unknown'):
        logger.warning('Yag 0 is Unknown position')
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
    if (pp.position == 'CLOSED'):
        logger.critical('Pulse Picker is CLOSED.')
    else:
        logger.success('Pulse Picker is OPEN.')
    print("at1l0 transmission : " +str(at1l0.position))
    print("at2l0 transmission : " +str(at2l0.position))
    print("Si transmission : "+str(SiT()))
    print("slit 1  : ({:.3f}, {:.3f})".format(slit1.position[0], slit1.position[1]))
    print("slit 2  : ({:.3f}, {:.3f})".format(slit2.position[0], slit2.position[1]))
    print("slit 3  : ({:.3f}, {:.3f})".format(slit3.position[0], slit3.position[1]))
    print("slit 4  : ({:.3f}, {:.3f})".format(slit4.position[0], slit4.position[1]))
    print("slit 5  : ({:.3f}, {:.3f})".format(slit5.position[0]-1.588, slit5.position[1]-1.533))
    print("IPMs : UNKNOWN POSITION")
    be_stack = be_lens_stack.get()
    if ((be_stack == 1) or (be_stack == 2) or (be_stack == 3)):
        logger.warning('Be lens stack {} is IN.'.format(be_stack))
    else:
        logger.error('Be lens stack OUT.')
    print("HRM : UNKNOWN POSITION")
    print('******************************************************')
    if (spl_locking.get() == 1):
        logger.success('Laser is locked.')
    if (spl_locking.get() == 0):
        logger.error('Laser is NOT locked.')
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
#        print('out':JJ1:JAWS:XCENTER.VAL
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

def zero_hex_angles():
    tc_hexapod.u.umv(0)
    tc_hexapod.v.umv(0)
    tc_hexapod.w.umv(0)

def pin():
    """ move to the pin. Uses the User pvs."""
    zero_hex_angles()    
    tgx.mv(pintgx.get())
    tc_hexapod.x.mv(pinhx.get())
    tc_hexapod.y.mv(pinhy.get())
    tc_hexapod.z.mv(pinhz.get())

def pin_slow():
    """ move to the pin taking the right amount of time. Uses the User pvs."""
    zero_hex_angles()
    tgx.umv(pintgx.get())
    tc_hexapod.x.umv(pinhx.get())
    tc_hexapod.y.umv(pinhy.get())
    tc_hexapod.z.umv(pinhz.get())

def pin_s():
    """ saves current position in pin user pv. Uses the User pvs."""
    pintgx.put(tgx())
    pinhx.put(tc_hexapod.x.get()[2])
    pinhy.put(tc_hexapod.y.get()[2])
    pinhz.put(tc_hexapod.z.get()[2])

def pinhole():
    """ move to the pinhole. Uses the User pvs."""
    zero_hex_angles()
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
    zero_hex_angles()
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
    zero_hex_angles()
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

def siemens():
    """ move to the Siemens star. Uses the User pvs."""
    zero_hex_angles()
    tgx.mv(siemenstgx.get())
    tc_hexapod.x.mv(siemenshx.get())
    tc_hexapod.y.mv(siemenshy.get())
    tc_hexapod.z.mv(siemenshz.get())

def siemens_s():
    """ saves current position in Siemens star user pv. Uses the User pvs."""
    siemenstgx.put(tgx())
    siemenshx.put(tc_hexapod.x.get()[2])
    siemenshy.put(tc_hexapod.y.get()[2])
    siemenshz.put(tc_hexapod.z.get()[2])

def zn():
    """ move to the Zn 2.5 mic calibrant. Uses the User pvs."""
    zero_hex_angles()
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

def yag90():
    """ move to the yag90 sample. Uses the User pvs."""
    zero_hex_angles()
    tgx.mv(yag90tgx.get())
    tc_hexapod.x.mv(yag90hx.get())
    tc_hexapod.y.mv(yag90hy.get())
    tc_hexapod.z.mv(yag90hz.get())

def yag90_s():
    """ saves current position in yag90 user pv. Uses the User pvs."""
    yag90tgx.put(tgx())
    yag90hx.put(tc_hexapod.x.get()[2])
    yag90hy.put(tc_hexapod.y.get()[2])
    yag90hz.put(tc_hexapod.z.get()[2])

def grid():
    """ move to the grid sample. Uses the User pvs."""
    zero_hex_angles()
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
    zero_hex_angles()
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
    '''
        Description: Saves the current channel C on the GAIA DG box and sotre it in a PV value.
    '''
    gaiatimingsave.put(gaia_dgbox.get())
    logger.success('Current timing of {} s has been saved to PV.'.format(gaia_dgbox.get()))

def gaia_timing_offset(offset = 0):
    ''' 
        Description: Offset the GAIA timing to detune the amplificaiton, for example to change the amount of energy on target.
        IN:
            offset : value in ns, negative values decrease the energy
    '''
    ch_gaia_val = gaiatimingsave.get() + (1.0e-9 * offset)
    gaia_dgbox.set(ch_gaia_val)
    if (offset == 0):
        logger.critical('GAIA is timed IN.')
    else:
        logger.warning('GAIA is timed off by {} ns.'.format(offset))

def gaia_detune():
    '''
        Description: Function to offset the gaia timing by 100 ns to not amplify MPA anymore
    '''
    gaia_timing_offset(100)
# ----

#def talbot_in():
#    """ moves the 500mm stage to the NEO position in user pv."""
#    talbot_x.umv(34.15)
#
#def talbot_out():
#    """ moves the 500mm stage to the NEO position in user pv."""
#    talbot_x.umv(-35)

# target motion definition (TO DO: add target.tweakxy)
def target_up(n=1):
    """ moves up n spaces, spacing is 3.5mm"""
    tc_hexapod.y.mv(tc_hexapod.y.get()[2]+(n*5))

def target_down(n=1):
    """ moves down n spaces, spacing is 3.5mm"""
    target_up(-n)

def target_next(n=1):
    """ moves next n spaces, spacing is 3.7mm"""
    tgx(tgx()+(n*5))

def target_prev(n=1):
    """ moves previous n spaces, spacing is 3.7mm"""
    target_next(-n)

def move_target(n=1, angle=45):
    """ moves next n spaces, spacing is 3.7mm"""
    val = np.sin(angle*3.141592/180)
    tgx.umvr(-n*3.505*val)
    tc_hexapod.y.umvr(n*3.709*val)

def move_target_back(n=1, angle=45):
    """ moves next n spaces, spacing is 3.7mm"""
    val = np.sin(angle*3.141592/180)
    tgx.umvr(n*3.505*val)
    tc_hexapod.y.umvr(-n*3.709*val)

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
letter_arr = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

# width of a frame in mm
one_u = 40.2
half_u = 19.5
# look from the back of the target holder, 1 is for a full U, 0.5 is for a half U, start from the left
# defining a global variable to store the current target position
msg_log_target = ''

def move_to_target(config='colinear', frame_cfg=[1, 'F1', 1, 'F2', 1, 'F3'], pillar_cfg='legacy', frame=1, target='A1', visar_disable=True):
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
                          colinear: for std colienar LPL beam delivery
                          perp: for perpendicular LPL beam delivery
                          long: for colienar beam delivery but using the elongated holes
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
        # x_start_pos is pin_pos - position of the first frame A1 column value
        # when using the perpendicular beam delivery with target holder perpendicular
        #pin_pos = 154.938
        # when using the colinear configuration with the target holder perpendicular to the FEL
        pin_pos = 156.046
        #pin_pos = 154.17
        #pin_pos = 148.47
        #x_start_pos = 17.2
        # for std delivery
        # to uncomment when putting the calibrant half U back
        x_start_pos = 35.2
        y_start_pos = -12.4
        #x_start_pos = 31.1
        #y_start_pos = -10.7
        # for LY27
        #x_start_pos = 30.81
        #y_start_pos = -12.0
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
        target_row = int(target[1])
        # initialisation of x and y target positions
        y_target_pos = y_start_pos
        x_target_pos = 0.0
        # calculating the y position of the target
        if (target_row > 1):
            y_target_pos = y_target_pos + ((target_row - 1) * y_step)
        # calculatinf the x position of the target
        if (target_col > 1):
            x_target_pos = x_target_pos + ((target_col - 1) * x_step)
        # execute the motion
        tgx.umv(pin_pos - (x_target_pos + frame_pos) + xcorr)
        #tc_hexapod.y.mv(y_target_pos + ycorr)
        tc_hexapod.y.umv(y_target_pos + ycorr)

        # function to take into account offset in target plan
        #x_offset = (133.76 - tgx.position)*np.tan(0.00899)
        #tc_hexapod.x.umv(-x_offset)

        print('Moving to Frame {}, target {}.'.format(frame, target))
        print('Tweak position as appropriate.')
        print('The frame configuration is {}.'.format(frame_cfg))
        # print in the eLog only the naming used by the users to avoid confusion
        msg_log_target = 'on frame {}, target {}'.format(frame_cfg[(2*frame)-1], target)

    if (config == 'long'):
        print('Configuration: colinear with long target openings on cartridge.')
        # 1U is 40mm large, 0.5U is 20mm, starting from just after the calibration cartridge
        # x_start_pos is pin+pos - position of the first frame A1 column value
        # when using the perpendicular beam delivery with target holder perpendicular
        #pin_pos = 154.938
        # when using the colinear configuration with the target holder perpendicular to the FEL
        pin_pos = -140.78
        # for std delivery
        x_start_pos = 32.83
        y_start_pos = -10.0
        # for LY27
        #x_start_pos = 30.81
        #y_start_pos = -12.0
        x_step = 6.55
        y_step = 7.01
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
        target_row = int(target[1])
        # initialisation of x and y target positions
        y_target_pos = y_start_pos
        x_target_pos = 0.0
        # calculating the y position of the target
        if (target_row > 1):
            y_target_pos = y_target_pos + ((target_row - 1) * y_step)
        # calculating the x position of the target
        if (target_col > 1):
            x_target_pos = x_target_pos + ((target_col - 1) * x_step)
        # execute the motion
        tgx.umv(pin_pos + (x_target_pos + frame_pos) + xcorr)
        #tc_hexapod.y.mv(y_target_pos + ycorr)
        tc_hexapod.y.umv(y_target_pos + ycorr)

        # function to take into account offset in target plan
        x_offset = (-107.4 - tgx.position)*np.tan(0.006818)
        #x_offset = (133.76 - tgx.position)*np.tan(0.00899)
        tc_hexapod.x.umv(x_offset)

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
        target_row = int(target[1])
        # initialisation of x and y target positions: reference is first pillar
        x_target_pos = 129.945
        y_target_pos = -11.9
        y_step = 3.0
        if (pillar_cfg == 'peek'):
            y_target_pos = -10.5
            y_step = 4.6
        x_step = 11.303
        # zeroing the hexapod angles
        zero_hex_angles()
        # calculating the y position of the target
        if (target_row > 1):
            y_target_pos = y_target_pos + ((target_row - 1) * y_step)
        # calculating the x position of the target
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

def mxi(state = 'IN'):
    '''
    description: set the MXI system IN or OUT
    input:
        state   : IN or OUT
    '''
    if (state == 'IN'):
        mxi_y.put(-1.870)
        time.sleep(2)
        mxi_z.put(14.97)
        logger.success('MXI is IN')
    if (state == 'OUT'):
        mxi_z.put(6.96)
        time.sleep(2)
        mxi_y.put(-3.830)
        logger.success('MXI is OUT')


glass_window_btn = EpicsSignal('MEC:XT2:VGC:06:OPN_SW')
window_rst_btn = EpicsSignal('MEC:PLC:ALM:00:RST_SW')
interlock_status = EpicsSignal('MEC:XT2:VGC:04:ILKALM')
be_window_btn = EpicsSignal('MEC:XT2:VGC:05:BE_INS_SW')
vgc_04_opn_btn = EpicsSignal('MEC:XT2:VGC:04:OPN_SW')

def set_beamline(mode='ref_laser'):
    '''
    description: insert qnd remove relevant components to all for the reference laser to be used for L-10165 beamtime
    input:
        mode: ref_laser (to use the reference laser for beamblock and lexan installation), alignment (for aligning the HE with the xrays), statics (to obtain cold data from HE)
    '''
    pp.close()
    logger.success('Pulse picker closed')
    if (mode == 'ref_laser'):
        logger.info('Setting beamline components to deliver reference laser')
        # insert glass window and reset system
        logger.warning('Inserting Be window, it takes 3s')
        be_window_btn.put(0)
        time.sleep(3)
        logger.warning('Clearing the window issue, it takes 10s')
        for insist in range(10):
            window_rst_btn.put(1)
            time.sleep(1)
            window_rst_btn.put(0)
            time.sleep(1)
        vgc_04_opn_btn.put(1)
        logger.success('Be window system and gate valve should be in normal state now')
        logger.success('Check if Glass window is IN and gate valve OPEN')
        logger.success('If NOT, proceed manually')
        # insert ref laser diode
        ref_y.umv(0)
        logger.success('Ref laser IN')
        # remove MXI
        mxi(state='OUT')
        # insert pin
        pin()
        logger.success('Pin IN')
        # set slit to 2 mm
        slit4.move(2)
        logger.success('Slit 4 OPEN')
        logger.success('REF LASER READY TO GO')

    if (mode == 'alignment'):
        logger.info('Setting beamline components for HE sample alignment')
        # set safe SiT
        SiT(0.01)
        logger.success('SiT=0.01')
        # remove MXI
        mxi(state='OUT')
        # insert Be window
        be_window_btn.put(1)
        logger.success('Be window IN')
        # set pulse picker to 1 Hz
        pulse_picker(rate=1)
        # remove ref laser diode
        try:
            ref_y.umvr(-51)
        except:
            logger.success('Reference laser is OUT')
            
    if (mode == 'statics'):
        logger.info('Setting beamline components for statics shots')
        # set operation SiT
        SiT(0.1)
        logger.success('SiT=0.1')
        # set slit to 0.5 mm
        slit4.move(0.5)
        logger.success('Slit 4 at 0.5 mm')
        # insert MXI
        mxi(state='IN')
        # set pulse picker to 1 Hz
        pulse_picker(rate=1)
        logger.success('STATICS READY TO GO')
        
def pm(position = 'IN', wait_mvt = True):
    """
    Description: move the SPL power meter IN or OUT of the SPL path
    IN:
        position: IN or OUT
    """
    if (position == 'IN'):
        spl_powermeter_stage.umv(295)
        logger.warning('Power meter is IN')
    if (position == 'OUT'):
        spl_powermeter_stage.umv(95)
        logger.success('Power meter is OUT')

def pm_fast(position = 'IN', wait_mvt = True):
    """
    Description: move the SPL power meter IN or OUT of the SPL path
    IN:
        position: IN or OUT
    """
    if (position == 'IN'):
        spl_powermeter_stage.mv(295)
        logger.warning('Power meter is IN')
    if (position == 'OUT'):
        spl_powermeter_stage.mv(95)

def filter(position = 'IN', wait_mvt = True):
    """
    Description: move the SPL OD4 filter IN or OUT of the SPL path
    IN:
        position: IN or OUT
    """
    if (position == 'IN'):
        spl_filter_stage.umv(98)
        logger.success('Filter is IN')
    if (position == 'OUT'):
        spl_filter_stage.umv(1)
        logger.success('Filter is OUT')

def filter_fast(position = 'IN', wait_mvt = True):
    """
    Description: move the SPL OD4 filter IN or OUT of the SPL path
    IN:
        position: IN or OUT
    """
    if (position == 'IN'):
        spl_filter_stage.mv(98)
        logger.success('Filter is IN')
    if (position == 'OUT'):
        spl_filter_stage.mv(1)

def iris_move(position = 'CLOSE'):
    """
    Description: open or close the SPL vacuum iris
    IN:
        position: OPEN or CLOSE
    """
    if (position == 'CLOSE'):
        vacuum_iris.umv(0.02)
        logger.warning('Vacuum Iris is CLOSED')
    if (position == 'OPEN'):
        vacuum_iris.umv(+5.5)
        logger.success('Vacuum Iris is OPEN')

def iris_move_fast(position = 'CLOSE'):
    """
    Description: open or close the SPL vacuum iris
    IN:
        position: OPEN or CLOSE
    """
    if (position == 'CLOSE'):
        vacuum_iris.mv(0.02)
        logger.warning('Vacuum Iris is CLOSED')
    if (position == 'OPEN'):
        vacuum_iris.mv(+5.5)
        logger.success('Vacuum Iris is OPEN')

def fsi_move(position = 'CLOSE'):
    """
    Description: open or close the blast shield of the FSI
    IN:
        position: OPEN or CLOSE
    """
    if (position == 'CLOSE'):
        fsi.umv(0)
        logger.warning('FSI blast shield is CLOSED')
    if (position == 'OPEN'):
        fsi.umv(75)
        logger.warning('FSI blast shield is OPEN')

def fsi_move_fast(position = 'CLOSE'):
    """
    Description: open or close the blast shield of the FSI
    IN:
        position: OPEN or CLOSE
    """
    if (position == 'CLOSE'):
        fsi.mv(0)
        logger.warning('FSI blast shield is CLOSED')
    if (position == 'OPEN'):
        fsi.mv(75)

def foc_img_move(position ='OUT'):
    """
    Description: move IN or OUT the SPL imaging system looking at the SPL laser spot
    IN:
        position: IN or OUT
    """
    if (position == 'OUT'):
        imaging_syst_pos = 31.837
        imaging_syst.umv(imaging_syst_pos)
        logger.success('Imaging system lens is OUT.')
    if (position == 'IN'):
        imaging_syst_pos = -47.837
        imaging_syst.umv(imaging_syst_pos)
        logger.warning('Imaging system lens is IN.')

def disp_sens_bs(position ='OUT'):
    """
    Description: move IN or OUT the displacement sensor blast shield
    IN:
        position: IN or OUT
    """
    if (position == 'OUT'):
        disp_sens_bs_pos = 1.0
        disp_sens_bs_mot.umv(disp_sens_bs_pos)
        logger.success('Displacement sensor blast shield is OUT.')
    if (position == 'IN'):
        disp_sens_bs_pos = 40.0
        disp_sens_bs_mot.umv(disp_sens_bs_pos)
        logger.success('Displacement sensor blast shield is IN.')

def fw3set(position=6):
    """
    Description: Function to move the filter wheel to a desired value in absolute
    IN:
        position : 6 is OD4, 1 is empty
    """
    cur_pos = fw3pos.get()
    # extract the number of times we will need to move the FW to get in position
    tmp_inc = position - cur_pos
    for i in np.arange(abs(tmp_inc)):
        if (tmp_inc > 0):
            fw3inc.put(1)
        if (tmp_inc < 0):
            fw3dec.put(1)
        time.sleep(2)
    logger.success('Filter Wheel 3 is in position {}.'.format(fw3pos.get()))

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
    logger.success('Filter Wheel 4 is in position {}.'.format(fw4pos.get()))

def fw_vac(position=6):
    """
    Function to move the vacuum filter wheel to a desired value in absolute
    IN:
        position :  1 is OD 0.1
                    2 is OD 1
                    3 is OD 2
                    4 is OD 4
                    5 is OD 5
                    6 is OD 7
    """
    if (position == 1):
        fw_vac_mot.umv(13.8)
    if (position == 2):
        fw_vac_mot.umv(11.5)
    if (position == 3):
        fw_vac_mot.umv(9.2)
    if (position == 4):
        fw_vac_mot.umv(6.9)
    if (position == 5):
        fw_vac_mot.umv(4.6)
    if (position == 6):
        fw_vac_mot.umv(2.3)
#def spl_focus_alignment():
#    """
#    Procedure to check the laser spot size.
#    """
#    pm('IN')
#    spl_mode('alignment')
#    gaia_timing_offset(0)
#    x.start_seq(5)
#    print('You can BEGIN RUNNING the DAQ')
#    print('Check if RP attenuators are OUT')
#    input("Press Enter to continue...")
#    spl_slicer_evr_btn.put(1)
#    print('Align FF_NF on opal 1 --> cross (768,256)')
#    input("Press Enter when aligned...")
#    gaia_detune()
#    spl_slicer_evr_btn.put(0)
#    iris_move('OPEN')
#    pin()
#    print('Waiting 10s for the pin to move IN')
#    time.sleep(10)
#    tc_hexapod.y.mv(tc_hexapod.y.get()[2]-3.0)
#    fw4set(position = 6)
#    imaging_system('IN')
#    print('Ready to send the focused beam')
#    print('opal 5 --> cross (1168,876)')
#    input("Press Enter to continue...")
#    pm('OUT')
#    spl_slicer_evr_btn.put(1)

#def spl_target_alignment():
#    """
#    Alignment procedure for a target or to back illuminate a pin.
#    """
#    spl_slicer_evr_btn.put(0)
#    print('SPL slicer trigger DISABLE')
#    pm('IN')
#    iris_move('CLOSE')
#    gaia_timing_offset(0)
#    spl_mode('alignment')
#    x.start_seq(5)
#    print('You can BEGIN RUNNING the DAQ')
#    fw4set(position = 1)
#    imaging_system('IN')
#    pm('OUT')
#    print('You can start aligning a new target using op.next_wire().')

#def spl_shot_readiness():
#    """
#    Getting ready for a shot on target.
#    """
#    spl_slicer_evr_btn.put(0)
#    print('SPL slicer trigger DISABLE')
#    pm('IN')
#    imaging_system('OUT')
#    if (check_tg_im_out() is False):
#        print('IMAGING SYSTEM NOT OUT ... DO NOT SHOOT')
#    elif (check_tg_im_out() is True):
#        fw4set(position = 6)
#        spl_mode('single_shot')
#        evt_seq_btn.put('Stop')
#        iris_move('OPEN')
#        pm('OUT')
#        print('You can proceed with a shot on target after the announcement:')
#        print('"WE ARE READY FOR A SHOT ON TARGET"')
#        print('"ARE ALL DIAGNOSTICS READY FOR TRIGGER?"')


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
        # rotate the matrix phi = v
        rot_phi = np.array(((np.cos(phi),0,np.sin(phi)),
                 (0,1,0),
                 (-np.sin(phi),0,np.cos(phi))))
        matrix = np.dot(rot_phi,matrix)
        # rotate theta = phi = v # sample mount
        theta = 43.065/2*np.pi/180
        rot_theta = np.array(((np.cos(theta),0,np.sin(theta)),
                 (0,1,0),
                 (-np.sin(theta),0,np.cos(theta))))
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
    return out, phi_array


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
        # rotate the matrix chi
        rot_chi = np.array(((1,0,0),
                         (0,np.cos(chi),-np.sin(chi)),
                         (0,np.sin(chi),np.cos(chi))))

        matrix = np.dot(rot_chi,matrix)
        # rotate theta = phi = v # sample mount
        theta = 43.065/2*np.pi/180
        rot_theta = np.array(((np.cos(theta),0,np.sin(theta)),
                 (0,1,0),
                 (-np.sin(theta),0,np.cos(theta))))
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
    return out, chi_array



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
        # rotate the matrix omega
        rot_omega = np.array(((np.cos(omega),-np.sin(omega),0),
                         (np.sin(omega),np.cos(omega),0),
                         (0,0,1)))
        matrix = np.dot(rot_omega,matrix)

        # rotate theta = phi = v # sample mount
        theta = 43.065/2*np.pi/180
        rot_theta = np.array(((np.cos(theta),0,np.sin(theta)),
                 (0,1,0),
                 (-np.sin(theta),0,np.cos(theta))))
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
    return out, omega_array

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
        epics_phi.put(float(phi))
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
        epics_chi.put(float(chi))
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
        epics_omega.put(float(omega))
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
        time.sleep(sleep_time)

def mvr_hex_vert_45deg(delta):
    ''' moves hexapod for vertical motion
        with 45 deg target holder
        taking into account x axis
        compensation:
        delta: relative motion expected in height
    '''
    tc_hexapod.y.umvr(delta/sqrt(2))
    tc_hexapod.x.umvr(delta/sqrt(2))

def xray_only_45deg_scan(msg='', tags_words=['xray', 'sample', 'scan'], save_data = True, use_xrays = True, shot_rate = 1, nshot = 50, nrow = 1, y_dist=.3, scan_mode='left-right', end_return='start'):
    '''
    Description: script to shoot the xrays while scanning a sample for exp L-10011.
    It automatically pushes parameters to the elog the laser energy.
    IN:
        msg        : set a message in the elog
        tag_words  : set tag words for the elog 
        save_data  : True if you want to save the data in the DAQ, False otherwise 
        use_xrays  : True if you want to raster with the xrays, False otherwise
        shot_rate  : shot rate
        nshot      : defines the number of shots per row
        nrow       : defines the number of row to raster 
        y_dist     : defines the spacing between rows
        scan_mode  : defines the motion pattern ("left-right" with return at the end of each row or "snake")
        end_return : defines the return motion at the end of the scan ("start" position or next "fresh" position
    '''

    # create plan
    if scan_mode == 'left-right':
        p = x.xy_45deg_fly_scan(nshots=nshot, nrows=nrow, y_distance=y_dist, record=save_data, xrays=use_xrays, rate=shot_rate, end_motion=end_return)
    elif scan_mode == 'snake':
        p = x.xy_45deg_fly_snake(nshots=nshot, nrows=nrow, y_distance=y_dist, record=save_data, xrays=use_xrays, rate=shot_rate, end_motion=end_return)
    # execute the plan
    RE(p)
    # to save to the elog: needs to be set after the plan is executed otherwise post in the wrong run number
    if (save_data == True):
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg = msg + '{} xray shot(s) per row, and {} row(s) in total.'.format(nshot, nrow)
        mecl.post(msg, run=RunNumber, tags=tags_words)
    logger.success('End of the scan.')

def countdown(t):
    while t:
        secs, decs = divmod(t, 10)
        timer = '{:02d}.{:01d}'.format(secs, decs)
        print(timer, end="\r")
        time.sleep(0.1)
        t -= 1

def check_remaining_sample_45deg(Nrows=5, Ydist=0.1, Nloops=5):
    Ydist = Ydist / sqrt(2)
    currentHexY = tc_hexapod.y.get()[2]
    nextHexY = currentHexY + Nrows*Nloops*Ydist
    if nextHexY < 7.0:
        remaining = int(divmod(7.0-nextHexY, Nrows*Ydist)[0])
        logger.success('Enough sample remaining... After that sequence, {} similar run(s) remaining.'.format(remaining))
    else:
        recommend = int(divmod(7.0-currentHexY, Nrows*Ydist)[0])
        logger.critical('Not enough sample remaining... Recommendation: {} similar run(s) instead.'.format(recommend))
        user = input('Continue anyway? [y/n]')
        if user == 'y':
            pass
        elif user == 'n':
            print('Press CTRL + C to exit')
            print('Script will continue in')
            countdown(300)
            pass
        else:
            pass

def loopscan_xray_only_45deg(msg='', tags_words=['xray', 'sample', 'scan'], xray_trans=1, shot_rate = 1, nshot = 50, nrow = 1, y_dist=.3, nloop=1):
    check_remaining_sample_45deg(Nrows=nrow, Ydist=y_dist, Nloops=nloop)
    SiT(xray_trans)
    for i in range(nloop):  
        logger.info("Start of "+str(i+1)+" out of "+str(nloop)+" run(s) in the loop")
        daq.disconnect()
        time.sleep(5)
        p = x.xy_45deg_fly_snake(nshots=nshot, nrows=nrow, y_distance=y_dist, record=True, xrays=True, rate=shot_rate, end_motion="fresh")
        RE(p)
        RunNumber = get_run_number(hutch='mec', timeout=10)
        mecl = elog.ELog({'experiment':experimentName}, user='mecopr', pw=pickle.load(open('/reg/neh/operator/mecopr/mecpython/pulseshaping/elogauth.p', 'rb')))
        msg_run = msg + ', SiT = {}, snake scan at {} Hz.'.format(xray_trans, shot_rate)
        mecl.post(msg_run, run=RunNumber, tags=tags_words)
        logger.success("End of "+str(i+1)+" out of "+str(nloop)+" run(s) in the loop")

# --- experiment specific for L-10388 ---
def align_target(value=0, axis='fsi'):
    '''
    Description: method to move the target along the FSI (31deg) or the TSO axis (45deg). Default is positive goes upstream the objective considered. Use fsi to align on the tso, and inversely, use tso to align on the fsi.
    Input:
        axis    : along the 'fsi' or the 'tso' axis
        value   : value to move in mm
    '''
    if axis == 'tso':
        angle = -45 * np.pi / 180. #from deg to rad
    if axis == 'fsi':
        angle = 31 * np.pi / 180. #from deg to rad
    tc_hexapod.x.mvr(value * np.cos(angle))
    tc_hexapod.z.mvr(value * np.sin(angle))

def diag_switch(move_to = 'MXI'):
    '''
    Description: set the beamline for MXI or SAXS
    Input:
        move_to : MXI or SAXS
    '''
    if (move_to == 'MXI'):
        pp.close()
#        be_y.put(79.865)
        logger.warning('Make sure the Hutch Be CRL are OUT.')
        s500mm.put(345.095)
        logger.success('Optique Peter is IN')
        mxi_z.put(-14.669)
        logger.success('MXI lens stack is IN.')
        looger.success('Users can remove absorbers and beam block.')
    if (move_to == 'SAXS'):
        pp.close()
        mxi_z.put(-0.669)
        logger.success('MXI lens stack is OUT.')
        s500mm.put(177.78)
        logger.success('ePix10k is IN')
#        be_y.put(2.865)
        logger.warning('Make sure the Hutch Be CRL are IN.')
#        logger.success('Hutch Be CRL are IN.')
        looger.success('Users can insert absorbers and beam block.')

def preshot(record=True, events=100, transmission=1e-3):
    '''
    Description: script to automatically take number of events for xray only.
    Input:
        events: number of events to save
        record: Tru eto save, False to not save data
    '''
    SiT(transmission)
    time.sleep(10)
    daq.configure(record=record)
    pulse_picker(5)
    daq.begin(events=events)
    time.sleep((events/5)+15)
    daq.disconnect()
    pp.close()

# VAREX operation scripts

def varex_visar_ref():
    ref_only(xray_trans=1.0, xray_num=0, shutters=False, dark=1, daq_end=True,
            calibrant="", rate=1, visar=True, save=True, slow_cam=False,
            varex=False, varex_skip=0, varex_predark=0, varex_prex=0,
            varex_postdark=0, varex_gain=1, varex_binning=1)

def varex_long_xray_ref(SiT=0.1, skip=0, predark=0, prex=1, gain=1, binning=1):
    x.nsl._varex_seq.xray_test()
    varex_xray_ref(SiT=SiT, skip=skip, predark=predark, prex=prex, gain=1, binning=1)
    x.nsl._varex_seq.set_beampos()

def varex_xray_ref(SiT=0.1, skip=100, predark=50, prex=1, gain=1, binning=1):
    ref_only(xray_trans=SiT, xray_num=0, shutters=False, dark=0, daq_end=True,
            calibrant="", rate=10, visar=False, save=True, slow_cam=False,
            varex=True, varex_skip=skip, varex_predark=predark,
            varex_prex=prex, varex_postdark=0, varex_gain=gain,
            varex_binning=binning)

def varex_optical_shot(Elaser=1.0, delay=0.0e-9, SiT=1.0, skip=100, gain=1,
        binning=1, threshold=0.1):
    optical_shot(lpl_ener=Elaser, timing=delay, xray_threshold=threshold,
            xray_trans=SiT, save=True, auto_charge=True, auto_trig=True,
            visar=True, varex=True, varex_skip=skip, varex_predark=0,
            varex_prex=0, varex_during=1, varex_postdark=0, varex_gain=gain,
            varex_binning=binning)
