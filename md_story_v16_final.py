# ==========================================================================================
# ------------------------- [ MD INDUSTRIES: STORY ENGINE V16 ] ----------------------------
# ==========================================================================================
# Developed by: M.DHANESVARAN & SRI RAM. G
# SRM Institute of Science and Technology - Trichy
#
# FEATURES:
# 1. Thread Synchronization (Explicit Sequential Completion via Thread.join())
# 2. Hardware-Aware Active Governance (Sequential VRAM Unloading & offloading)
# 3. Dynamic Manual User Navigation
# 4. Hierarchical Data Serialization (Subfolder Image Organization)
# 5. SDXL Turbo Image Cohesion Fix (Anti-Pattern Parameters)
# ==========================================================================================

import os
import subprocess
import re
import sys
import time
import threading
import datetime

# ==========================================================================================
# ------------------------------ [ LIBRARY VALIDATION ] ------------------------------------
# ==========================================================================================

try:
    import psutil
    import torch
    from diffusers import StableDiffusionXLPipeline
except ImportError:
    print("\n[SYSTEM ERROR] Missing required libraries.")
    print("Please run: pip install psutil torch diffusers transformers accelerate")
    sys.exit(1)

# ==========================================================================================
# ------------------------------ [ VISUAL ASSETS & CONFIG ] --------------------------------
# ==========================================================================================

WIPE_SPEED = 0.01 
HEADER_HEIGHT = 0 
SDXL_MODEL_PATH = "sd_xl_turbo_1.0_fp16.safetensors"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def retro_wipe_up():
    try:
        rows = os.get_terminal_size().lines
        lines_to_erase = rows - HEADER_HEIGHT
        
        if lines_to_erase > 0:
            sys.stdout.write(f"\033[{rows};1H")
            for _ in range(lines_to_erase):
                sys.stdout.write("\033[1A")
                sys.stdout.write("\033[2K")
                sys.stdout.flush()
                time.sleep(WIPE_SPEED)
    except:
        pass

# ==========================================================================================
# ----------------------------- [ HARDWARE TELEMETRY ] -------------------------------------
# ==========================================================================================

def get_cpu_temp():
    try:
        cmd = "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace \"root/wmi\" | Select -ExpandProperty CurrentTemperature"
        output = subprocess.check_output(["powershell", "-Command", cmd], creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        kelvin = int(output) / 10
        celsius = kelvin - 273.15
        return f"{int(celsius)}C"
    except:
        return "N/A"

def get_gpu_stats():
    try:
        cmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        util, mem_used, mem_total, temp = output.split(',')
        mem_used_gb = float(mem_used.strip()) / 1024
        mem_total_gb = float(mem_total.strip()) / 1024
        
        return {
            "util": f"{util.strip()}%",
            "vram": f"{mem_used_gb:.2f}GB / {mem_total_gb:.2f}GB",
            "temp": f"{temp.strip()}C"
        }
    except:
        return {"util": "N/A", "vram": "N/A", "temp": "N/A"}

def print_banner_with_stats():
    global HEADER_HEIGHT
    clear_screen()
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    
    banner = r"""
  ███╗   ███╗██████╗     ██╗███╗   ██╗██████╗ ██╗   ██╗███████╗████████╗██████╗ ██╗███████╗███████╗
  ████╗ ████║██╔══██╗    ██║████╗  ██║██╔══██╗██║   ██║██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝██╔════╝
  ██╔████╔██║██║  ██║    ██║██╔██╗ ██║██║  ██║██║   ██║███████╗   ██║   ██████╔╝██║█████╗  ███████╗
  ██║╚██╔╝██║██║  ██║    ██║██║╚██╗██║██║  ██║██║   ██║╚════██║   ██║   ██╔══██╗██║██╔══╝  ╚════██║
  ██║ ╚═╝ ██║██████╔╝    ██║██║ ╚████║██████╔╝╚██████╔╝███████║   ██║   ██║  ██║██║███████╗███████║
  ╚═╝     ╚═╝╚═════╝     ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝
    """
    print("\033[96m" + banner + "\033[0m") 
    print("  " + "="*85)
    print("  Developed by: \033[93mM.DHANESVARAN & SRI RAM. G\033[0m")
    print("  SRM Institute of science and Technology - Trichy")
    print("  " + "="*85)

    cpu_usage = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    ram_used = round(ram.used / (1024**3), 2)
    ram_total = round(ram.total / (1024**3), 2)
    gpu = get_gpu_stats()
    cpu_temp = get_cpu_temp()
    
    print(f"\n  [SYSTEM TELEMETRY]" + " "*55 + f"[{current_time}]")
    print(f"  CPU Load : {cpu_usage}%".ljust(30) + f"|  RAM  : {ram_used}GB / {ram_total}GB")
    print(f"  GPU Load : {gpu['util']}".ljust(30) + f"|  VRAM : {gpu['vram']}")
    print(f"  THERMALS : CPU: {cpu_temp}  |  GPU: {gpu['temp']}  |  MOBO: N/A")
    print("\n  " + ":"*85) 
    HEADER_HEIGHT = 20 

# ==========================================================================================
# ------------------------ [ ANIMATION & STOPWATCH ENGINE ] --------------------------------
# ==========================================================================================

class ProcessingAnimation(threading.Thread):
    def __init__(self, mode="LLM"):
        super().__init__()
        self.stop_anim = False
        self.start_time = time.time()
        self.mode = mode 
        
    def run(self):
        distance = 15
        bullets = [] 
        frame = 0
        print("") 
        
        while not self.stop_anim:
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(elapsed, 60)
            timer_str = f"{int(minutes):02}:{int(seconds):02}"
            
            frame += 1
            if frame % 3 == 0: bullets.append(10) 
            bullets = [b + 2 for b in bullets if b < distance + 10]
            
            scene = [" "] * 35
            for b in bullets:
                if 0 <= b < 35: scene[b] = "="
            bullet_stream = "".join(scene)
            
            wiggle = frame % 2
            padding = " " * wiggle
            
            if self.mode == "LLM":
                render_line = f"\r  [ TEXT GEN: \033[93m{timer_str}\033[0m ]   {padding}[POLICE] {bullet_stream} [>o<]   "
            else:
                render_line = f"\r  [ IMAGE GEN: \033[96m{timer_str}\033[0m ]  {padding}[SDXL] {bullet_stream} [IMAGE] "
            
            sys.stdout.write(render_line)
            sys.stdout.flush()
            time.sleep(0.1)
        
        sys.stdout.write("\r" + " "*85 + "\r")

    def stop(self):
        self.stop_anim = True

# ==========================================================================================
# ------------------------------ [ SYSTEM UTILITIES ] --------------------------------------
# ==========================================================================================

def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def clean_filename(name):
    return re.sub(r'[^a-zA-Z0-9]', '_', name)

def get_installed_models():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.check_output(["ollama", "list"], encoding="utf-8", startupinfo=startupinfo)
        lines = result.strip().split('\n')
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except:
        return []

def unload_model(model_name):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(["ollama", "stop", model_name], check=False, startupinfo=startupinfo)
        return True
    except:
        return False

def create_organized_paths(base_dir, char_name):
    date_str = datetime.datetime.now().strftime("%d_%m_%Y")
    safe_char = clean_filename(char_name)
    path = os.path.join(base_dir, "main_prompt", f"md_story_{date_str}", f"{safe_char}_{date_str}", safe_char)
    os.makedirs(path, exist_ok=True)
    return path

def extract_image_prompts(story_filepath):
    prompts = []
    try:
        with open(story_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if "**Illustration Prompt:**" in line:
                    clean_prompt = line.replace("**Illustration Prompt:**", "").strip()
                    if clean_prompt:
                        prompts.append(clean_prompt)
    except Exception as e:
        print(f"\n  [WARNING] Failed to extract prompts: {e}")
    return prompts

# ==========================================================================================
# ---------------------------- [ PHASE 2 WORKER THREAD ] ------------------------------------
# ==========================================================================================

class ImageGenWorker(threading.Thread):
    def __init__(self, prompts, output_folder, safe_char):
        super().__init__()
        self.prompts = prompts
        self.output_folder = output_folder
        self.safe_char = safe_char
        self.is_finished = False

    def run(self):
        print("\n  [SYSTEM] Initializing SDXL Turbo Engine...")
        print("  [WARNING] High VRAM Usage Imminent. Activating GPU Core...")
        
        try:
            self.pipe = StableDiffusionXLPipeline.from_single_file(
                SDXL_MODEL_PATH, 
                torch_dtype=torch.float16, 
                variant="fp16"
            )
            
            self.pipe.enable_model_cpu_offload()
            print("  [SUCCESS] SDXL Turbo Loaded with offloading. [HW STATUS: SAFE]")
            
            self.anim_thread = ProcessingAnimation(mode="IMAGE")
            self.anim_thread.start()

            # [V16 NEW] Create the dedicated illustrations subfolder
            illustrations_dir = os.path.join(self.output_folder, "illustrations")
            os.makedirs(illustrations_dir, exist_ok=True)

            for idx, prompt in enumerate(self.prompts):
                # [V16 NEW] Adjusted parameters to prevent the "mosaic/pattern" hallucination
                # 4 steps and 1.5 guidance forces it to focus on a central character subject
                image = self.pipe(prompt=prompt, num_inference_steps=4, guidance_scale=1.5).images[0]
                
                # [V16 NEW] Save the image inside the new subfolder instead of the root
                img_filename = f"{self.safe_char}_Page_{idx+1}.png"
                img_path = os.path.join(illustrations_dir, img_filename)
                image.save(img_path)

            self.anim_thread.stop()
            self.anim_thread.join()

            print(f"\n  [SUCCESS] {len(self.prompts)} Images Generated & Saved to /illustrations!")

        except Exception as e:
            print(f"\n  [SDXL ERROR] {e}")
            print("  [HINT] Ensure 'sd_xl_turbo_1.0_fp16.safetensors' is in the project folder.")
        finally:
            print("  [SYSTEM] Flushing SDXL from VRAM...")
            try:
                del self.pipe 
            except:
                pass
            torch.cuda.empty_cache() 
            print("  [SYSTEM] VRAM Cleared. GPU Idle. [HW STATUS: SAFE]")
            self.is_finished = True

def generate_sdxl_images(prompts, output_folder, safe_char):
    if not prompts:
        print("  [SYSTEM] No valid image prompts found in the story text.")
        return

    sdxl_worker = ImageGenWorker(prompts, output_folder, safe_char)
    sdxl_worker.start()
    sdxl_worker.join() 
    print("  [SUCCESS] Phase 2: Sequential Workflow Finalized.")

# ==========================================================================================
# ---------------------------- [ MAIN REBOOT ENGINE ] --------------------------------------
# ==========================================================================================

def manual_stop_timer():
    print("\n  " + "="*85)
    print("  \033[92m[GENERATION PIPELINE COMPLETE]\033[0m")
    print("  Outputs finalized. View directories and serialized assets.")
    print("  " + "="*85)
    print("\n  Press \033[93m[ENTER]\033[0m to return to Main Menu & generate a new Story...")
    try:
        input() 
        print("  [SYSTEM] Rebooting AI Story Engine...")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n  [MANUAL ABORT] Exiting Software.")
        sys.exit(0)

# ==========================================================================================
# --------------------------------- [ MAIN LOOP ] ------------------------------------------
# ==========================================================================================

def run_software():
    while True:
        try:
            print_banner_with_stats()
            
            current_dir = get_script_directory()
            print(f"  [ENVIRONMENT] {current_dir}")
            print("  Initializing AI Story Engine Core...\n")
            time.sleep(1) 

            models = get_installed_models()
            if not models:
                print("  [CRITICAL ERROR] No Ollama models found.")
                input("  Press Enter to Exit...")
                sys.exit(0)

            print("  [AVAILABLE AI CORES]")
            for i, model in enumerate(models):
                print(f"   [{i+1}] {model}")
            
            choice = input("\n  Select Core (1-{}): ".format(len(models)))
            selected_model = models[int(choice) - 1]
            
            retro_wipe_up() 
            print(f"\n  >> Core Loaded: {selected_model} [HW STATUS: SAFE]")

            print("\n  [STORY CONFIGURATION]")
            page_count = input("   > Page Count (Default 5): ")
            if not page_count.strip() or not page_count.isdigit():
                page_count = "5"
            theme = input("   > Theme: ")
            tone = input("   > Tone: ")
            style = input("   > Art Style: ")
            char_name = input("   > Character Name: ")
            char_desc = input("   > Visual Description: ")

            retro_wipe_up()

            print("\n  [PHASE 1: TEXT GENERATION]")
            
            output_folder = create_organized_paths(current_dir, char_name)
            
            safe_char = clean_filename(char_name)
            safe_model = clean_filename(selected_model.replace(":", "_"))
            
            prompt_filename = f"{safe_char}_prompt.txt"
            story_filename = f"{safe_char}_{safe_model}_story.txt"
            
            prompt_path = os.path.join(output_folder, prompt_filename)
            story_path = os.path.join(output_folder, story_filename)
            
            print(f"   > Output Target: {output_folder}")

            prompt_content = f"""
[INST] You are a professional children's book author.
Your task is to write a personalized bedtime story for a child that is EXACTLY {page_count} pages long.

STORY THEME: {theme}
TONE: {tone}
KEY CHARACTER VISUALS: {char_name} looks like {char_desc}.

IMPORTANT RULES:
1. You MUST write exactly {page_count} pages.
2. STOP immediately after writing "Page {page_count}".
3. Do NOT generate Page {int(page_count) + 1}.

For EACH of the {page_count} pages, use this EXACT format:

### Page [Number]
**Story Text:** [Write 3-4 sentences of the story here.]
**Illustration Prompt:** {char_desc}, {char_name} [action and environment]. Style: {style}.

Go. [/INST]
"""
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_content)

            print(f"   > Sending Data to {selected_model}...")
            
            anim_thread = ProcessingAnimation(mode="LLM")
            anim_thread.start()
            process_start_time = time.time()

            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                with open(story_path, "w", encoding="utf-8") as outfile:
                    with open(prompt_path, "r", encoding="utf-8") as infile:
                        subprocess.run(["ollama", "run", selected_model], stdin=infile, stdout=outfile, check=True, startupinfo=startupinfo)
            finally:
                anim_thread.stop()
                anim_thread.join()
            
            print("\n  [SYSTEM] Phase 1 Governance: Unloading Text Core to free VRAM...")
            unload_model(selected_model)
            print("  [SYSTEM] \033[92mText Core Unloaded.\033[0m [HW STATUS: SAFE]")

            print(f"\n  [PHASE 2: IMAGE GENERATION (SEQUENTIAL PIPELINE)]")
            
            image_prompts = extract_image_prompts(story_path)
            
            if image_prompts:
                print(f"  > Extracted {len(image_prompts)} illustration prompts.")
                generate_sdxl_images(image_prompts, output_folder, safe_char)
            else:
                print("  [ERROR] Sequential failure: Could not extract illustration prompts from text serialized asset.")

            process_end_time = time.time()
            total_time = process_end_time - process_start_time
            minutes, seconds = divmod(total_time, 60)
            time_str = f"{int(minutes)}m {int(seconds)}s"
            
            print(f"  > Outputs Saved: {output_folder}") 
            print("\n  [SYSTEM] Generation pipeline sequential loop complete.")
            
            manual_stop_timer()

        except KeyboardInterrupt:
            print("\n\n  [SYSTEM SHUTDOWN] Goodbye.")
            try:
                unload_model(selected_model) 
            except:
                pass
            sys.exit(0)
        except Exception as e:
            try:
                anim_thread.stop()
            except:
                pass
            print(f"\n\n  [SYSTEM ERROR] {e}")
            input("  Press Enter to Recover...")

if __name__ == "__main__":
    run_software()
