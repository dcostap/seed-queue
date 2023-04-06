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

        # Add a gradio.HTML component with JavaScript code
        get_seed_button = gr.HTML("""
            <button id="get-seed-button">Get Seed</button>
            <script>
                document.querySelector("#get-seed-button").onclick = function() {
                    var infoDivContent = document.querySelector("#html_info_txt2img").textContent;
                    var seedRegex = /Seed:\s+(\d+)/;
                    var seedMatch = infoDivContent.match(seedRegex);
                    if (seedMatch) {
                        var seed = seedMatch[1];
                        var destSeedInput = document.querySelector('[label="Seed(s) (Comma separated)"] input');
                        if (destSeedInput.value.trim() === "") {
                            destSeedInput.value = seed;
                        } else {
                            destSeedInput.value += ", " + seed;
                        }
                    } else {
                        alert("No seed found in the output viewer.");
                    }
                };
            </script>
        """)

        return [dest_seed, enabled, get_seed_button]

    def run(self, p, dest_seed, enabled):
        if not enabled:
            return None

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
