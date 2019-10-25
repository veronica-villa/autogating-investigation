#!/usr/bin/env python
import os
import h5py
import numpy
import random
from pycbc.events import ranking
from matplotlib import use; use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
parser.add_argument('--single-trigger-files',
                    help='The HDF format single detector merged trigger files')
parser.add_argument('--window', type=float, default=1.5,
                    help='Time in seconds around the gate to plot (def=1.5)')
parser.add_argument('--gate',
                    help='The gps time to plot the closest gate around. '
                         'If omitted, the gate would be chosen randomly.'
                         'Other options: 1 plot the first gate in the file'
                                        'all plot all gates')
parser.add_argument('--gate-number', type=int, default=1,
                    help='Number of gates to be plotted (def=1).')
parser.add_argument('--snr-cut', nargs='+',
                    help='Lowest snr/newsnr to be plotted.'
                         '(use: --snr-cut snr/newsnr cut_values)')
parser.add_argument('--log-axis', action='store_true',
                    help='Set y-axis in logaritmic scale.')
parser.add_argument('--output-file')
args = parser.parse_args()

my_dir = os.path.abspath(os.path.dirname(__file__))
out_dir = os.path.join(my_dir, 'output_files/')
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
public_dir = os.path.join('/', os.path.expanduser("~"), 'public_html', 'gating_investigation/', 'gate_histograms/')
print("Reading trigger file...")
file_ = h5py.File(args.single_trigger_files,"r")
data = file_[file_.keys()[0]]
print("Extracting data...")
auto_time = numpy.unique(data['gating/auto/time'][:])
times = data['end_time'][:]
all_true = False
print("Looking for gate...")
if args.gate:
    if args.gate == '1':
        T_idx = 0
    if args.gate == 'all':
        all_true = True
    else:
	if args.gate < min(auto_time) or args.gate > max(auto_time):
            raise RuntimeError('Gate time should be in the interval [%.3f,%.3f]' %(min(auto_time), max(auto_time)))
        time_T = abs(auto_time - float(args.gate))
        T_idx = time_T.argmin()
else:
    T_idx = random.randrange(len(auto_time))

if all_true:
    gate_time = auto_time
    args.gate_number = len(gate_time)
else:
    gate_idx = [i for i in xrange(T_idx, T_idx + args.gate_number)]
    gate_time = auto_time[gate_idx]

if args.snr_cut:
    print("Cutting on SNR...")
    cut_type = args.snr_cut[0]
    cut_values = sorted([float(i) for i in args.snr_cut[1:]])
    if cut_type == 'snr':
        val = data['snr'][:]
    if cut_type == 'newsnr':
        rchisq = data['chisq'][:] / (2 * data['chisq_dof'][:] - 2)
        if len(rchisq) > 0:
            val = ranking.newsnr(data['snr'][:], rchisq)
        else:
            val = numpy.array([])
        del rchisq
else:
    cut_values = str(0)

window = args.window
time_triggers = [[] for i in xrange(len(cut_values))]
print("Starting loop...")
for i in xrange(len(cut_values)):
    if args.snr_cut:
        times = times[val>=cut_values[i]]
        val = val[val>=cut_values[i]]
    for j in xrange(0, len(gate_time)):
        print("Finding indices for gate %d" %j)
        idx = numpy.logical_and(times < gate_time[j] + window,
                                times > gate_time[j] - window)
        print("Finding trigger times")
        time_trigger = times[idx] - gate_time[j]
        time_triggers[i].extend(time_trigger)
    plt.hist(time_triggers[i], bins=numpy.linspace(-window, window, 80),
             label=['%s > %.1f' % (cut_type, cut_values[i]) if args.snr_cut else ''])

if args.log_axis:
        plt.yscale('log')

plt.xlabel('Time relative to the gate (s)')
plt.ylabel('Number of triggers')
plt.title('Histogram of triggers around %s %s' % ('all' if args.gate == 'all' else str(args.gate_number),
                                                  'gate' if args.gate_number == 1 else 'gates'))
if args.snr_cut:
    plt.legend()
if args.output_file:
    out_name = args.output_file
else:
    ifo_name = str(file_.keys()[0])
    gate_name = str("{:.3f}".format(gate_time[0])).replace('.', '-')
    number_name = 'ALL' if args.gate == 'all' else str(args.gate_number)
    window_name = str("{:.1f}".format(window)).replace('.', '-')
    if args.snr_cut:
        cut_name = (cut_type).upper()
        cut_value = '_'.join([str("{:.1f}".format(float(cut_values[i]))).replace('.', '-') for i in xrange(len(cut_values))])
        out_name = ('%s_GATE_%s_%s_%s_NGATES-%s_WINDOW-%s' % (ifo_name, gate_name, cut_name, cut_value, number_name, window_name))
    else:
	out_name = ('%s_GATE_%s_NGATES-%s_WINDOW-%s' % (ifo_name, gate_name, number_name, window_name))
    if args.log_axis:
        out_name = '_'.join([out_name, 'LOG'])
plt.savefig(out_dir + out_name + '.png')
plt.savefig(public_dir + out_name + '.png')

print("Done")

