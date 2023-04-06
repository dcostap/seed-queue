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

        get_seed_button = gr.HTML("""
            <button id="get-seed-button" class="lg secondary gradio-button" onclick="storeCurrentPreviewInfo()">Store current image info</button>
        """)

        seed_list = gr.HTML('<ul id="seed_list"></ul>')

        delete_seed_button = gr.HTML("""
            <button id="delete-seed-button" class="lg secondary gradio-button" onclick="deleteSeed()">Delete Seed</button>
        """)

        delete_all_seeds_button = gr.HTML("""
            <button id="delete-all-seeds-button" class="lg secondary gradio-button" onclick="deleteAllSeeds()">Delete All Seeds</button>
        """)

        hidden_prompt_seed_pairs_input = gr.Textbox(elem_id="hidden_prompt_seed_pairs_input", label="stored preview", lines=5)

        return [enabled, hidden_prompt_seed_pairs_input]


    def run(self, p, enabled, hidden_prompt_seed_pairs_input):
        if not enabled:
            return None

        hidden_prompt_seed_pairs_input = hidden_prompt_seed_pairs_input.replace("<json>", "")

        print("hidden_prompt_seed_pairs_input: " + hidden_prompt_seed_pairs_input)

        images = []

        # Force Batch Count and Batch Size to 1.
        p.n_iter = 1
        p.batch_size = 1

        import json
        # Parse hidden_prompt_seed_pairs_input and retrieve the seeds and prompts
        seedPromptPairs = json.loads(hidden_prompt_seed_pairs_input)
        seeds = [int(pair["seed"]) for pair in seedPromptPairs]
        prompts = [pair["prompt"] for pair in seedPromptPairs]

        # Generate images for each seed and prompt
        for seed, prompt in zip(seeds, prompts):
            if state.interrupted:
                break
            p.seed = seed
            p.prompt = prompt
            fix_seed(p)
            proc = process_images(p)
            images += proc.images


        return Processed(p, images, p.seed, proc.info)


    def describe(self):
        return "Provide seeds and generate one image for each."
