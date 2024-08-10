# -*- coding: utf-8 -*-
""" dataset2wav.py

Example code on how to generate a fixed-augmented query dataset.

• Fixed validation/test set queries were synthesized in this method.
• We can apply different random augmentation every N seconds.
 
"""
from os import path
import os
import glob
import sys
import wavio
import yaml
import numpy as np
from tensorflow.keras.utils import Progbar
#sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from model.dataset import Dataset
from model.utils.dataloader_keras import genUnbalSequence


SNR_RANGE = (10, 10) # fix 0 dB; (0, 10) for random dB in range.
AUG_CHANGE_INTERVAL = 1 # change augmentation method every N secconds.
USE_SPEECH_AUG = False
SOURCE_DIR = 'val-query-db-500-30s/db' #'test-query-db-500-30s/db' 
OUTPUT_ROOT_DIR = '../aug_output/val_10dB'


def load_config(config_fname):
    config_filepath = './config/' + config_fname + '.yaml'
    if path.exists(config_filepath):
        print(f'cli: Configuration from {config_filepath}')
    else:
        sys.exit(
            f'cli: Configuration file {config_filepath} is missing.')

    with open(config_filepath, 'r') as f:
        cfg = yaml.safe_load(f)
    return cfg


def gen_wav(x, fpath, fs=8000):
    wavio.write(fpath, x, fs, sampwidth=2)


def ds_to_wav(ds, n_anchor, output_root_dir, split_output_file=False):
    # Get filename and position info
    file_list = ds.fns_event_seg_list
    #seg_index = ds.fns_event_seg_list[1]

    pb = Progbar(len(ds))
    for i in range(len(ds)):
        X,_ = ds.__getitem__(i) # output is (rep, org) in this mode.. shape(3, 1, 80000)
        pb.add(1)
        if split_output_file:
            # multiple output files for each augmentation
            for j in range(len(X)):
                fpath = file_list[len(X)*i + j][0]
                dirname, fname = path.split(fpath)
                dirname = dirname.split('/')[-1]
                fname = fname.split('.')[0]
                n_seg_idx = file_list[len(X)*i + j][1]
                # destination
                full_path = output_root_dir + '/' + dirname + '/' + fname + \
                    f'_{n_seg_idx:03d}.wav'
                os.makedirs(output_root_dir + '/' + dirname, exist_ok=True)
                gen_wav(X[j].squeeze(), full_path)
        else:
            # single output file for each source
            bsz = len(X)
            X = X.reshape(-1)
            assert len(X)==8000*30
            src_fp = ds.fns_event_seg_list[bsz * i][0]
            sub_dir, fname = src_fp.split('/')[-2:]
            # destination
            full_path = output_root_dir + '/' + sub_dir + '/' + fname
            os.makedirs(output_root_dir + '/' + sub_dir, exist_ok=True)
            gen_wav(X, full_path)


""" main """
cfg = load_config('640_lamb') # Just for dataset location info
dataset = Dataset(cfg)

source_dir = cfg['DIR']['SOURCE_ROOT_DIR'] + SOURCE_DIR
bg_dir = cfg['DIR']['BG_ROOT_DIR']
ir_dir = cfg['DIR']['IR_ROOT_DIR']
speech_dir = cfg['DIR']['SPEECH_ROOT_DIR']


source_fps = sorted(glob.glob(source_dir + '/**/*.wav', recursive=True))
#assert len(source_fps)==500 # 500 songs with 30s ech

# build dataset
if USE_SPEECH_AUG:
    speech_mix_parameter = [True, dataset.ts_speech_fps, SNR_RANGE]
else:
    speech_mix_parameter = [False]
    
offset_margin_hop = 0.2 / AUG_CHANGE_INTERVAL
assert (30 / AUG_CHANGE_INTERVAL) == int(30 / AUG_CHANGE_INTERVAL)
n_anchor = int(30 / AUG_CHANGE_INTERVAL)
bsz = int(2 * n_anchor)
    
ds = genUnbalSequence(
    source_fps,
    bsz=bsz, # actually we use 3 replicas only
    n_anchor=n_anchor, # each batch has one 30s song
    duration=AUG_CHANGE_INTERVAL,
    hop=AUG_CHANGE_INTERVAL, # each 1 sec with no overlap
    shuffle=False,
    random_offset_anchor=False,
    offset_margin_hop_rate=0.2, # hop* rate = 200ms; we apply offset modulation here.
    bg_mix_parameter=[True, dataset.ts_bg_fps, SNR_RANGE],
    ir_mix_parameter=[True, dataset.ts_ir_fps],
    speech_mix_parameter=speech_mix_parameter,
    reduce_batch_first_half=True) # <--- output will be (rep, empty) instead of (org, rep)

# Augmented dataset to wav
ds_to_wav(ds, ds.n_anchor, OUTPUT_ROOT_DIR)
