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

DEFAULT_UPSCALE_METH   = __('Upscaler', 'Lanczos')
DEFAULT_UPSCALE_RATIO  = __('Upscale ratio', 1.0)
CHOICES_UPSCALER  = [x.name for x in sd_upscalers]

seed_travel_substep_min = 0.0001

class Script(scripts.Script):
    def title(self):
        return "Seed travel"

    def show(self, is_img2img):
        return True

    def ui(self, is_img2img):
        seed_travel_extra = []

        dest_seed = gr.Textbox(label='Destination seed(s) (Comma separated)', lines=1)
        with gr.Row():
            rnd_seed = gr.Checkbox(label='Only use Random seeds (Unless comparing paths)', value=False)
            seed_count = gr.Number(label='Number of random seed(s)', value=4)
        compare_paths = gr.Checkbox(label='Compare paths (Separate travels from 1st seed to each destination)', value=False)
        steps = gr.Number(label='Steps (Number of images between each seed)', value=10)
        with gr.Row():
            loopback = gr.Checkbox(label='Loop back to initial seed', value=False)
            ssim_diff = gr.Slider(label='SSIM threshold (0 to disable)', value=0.0, minimum=0.0, maximum=1.0, step=0.01)
        with gr.Row():
            save_video = gr.Checkbox(label='Save results as video', value=True)
            ssim_ccrop = gr.Slider(label='SSIM CenterCrop% (0 to disable)', value=0, minimum=0, maximum=100, step=1)
        with gr.Row():
            video_fps = gr.Number(label='Frames per second', value=30)
            lead_inout = gr.Number(label='Number of frames for lead in/out', value=0)
        with gr.Row():
            upscale_meth  = gr.Dropdown(label='Upscaler',    value=lambda: DEFAULT_UPSCALE_METH, choices=CHOICES_UPSCALER)
            upscale_ratio = gr.Slider(label='Upscale ratio', value=lambda: DEFAULT_UPSCALE_RATIO, minimum=0.0, maximum=8.0, step=0.1)
        bump_seed = gr.Slider(label='Bump seed (If > 0 do a Compare Paths but only one image. No video will be generated.)', value=0.0, minimum=0, maximum=0.5, step=0.001)
        use_cache = gr.Checkbox(label='Use cache', value=True)
        show_images = gr.Checkbox(label='Show generated images in ui', value=True)
        with gr.Row():
            rate = gr.Dropdown(label='Interpolation rate', value='Linear', choices=['Linear', 'Hug-the-middle', 'Slow start', 'Quick start'])
            ratestr = gr.Slider(label='Rate strength', value=3, minimum=0.0, maximum=10.0, step=0.1)
        allowdefsampler = gr.Checkbox(label='Allow the default Euler a Sampling method. (Does not produce good results)', value=False)

        return [rnd_seed, seed_count, dest_seed, steps, rate, ratestr, loopback, save_video, video_fps, show_images, compare_paths,
                allowdefsampler, bump_seed, lead_inout, upscale_meth, upscale_ratio, use_cache, ssim_diff, ssim_ccrop]

    def get_next_sequence_number(path):
        from pathlib import Path
        """
        Determines and returns the next sequence number to use when saving an image in the specified directory.
        The sequence starts at 0.
        """
        result = -1
        dir = Path(path)
        for file in dir.iterdir():
            if not file.is_dir(): continue
            try:
                num = int(file.name)
                if num > result: result = num
            except ValueError:
                pass
        return result + 1

    def run(self, p, rnd_seed, seed_count, dest_seed, steps, rate, ratestr, loopback, save_video, video_fps, show_images, compare_paths,
            allowdefsampler, bump_seed, lead_inout, upscale_meth, upscale_ratio, use_cache, ssim_diff, ssim_ccrop):
        initial_info = None
        images = []
        lead_inout=int(lead_inout)
        tgt_w, tgt_h = round(p.width * upscale_ratio), round(p.height * upscale_ratio)

        # If we are just bumping seeds, ignore compare_paths and save_video
        if bump_seed > 0:
            compare_paths = False
            save_video = False
            steps = 1
            allowdefsampler = True # Since we aren't trying to get to a target seed, this will be ok.

        if not allowdefsampler and p.sampler_name == 'Euler a':
            print(f"You seem to be using Euler a, it will most likely not produce good results.")
            return Processed(p, images, p.seed)

        if rnd_seed and (not seed_count or int(seed_count) < 2):
            print(f"You need at least 2 random seeds.")
            return Processed(p, images, p.seed)

        if not rnd_seed and not dest_seed:
            print(f"No destination seeds were set.")
            return Processed(p, images, p.seed)

        if not save_video and not show_images:
            print(f"Nothing to show in gui. You will find the result in the ouyput folder.")
            #return Processed(p, images, p.seed)

        if save_video:
            import numpy as np
            try:
                import moviepy.video.io.ImageSequenceClip as ImageSequenceClip
            except ImportError:
                print(f"moviepy python module not installed. Will not be able to generate video.")
                return Processed(p, images, p.seed)

        # Remove seeds within () to help testing
        dest_seed = re.sub('\([^)]*\)', ',', dest_seed)
        dest_seed = re.sub(',,*', ',', dest_seed)

        # Custom seed travel saving
        travel_path = os.path.join(p.outpath_samples, "travels")
        os.makedirs(travel_path, exist_ok=True)
        travel_number = Script.get_next_sequence_number(travel_path)
        travel_path = os.path.join(travel_path, f"{travel_number:05}")
        p.outpath_samples = travel_path
        if save_video: os.makedirs(travel_path, exist_ok=True)

        # Force Batch Count and Batch Size to 1.
        p.n_iter = 1
        p.batch_size = 1
        p.seed = int(p.seed)

        initial_prompt = p.prompt
        initial_negative_prompt = p.negative_prompt

        if compare_paths or bump_seed > 0:
            loopback = False

        seeds = []
        # Random seeds
        if rnd_seed == True:
            if (compare_paths or bump_seed) and not p.seed == None:
                seeds.append(p.seed)
            s = 0          
            while (s < seed_count):
                seeds.append(random.randint(0,2147483647))
                #print(seeds)
                s = s + 1
        # Manual seeds        
        else:
            seeds = [] if p.seed == None else [p.seed]
            seeds = seeds + [int(x.strip()) for x in dest_seed.split(",")]
        p.seed = seeds[0]

        if bump_seed > 0:
            p.subseed_strength = bump_seed
            for s in range(len(seeds)-1):
                if state.interrupted:
                    break
                p.subseed = seeds[s+1]
                fix_seed(p)
                proc = process_images(p)
                if initial_info is None:
                    initial_info = proc.info
                images += proc.images
            return Processed(p, images if show_images else [], p.seed, initial_info)

        travel_queue = []
        if compare_paths:
            travel_queue = [[seeds[0], seeds[i+1]] for i in range(len(seeds)-1)]
        else:
            travel_queue = [[seeds[i] for i in range(len(seeds))]]

        generation_queues = []
        for travel in travel_queue:
            generation_queue = []
            for s in range(len(travel) - (0 if loopback else 1)):
                p.seed = travel[s]
                p.subseed = travel[s+1] if s+1 < len(travel) else travel[0]
                fix_seed(p) # replaces None and -1 with random seeds
                seed, subseed = p.seed, p.subseed
                numsteps = int(steps) + (1 if s+1 == len(travel) else 0)
                for i in range(numsteps):
                    strength = float(i/float(steps))

                    # Calculate rate
                    if rate == "Hug-the-middle":
                        strength = strength + (0.1 * math.sin(strength*2*math.pi))
                    elif rate == "Slow start":
                        strength = strength**ratestr
                    elif rate == "Quick start":
                        strength = (1-strength)**ratestr
                    # "Linear" is default (do nothing)

                    key = (seed, subseed, strength)
                    generation_queue.append(key)
            if not loopback: # Kludge to add last image
                key = (subseed, subseed, 0.0)
                generation_queue.append(key)
            generation_queues.append(generation_queue)

        if bump_seed:
            total_images = len(seeds)
        else:
            total_images = len(set(key for queue in generation_queues for key in queue))
        print(f"Generating {total_images} images.")

        # Set generation helpers
        state.job_count = total_images

        # reuse generated images with the same seeds and strength
        image_cache = {}

        for s in range(len(generation_queues)):
            queue = generation_queues[s]
            step_images = []
            step_keys = []
            for key in queue:
                if state.interrupted:
                    break
                p.seed, p.subseed, p.subseed_strength = key
                step_keys += [key]

                # DEBUG
                print(f"Process: {key} of {seeds}")

                # lower seed comes first so equivalent cached images hash the same
                # e.g. strength 0.75 from B to A = strength 0.25 from A to B
                seed0, seed1, strength = key
                if seed1 < seed0:
                    seed0, seed1 = seed1, seed0
                    strength = 1 - strength
                if strength == 0: seed1 = 0 # seed1 does not affect the output when strength is 0
                if strength == 1: seed0 = 0 # seed0 does not affect the output when strength is 1
                cache_key = (seed0, seed1, strength)

                if use_cache and cache_key in image_cache:
                    step_images += image_cache[cache_key]
                    images += image_cache[cache_key]
                    continue

                proc = process_images(p)
                if initial_info is None:
                    initial_info = proc.info

                # upscale - copied from https://github.com/Kahsolt/stable-diffusion-webui-prompt-travel
                if upscale_meth != 'None' and upscale_ratio != 1.0 and upscale_ratio != 0.0:
                    image = [resize_image(0, proc.images[0], tgt_w, tgt_h, upscaler_name=upscale_meth)]
                else:
                    image = [proc.images[0]]

                step_images += image
                images += image
                if use_cache:
                    image_cache[cache_key] = image

            # DEBUG
            print(f"step_keys: {step_keys}")

            # If SSIM > 0 and not bump_seed
            # TODO ssim step_images
            if ssim_diff > 0:
                ssim = StructuralSimilarityIndexMeasure(data_range=1.0)
                # transform = transforms.Compose([transforms.Resize((x/2,y/2)), transforms.ToTensor()])
                if ssim_ccrop == 0:
                    transform = transforms.Compose([transforms.ToTensor()])
                else:
                    transform = transforms.Compose([transforms.CenterCrop(min(tgt_w, tgt_h)*(ssim_ccrop/100)), transforms.ToTensor()])

                check = True
                skip_count = 0

                done = 0
                while(check):
                    if state.interrupted:
                        break
                    check = False
                    for i in range(done, len(step_images)-1):
                        # Check distance between i and i+1

                        a = transform(step_images[i].convert('RGB')).unsqueeze(0)
                        b = transform(step_images[i+1].convert('RGB')).unsqueeze(0)
                        d = ssim(a, b)

                        seed_a, subseed_a, subseed_strength_a = step_keys[i]
                        seed_b, subseed_b, subseed_strength_b = step_keys[i+1]
                        if d < ssim_diff and abs(subseed_strength_b - subseed_strength_a) > seed_travel_substep_min:
                            # DEBUG
                            print(f"SSIM: {step_keys[i]} <-> {step_keys[i+1]} = {d}")

                            # Add image and run check again
                            check = True

                            if subseed_strength_b == 0:
                                subseed_strength_b = 1

                            new_strength = (subseed_strength_a + subseed_strength_b)/2.0

                            #new_strength = (subseed_strength_a + subseed_strength_b)/2.0
                            #key = (from_seed, to_seed, new_strength)

                            key = (seed_a, subseed_a, new_strength)

                            p.seed, p.subseed, p.subseed_strength = key

                            # DEBUG
                            print(f"Process: {key} of {seeds}")
                            proc = process_images(p)

                            if initial_info is None:
                                initial_info = proc.info

                            # upscale - copied from https://github.com/Kahsolt/stable-diffusion-webui-prompt-travel
                            if upscale_meth != 'None' and upscale_ratio != 1.0 and upscale_ratio != 0.0:
                                image = [resize_image(0, proc.images[0], tgt_w, tgt_h, upscaler_name=upscale_meth)]
                            else:
                                image = [proc.images[0]]

                            #images = images[0:i] + [image] + images[i:]
                            # TODO use cache?
                            step_images.insert(i+1, image[0])
                            step_keys.insert(i+1, key)
                            break;
                        else:
                            # DEBUG
                            if abs(subseed_strength_b - subseed_strength_a) <= seed_travel_substep_min:
                                print(f"Reached minimum step limit @{step_keys[i]} (Skipping)   ")
                                skip_count += 1
                            else:
                                if i > done:
                                    print(f"Done: {i} of {len(step_keys)} ({step_keys[i]}) {len(step_keys[i:])} in queue.")
                                    #print(f"Work: {step_keys[i:]}")
                            done = i
                # DEBUG
                print("SSIM done!")
                print(f"Minimum step limits reached: {skip_count}")

            if save_video:
                frames = [np.asarray(step_images[0])] * lead_inout + [np.asarray(t) for t in step_images] + [np.asarray(step_images[-1])] * lead_inout
                clip = ImageSequenceClip.ImageSequenceClip(frames, fps=video_fps)
                filename = f"travel-{travel_number:05}-{s:04}.mp4" if compare_paths else f"travel-{travel_number:05}.mp4"
                clip.write_videofile(os.path.join(travel_path, filename), verbose=False, logger=None)

        return Processed(p, images if show_images else [], p.seed, initial_info)


    def describe(self):
        return "Travel between two (or more) seeds and create a picture at each step."
