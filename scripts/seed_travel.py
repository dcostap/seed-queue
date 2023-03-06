import os
import sys
import modules.scripts as scripts
import gradio as gr
import math
from torchmetrics import StructuralSimilarityIndexMeasure
from torchvision import transforms
import torch
import random
import re
from modules.processing import Processed, process_images, fix_seed
from modules.shared import opts, cmd_opts, state, sd_upscalers
from modules.images import resize_image

__ = lambda key, value=None: opts.data.get(f'customscript/seed_travel.py/txt2img/{key}/value', value)

class Script(scripts.Script):
    def title(self):
        return "Seeds Queue"

    def show(self, is_img2img):
        return True

    def ui(self, is_img2img):
        dest_seed = gr.Textbox(label='Seed(s) (Comma separated)', lines=1)

        return [dest_seed]

    def run(self, p, dest_seed):
        images = []

        # Force Batch Count and Batch Size to 1.
        p.n_iter = 1
        p.batch_size = 1

        # Manual seeds
        seeds = [int(x.strip()) for x in dest_seed.split(",")]

        for seed in seeds:
            if state.interrupted:
                break
            p.seed = seed
            fix_seed(p)
            proc = process_images(p)
            images += proc.images

        return Processed(p, images, p.seed, proc.info)


    def describe(self):
        return "Provide seeds and generate one image for each."
