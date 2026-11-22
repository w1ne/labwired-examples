#!/usr/bin/env python3
"""Read observations from the existing runtime; this file does not simulate motion."""
import json, math, sys
from pathlib import Path
result_path = Path(sys.argv[1])
result = json.loads(result_path.read_text())
tag = result_path.name.removesuffix('-result.json')
rows = []
events = []
for line in result_path.with_name(tag + '.ndjson').read_text().splitlines():
    raw = json.loads(line)
    if 'event' in raw:
        events.append(raw)
        continue
    body = raw.get('body')
    if not body:
        continue
    frame = body['frame']
    x, y, z, w = frame['orientation']
    roll = math.atan2(2*(w*x + y*z), 1-2*(x*x+y*y))
    pitch = math.asin(max(-1, min(1, 2*(w*y-z*x))))
    yaw = math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    rows.append(dict(t=body['timeNs']/1e9, altitude=frame['altitudeM'],
        rpy=[math.degrees(a) for a in (roll,pitch,yaw)], velocity=frame['velocityMps'],
        motors=raw['motors'], faults=frame['faults'], gates=raw.get('gateRegisters',[])))

def streak(start, end, condition):
    first = previous = None
    best = 0.0
    best_window = None
    for row in rows:
        t = row['t']
        if not start <= t < end or not condition(row):
            first = previous = None
            continue
        if first is None or previous is None or t-previous > .03:
            first = t
        previous = t
        if t-first > best:
            best, best_window = t-first, [first,t]
    return dict(seconds=best, window=best_window)

hover_angle = math.degrees(math.asin(1430/16384))
recover_angle = math.degrees(math.asin(900/16384))
level = lambda row, limit: abs(row['rpy'][0]) <= limit and abs(row['rpy'][1]) <= limit
altitude = lambda row: .85 <= row['altitude'] <= 1.15
hover = streak(5,8,lambda row: altitude(row) and level(row,hover_angle))
recovery = streak(13,float('inf'),lambda row: altitude(row) and level(row,recover_angle) and abs(row['rpy'][2]) <= 5)
measurements = dict(
    maximumAltitudeM=max((row['altitude'] for row in rows),default=0),
    finalAltitudeM=rows[-1]['altitude'] if rows else None,
    finalEulerDegrees=rows[-1]['rpy'] if rows else None,
    hover=hover,recovery=recovery,
    rollPeakDegrees=max((row['rpy'][0] for row in rows if 8<=row['t']<9.2),default=0),
    pitchPeakDegrees=max((row['rpy'][1] for row in rows if 9.2<=row['t']<10.4),default=0),
    yawPeakDegrees=max((row['rpy'][2] for row in rows if 10.4<=row['t']<12),default=0))
# Require a fresh, continuous body trace and all four native motor identities.
# Runtime completion alone cannot prove that the observation stream completed.
expected_motors = {(f'ctrl{i}', f'rotor{i}') for i in range(1, 5)}
trace_complete = bool(rows) and rows[0]['t'] <= .03 and rows[-1]['t'] >= result['duration']-.010001
trace_contiguous = all(0 < b['t']-a['t'] <= .03 for a,b in zip(rows,rows[1:]))
all_motors_present = bool(rows) and all(len(row['motors']) == 4 and
    {(m['owner'],m['id']) for m in row['motors']} == expected_motors for row in rows)
checks = dict(
    complete=result['stopped']=='duration' and not result['errors'] and result['seconds'] >= result['duration'],
    completeBodyTrace=trace_complete and trace_contiguous,
    allNativeMotorsObserved=all_motors_present,
    nativeLoadsAcknowledged=all(load['acknowledged'] for body in result['final'] for load in body.get('shaftLoads',[]))
        and sum(len(body.get('shaftLoads',[])) for body in result['final']) == 4)
if not result['faultInjected']:
    checks.update(
        noNativeFaults=not any(m['faults'] for row in rows for m in row['motors']),
        takeoff=any(row['altitude']>.5 for row in rows if row['t']>=2),
        hover=hover['seconds']>=1,
        roll=measurements['rollPeakDegrees']>math.degrees(math.asin(1000/16384)),
        pitch=measurements['pitchPeakDegrees']>math.degrees(math.asin(900/16384)),
        yaw=measurements['yawPeakDegrees']>8,
        recovery=recovery['seconds']>=.5)
else:
    injected = next(e['seconds'] for e in events if e['event']=='fault-injected')
    attempt = next((e for e in events if e['event']=='fault-release-attempt'), None)
    def motor_off(row, motor):
        if str(motor['control_state']).startswith('off:'):
            return True
        # Native `fault:inverter` overrides the off label until its next
        # service. Accept it only with direct L476 register evidence that
        # external ENABLE, TIM1 MOE and every phase channel are disabled.
        gate=next((g for g in row['gates'] if g['owner']==motor['owner']),None)
        return motor['control_state']=='fault:inverter' and gate is not None and \
            gate['gpioBOutput'] & 1 == 0 and gate['timer1BreakDeadTime'] & 0x8000 == 0 and \
            gate['timer1ChannelEnable'] & 0x555 == 0
    off=lambda row: all(motor_off(row,m) for m in row['motors'])
    stopped=lambda row: all(abs(m['speed_rpm'])<1 for m in row['motors'])
    after=[row for row in rows if row['t']>=injected]
    off_times=[row['t'] for row in after if off(row)]
    stop_times=[row['t'] for row in after if off(row) and stopped(row)]
    tail=[row for row in rows if row['t']>=rows[-1]['t']-.5] if rows else []
    post_attempt=[row for row in rows if attempt and row['t']>=attempt['seconds']-1e-9]
    clear_rejected = bool(result.get('faultReleaseRejected'))
    input_cleared = bool(attempt) and not clear_rejected
    sticky_overcurrent = result['faultKind']=='overcurrent_fault'
    native_fault_name = dict(inverter_fault='inverter',overcurrent_fault='overcurrent',
        undervoltage_fault='undervoltage',stall='stalled').get(result['faultKind'])
    selected_fault = lambda row: next((m['faults'] for m in row['motors'] if m['owner']=='ctrl1' and m['id']=='rotor1'), [])
    native_fault_observed = native_fault_name is None or any(native_fault_name in selected_fault(row) for row in after)
    native_latch_preserved = bool(post_attempt) and all('overcurrent' in selected_fault(row) for row in post_attempt)
    expected_marker = dict(button='FAULT DRIVER',inverter_fault='FAULT DRIVER',
        overcurrent_fault='FAULT OVERCURRENT',undervoltage_fault='FAULT UNDERVOLTAGE',stall='FAULT STALL')[result['faultKind']]
    release_contract = (clear_rejected and native_latch_preserved) if sticky_overcurrent else input_cleared
    measurements.update(faultInjectedAt=injected,allInvertersOffAt=min(off_times,default=None),
        allRotorsStoppedAt=min(stop_times,default=None),faultKind=result['faultKind'],
        allInvertersOffLatencySeconds=min(off_times)-injected if off_times else None,
        allRotorsStoppedLatencySeconds=min(stop_times)-injected if stop_times else None,
        clearAttemptAt=attempt['seconds'] if attempt else None,inputCleared=input_cleared,
        clearAttemptDisposition='rejected-native-overcurrent-latch' if sticky_overcurrent and clear_rejected else 'input-cleared' if input_cleared else 'no-successful-clear',
        clearRejection=result.get('faultReleaseRejected'),postClearAttemptObservations=len(post_attempt),
        unprovenOffPostClearAttemptObservations=sum(not off(row) for row in post_attempt),
        directGateConfirmedPostClearAttemptObservations=sum(any(m['control_state']=='fault:inverter' and motor_off(row,m) for m in row['motors']) for row in post_attempt))
    checks.update(airborneBeforeFault=any(row['altitude']>.5 for row in rows if injected-.5 <= row['t'] < injected),
        faultClearAttempted=bool(attempt),faultClearContract=release_contract,
        nativeFaultObserved=native_fault_observed,
        firmwareFaultPath=expected_marker in result['uart']['ctrl1'] and 'LATCHED OFF' in result['uart']['ctrl1']
            and 'FC FAULT DETECTED - ALL ESC DISARM' in result['uart']['fc'],
        allInvertersOff=bool(off_times),allRotorsStopped=bool(stop_times),
        latchAfterClearAttempt=bool(post_attempt) and all(off(row) for row in post_attempt),
        finalRotorsStopped=bool(tail) and all(off(row) and stopped(row) for row in tail),
        groundContact=bool(tail) and all(row['altitude']<=.05 for row in tail))
report = dict(kind='independent-readback-oracle',passed=all(checks.values()),checks=checks,
    measurements=measurements,traceSampleIntervalSeconds=.01,maximumAllowedTraceGapSeconds=.03,
    thresholds=dict(hoverAltitudeM=[.85,1.15],hoverEulerLimitDegrees=hover_angle,hoverDurationSeconds=1,
        recoveryAltitudeM=[.85,1.15],recoveryEulerLimitDegrees=recover_angle,recoveryYawLimitDegrees=5,
        recoveryDurationSeconds=.5,rollLowerDegrees=math.degrees(math.asin(1000/16384)),
        pitchLowerDegrees=math.degrees(math.asin(900/16384)),yawLowerDegrees=8),
    sourceResult=str(result_path),runtime=result['kind'],wasmSha256=next(a['sha256'] for a in result['assets'] if a['name']=='candidate-wasm.wasm'))
out=result_path.with_name(tag+'-oracle.json');out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
sys.exit(0 if report['passed'] else 1)
