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
parser.add_argument('--gate', type=float,
                    help='The gps time to plot the closest gate around. '
                         'If omitted, the gate would be chosen randomly.')
parser.add_argument('--gate-number', type=int, default=1,
                    help='Number of gates to be plotted (def=1).')
parser.add_argument('--plot-type', choices=['snr', 'newsnr'], default='snr',
                    help="Which plot to make: an 'snr' or a newsnr' plot.")
parser.add_argument('--output-file')
args = parser.parse_args()

my_dir = os.path.abspath(os.path.dirname(__file__))
out_dir = os.path.join(my_dir, 'output_files/')
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
public_dir = os.path.join('/', os.path.expanduser("~"), 'public_html', 'gating_investigation/', 'several_gates/')

file_ = h5py.File(args.single_trigger_files,"r")
data = file_[file_.keys()[0]]
fig = plt.figure()

auto_time = numpy.array(sorted(list(set(data['gating/auto/time'][:]))))
auto_width = data['gating/auto/width'][:]
auto_pad = data['gating/auto/pad'][:]
times = data['end_time'][:]

if args.gate:
    time_T = abs(auto_time - args.gate)
    T_idx = time_T.argmin()
else:
    T_idx = random.randrange(len(auto_time))

gate_idx = [i for i in xrange(T_idx, T_idx + args.gate_number)]
gate_time = auto_time[gate_idx]

window = args.window
for i in xrange(0, len(gate_time)):
    idx = numpy.logical_and(times < gate_time[i] + window,
                            times > gate_time[i] - window)
    time_plot = times[idx] - gate_time[i]
    width_plot = 0.25
    pad_plot = 0.25
    if args.plot_type == 'snr':
        val = data['snr'][idx]
        plt.yscale('log')
    if args.plot_type == 'newsnr':
        rchisq = data['chisq'][idx] / (2 * data['chisq_dof'][idx] - 2)
        if len(rchisq) > 0:
            val = ranking.newsnr(data['snr'][idx], rchisq)
        else:
            val = numpy.array([])
        del rchisq
    template_duration = data['template_duration'][idx]
    color = template_duration
    csort = (color.argsort())[::-1]
    time_plot = time_plot[csort]
    val = val[csort]
    color = color[csort]

    plt.scatter(time_plot, val, marker='x', c=color, s=16, norm=colors.LogNorm())
plt.xlabel("Time of the gates")
plt.ylabel(args.plot_type)
plt.subplots_adjust(right=0.99)
plt.colorbar(label='template duration')
plt.grid()

if args.output_file:
   out_name = args.output_file
else:
    ifo_name = str(file_.keys()[0])
    gate_name = str("{:.3f}".format(gate_time[0])).replace('.', '-')
    type_name = (args.plot_type).upper()
    out_name = ('%s-GATE-%s-%s' % (ifo_name, gate_name, type_name))
plt.savefig(out_dir + out_name + '.png')
plt.savefig(public_dir + out_name + '.png')

print("Done")

