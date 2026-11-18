#!/usr/bin/env python3
"""Original 16-bar, 128 BPM electronic/chiptune cue; no samples or external media."""
from pathlib import Path
import json
import argparse
import wave
import numpy as np
from scipy.signal import butter, sosfilt

parser = argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
OUT = parser.parse_args().output_dir.resolve()
OUT.mkdir(parents=True,exist_ok=True)
SR, BPM, SECONDS = 48000, 128, 30.0
BEAT = 60.0 / BPM
N = round(SR * SECONDS)
RNG = np.random.default_rng(2211)
mix = np.zeros((N, 2), dtype=np.float64)
lead = np.zeros_like(mix)

def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)

def add(dst, sound, when, gain=1.0, pan=0.0):
    start = round(when * SR)
    if start >= N:
        return
    sound = sound[:N-start] * gain
    theta = (pan + 1.0) * np.pi / 4.0
    dst[start:start+len(sound), 0] += sound * np.cos(theta)
    dst[start:start+len(sound), 1] += sound * np.sin(theta)

def env(n, attack=.004, decay=.035, sustain=.60, release=.060):
    t = np.arange(n) / SR
    dur = n / SR
    out = np.minimum(t / max(attack, 1/SR), 1.0)
    out *= sustain + (1.0 - sustain) * np.exp(-np.maximum(t-attack, 0) / decay)
    out *= np.minimum(np.maximum(dur-t, 0) / release, 1.0)
    return out

def note(midi, dur, kind="lead"):
    t = np.arange(round(dur*SR)) / SR
    f = hz(midi)
    if kind == "bass":
        s = np.sin(2*np.pi*f*t) + .24*np.sin(2*np.pi*2*f*t) + .08*np.sin(2*np.pi*3*f*t)
        return np.tanh(1.2*s) * env(len(t), .003, .05, .80, .035)
    if kind == "pad":
        s = np.sin(2*np.pi*f*t) + .18*np.sin(2*np.pi*f*1.003*t) + .08*np.sin(2*np.pi*3*f*t)
        return s * env(len(t), .1, .45, .65, .24)
    # A rounded pulse timbre: harmonic amplitudes fall faster than a square wave.
    s = np.sin(2*np.pi*f*t)
    for k, amp in [(2,.07),(3,.21),(5,.07),(7,.025)]:
        s += amp*np.sin(2*np.pi*f*k*t)
    return s * env(len(t))

def kick():
    t = np.arange(round(.26*SR)) / SR
    freq = 47 + 101*np.exp(-t/.022)
    phase = 2*np.pi*np.cumsum(freq)/SR
    tone = np.sin(phase) * np.exp(-t/.073)
    click = RNG.normal(0,1,len(t)) * np.exp(-t/.0028) * .055
    return (tone+click) * np.minimum(t/.001,1)

def snare():
    t = np.arange(round(.17*SR)) / SR
    noise = RNG.normal(0,1,len(t))
    noise = sosfilt(butter(2,[850,6500],btype='bandpass',fs=SR,output='sos'),noise)
    s = .7*noise*np.exp(-t/.035) + .22*np.sin(2*np.pi*180*t)*np.exp(-t/.035)
    return s*np.minimum(t/.001,1)

def hat(opened=False):
    dur = .11 if opened else .045
    t = np.arange(round(dur*SR)) / SR
    noise = sosfilt(butter(2,[4800,10000],btype='bandpass',fs=SR,output='sos'),RNG.normal(0,1,len(t)))
    return noise*np.exp(-t/(.027 if opened else .012))*np.minimum(t/.001,1)

# Original melody, with sparse repeated motifs and a tonic resolution.
chords = [
    (45,[0,3,7],[12,19,15,17,19,24,22,19]),
    (41,[0,4,7],[12,19,16,14,19,21,19,16]),
    (48,[0,4,7],[12,19,16,19,24,23,19,16]),
    (43,[0,4,7],[12,19,16,14,19,21,19,14]),
]
for bar in range(16):
    base = bar * 4*BEAT
    root, intervals, melody = chords[bar % 4]
    if bar == 15:
        root, intervals, melody = chords[0]
    for i, iv in enumerate(intervals):
        add(mix,note(root+24+iv,4*BEAT+.16,"pad"),base,.037,[-.5,0,.5][i])
    # Half-beat bass rhythm leaves space for the lead and the interface clicks.
    for beat, iv in [(0,0),(.75,0),(1.5,7),(2,0),(2.75,12),(3.5,7)]:
        if bar==15 and beat>2:
            continue
        add(mix,note(root,.30 if beat%1==0 else .18,"bass"),base+beat*BEAT,.27)
    for beat in [0,1,2,3]:
        if bar==15 and beat>2:
            continue
        add(mix,kick(),base+beat*BEAT,.40)
    for beat in [1,3]:
        if bar==15 and beat==3:
            continue
        add(mix,snare(),base+beat*BEAT,.22,-.03)
    for step in range(8):
        if bar==15 and step>4:
            continue
        add(mix,hat(opened=bar>=10 and step==7),base+step*.5*BEAT,.072 if step%2 else .045,.22 if step%2 else -.17)
    # Start with a memorable six-note phrase; fuller pattern begins at bar 6 (~9.4s).
    active = [0,1,2,4,5,7] if bar<5 else list(range(8))
    if bar==15:
        active=[0,2,4]
        melody=[12,0,19,0,24,0,0,0]
    for step in active:
        duration = (.82 if bar==15 and step==4 else (.20 if step not in [2,7] else .29))
        add(lead,note(root+12+melody[step],duration),base+step*.5*BEAT,.115 if bar<10 else .132,.10*np.sin(bar))
    # Soft offbeat high arpeggios give a lift near 20s, without a harsh riser.
    if 10 <= bar < 15:
        for step in [1,3,5,7]:
            iv=intervals[(step//2)%3]
            add(mix,note(root+36+iv,.13),base+step*.5*BEAT,.032,-.30 if step%4==1 else .30)

mix += lead
for delay, gain in [(BEAT/2,.16),(BEAT,.08)]:
    k=round(delay*SR)
    mix[k:,0] += lead[:-k,1]*gain
    mix[k:,1] += lead[:-k,0]*gain
# Tame the high end, remove DC, and avoid hard clipping.
mix = sosfilt(butter(2,11500,fs=SR,output='sos'),mix,axis=0)
mix = sosfilt(butter(2,30,btype='highpass',fs=SR,output='sos'),mix,axis=0)
mix = np.tanh(mix*.95)
fadein=round(.012*SR); fadeout=round(.36*SR)
mix[:fadein] *= np.linspace(0,1,fadein)[:,None]
mix[-fadeout:] *= np.linspace(1,0,fadeout)[:,None]
mix *= .71 / np.max(np.abs(mix))
pcm = np.round(np.clip(mix + RNG.uniform(-.5/32768,.5/32768,mix.shape),-1,1)*32767).astype('<i2')
path=OUT/'wire-runner-original-30s.wav'
with wave.open(str(path),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
stats={"duration_seconds":SECONDS,"sample_rate":SR,"channels":2,"bpm":BPM,"bars":16,"sample_peak_dbfs":float(20*np.log10(np.max(np.abs(mix)))),"rms_dbfs":float(20*np.log10(np.sqrt(np.mean(mix**2)))),"provenance":"Original melody and synthesis in make_soundtrack.py; no samples, no external media."}
(OUT/'audio-stats.json').write_text(json.dumps(stats,indent=2)+'\n')
print(json.dumps({"file":str(path),**stats}))
