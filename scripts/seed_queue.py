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

        # Add a gradio.HTML component with a button
        get_seed_button = gr.HTML("""
            <button id="get-seed-button" class="gradio_button svelte-1v6o9pu" onclick="getSeed()">Get Seed</button>
        """)

        seed_prompt_table = gr.Table(
            label='Seed and Prompt Pairs',
            columns=['Seed', 'Prompt', 'Delete'],
            rows=[],
            editable=False
        )

        return [dest_seed, enabled, get_seed_button, seed_prompt_table]

    def run(self, p, enabled, seed_prompt_table):
        if not enabled:
            return None

        images = []

        # Force Batch Count and Batch Size to 1.
        p.n_iter = 1
        p.batch_size = 1

        # Read seed and prompt pairs from the table
        seed_prompt_pairs = seed_prompt_table.get("value", [])

        for seed, prompt, _ in seed_prompt_pairs:
            if state.interrupted:
                break
            p.seed = int(seed)
            # Set the prompt value here, depending on how you plan to use it
            p.prompt = prompt
            fix_seed(p)
            proc = process_images(p)
            images += proc.images

        return Processed(p, images, p.seed, proc.info)



    def describe(self):
        return "Provide seeds and generate one image for each."
