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
        enabled = gr.Checkbox(label='Enabled', value=False)
        with gr.Row():
            dest_seed = gr.Textbox(label='Seed(s) (Comma separated)', lines=1)

        get_seed_button = gr.HTML("""
            <button id="get-seed-button" class="gradio_button svelte-1v6o9pu" onclick="getSeed()">Get Seed</button>
        """)

        seed_list = gr.HTML('<ul id="seed_list"></ul>')

        delete_seed_button = gr.HTML("""
            <button id="delete-seed-button" class="gradio_button svelte-1v6o9pu" onclick="deleteSeed()">Delete Seed</button>
        """)

        delete_all_seeds_button = gr.HTML("""
            <button id="delete-all-seeds-button" class="gradio_button svelte-1v6o9pu" onclick="deleteAllSeeds()">Delete All Seeds</button>
        """)

        hidden_prompt_seed_pairs_input = gr.Textbox(elem_id="hidden_prompt_seed_pairs_input", label="", style={"display": "none"})

        return [dest_seed, enabled, hidden_prompt_seed_pairs_input]


    def run(self, p, enabled, hidden_prompt_seed_pairs_input):
        if not enabled:
            return None

        images = []

        # Force Batch Count and Batch Size to 1.
        p.n_iter = 1
        p.batch_size = 1

        # TODO: PARSE hidden_prompt_seed_pairs_input and retrieve the seeds into dest_seed, and each seed prompt into another variable
        dest_seed = "1000, 1001"
        #####

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
