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
        return not is_img2img

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label='Enabled', value=False)

        style_html = """
        display: inline-block;
        padding: 5px 17px;
        border: 1px solid #ccc;
        background-color: #c7c7c7;
        color: #000;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        font-weight: bold;
        border-radius: 5px;
"""

        get_seed_button = gr.HTML(f"""
            <button id="get-seed-button" class="lg secondary gradio-button" onclick="storeCurrentPreviewInfo()" style="{style_html}">Store current image info</button>
        """)

        seed_list = gr.HTML('<ul id="seed_list"></ul>')

        delete_seed_button = gr.HTML(f"""
            <button id="delete-seed-button" class="lg secondary gradio-button" onclick="deleteSeed()" style="{style_html}">Delete Seed</button>
        """)

        delete_all_seeds_button = gr.HTML(f"""
            <button id="delete-all-seeds-button" class="lg secondary gradio-button" onclick="deleteAllSeeds()" style="{style_html}">Delete All Seeds</button>
        """)


        # hack: this textbox will contain the raw json representing the stored seed & prompt pairs. It's modified / updated in javascript code
        hidden_prompt_seed_pairs_input = gr.Textbox(elem_id="hidden_prompt_seed_pairs_input", label="stored preview", lines=3, max_lines=8, interactive=False)

        return [enabled, hidden_prompt_seed_pairs_input]


    def run(self, p, enabled, hidden_prompt_seed_pairs_input):
        if not enabled:
            return None

        # hack: i surround the contents of the textbox with <json> so that here, when gradio sends back the contents, it actually works
        # otherwise since the text contents are pure json gradio sends back empty / None for some reason
        hidden_prompt_seed_pairs_input = hidden_prompt_seed_pairs_input.replace("<json>", "")

        import json
        # Parse hidden_prompt_seed_pairs_input and retrieve the seeds and prompts
        seed_prompt_pairs = json.loads(hidden_prompt_seed_pairs_input)
        seeds = [int(pair["seed"]) for pair in seed_prompt_pairs]
        prompts = [pair["prompt"] for pair in seed_prompt_pairs]

        p.n_iter = len(seeds)
        p.batch_size = 1

        p.do_not_save_grid = True

        # Generate images for each seed and prompt
        p.seed = [seed for seed in seeds]
        p.prompt = [prompt for prompt in prompts]
        return process_images(p)


    def describe(self):
        return "Provide seeds and generate one image for each."
