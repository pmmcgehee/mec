import bluesky.plan_stubs as bps
from mec.db import daq, seq

# Add sequencer, DAQ to detectors for shots
        dets = [daq, seq]

        for det in dets:
            # staging the daq auto calls end_run
            if det is not daq or end_run:
                yield from bps.stage(det)
    
        yield from bps.configure(daq, events=0, begin_sleep=10, record=record, use_l3t=use_l3t, controls=controls)


        # Setup the pulse picker for single shots in flip flop mode
        #pp.flipflop(wait=True)

        # Setup sequencer for requested rate
        sync_mark = int(self._sync_markers[self._config['rate']])
        seq.sync_marker.put(sync_mark)
        seq.play_mode.put(0) # Run sequence once

        # Dark (no optical laser, no XFEL) shots
        if self._config['predark'] > 0:
            # Get number of predark shots
            shots = self._config['predark']
            logging.debug("Configuring for {} predark shots".format(shots))
#            yield from bps.configure(daq, events=shots)
            daq._config['events'] = shots

            # Preshot dark, so use preshot laser marker
            pre_dark_seq = self._seq.darkSequence(shots, preshot=True)
            seq.sequence.put_seq(pre_dark_seq)

            # Number of shots is determined by sequencer, so just trigger/read
            print("Taking {} predark shots ... ".format(self._config['predark']))
            time.sleep(WAITFORDAQ)
            yield from bps.trigger_and_read(dets)
