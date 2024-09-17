import os
import argparse

import torch
import scipy.io.wavfile as wavfile
import gradio.processing_utils

from infer import infer, latest_version, get_net_g
from config import config
import utils


model = config.webui_config.model
device = config.webui_config.device


def generate_audio(
    slices,
    sdp_ratio,
    noise_scale,
    noise_scale_w,
    length_scale,
    speaker,
    language,
    reference_audio,
    emotion
):
    with torch.no_grad():
        audio = infer(
            slices,
            reference_audio=reference_audio,
            emotion=emotion,
            sdp_ratio=sdp_ratio,
            noise_scale=noise_scale,
            noise_scale_w=noise_scale_w,
            length_scale=length_scale,
            sid=speaker,
            language=language,
            hps=hps,
            net_g=net_g,
            device=device,
            skip_start=False,
            skip_end=False,
        )
        audio16bit = gradio.processing_utils.convert_to_16_bit_wav(audio)
    return audio16bit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--sdp_ratio', type=float, default=0.2)
    parser.add_argument('--noise_scale', type=float, default=0.6)
    parser.add_argument('--noise_scale_w', type=float, default=0.8)
    parser.add_argument('--length_scale', type=float, default=1)
    parser.add_argument('--speaker', type=str, required=True)
    parser.add_argument('--language', type=str, required=True)
    parser.add_argument('--reference_audio', type=str, default=None)
    parser.add_argument('--emotion', type=int, default=8)
    args = parser.parse_args()
    
    gen_audio_args = {
        'sdp_ratio': args.sdp_ratio,
        'noise_scale': args.noise_scale,
        'noise_scale_w': args.noise_scale_w,
        'length_scale': args.length_scale,
        'speaker': args.speaker,
        'language': args.language,
        'reference_audio': args.reference_audio,
        'emotion': args.emotion
    }
    
    hps = utils.get_hparams_from_file(config.webui_config.config_path)
    version = hps.version if hasattr(hps, 'version') else latest_version
    net_g = get_net_g(model, version, device, hps)
    
    input_dir = args.dataset
    output_dir = f"{args.dataset}_gen"
    os.makedirs(output_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(input_dir):
        lab_files = [file for file in files if file.endswith('.lab')]
        total = len(lab_files)
        for i, lab_file in enumerate(lab_files):
            with open(os.path.join(input_dir, lab_file), 'r', encoding='utf-8') as f:
                text = f.readline()
                print(f'[{i + 1}/{total}] {text}')
                
                gen_audio_args['slices'] = text
            
            output_file = lab_file.replace('.lab', '_f.wav')
            if os.path.exists(os.path.join(output_dir, output_file)):
                print(f'[{i + 1}/{total}] skip {output_file}')
                continue
            
            reference_audio = lab_file.replace('.lab', '.wav')
            gen_audio_args['reference_audio'] = os.path.join(input_dir, reference_audio)
            try:
                output_audio = generate_audio(**gen_audio_args)
            except AssertionError as e:
                print(f'[{i + 1}/{total}] have assertion error: {e}')
                os.remove(os.path.join(input_dir, lab_file))
                os.remove(os.path.join(input_dir, reference_audio))
                print(f'[{i + 1}/{total}] remove {lab_file} and {reference_audio}')
                continue
            wavfile.write(os.path.join(output_dir, output_file), hps.data.sampling_rate, output_audio)
            print(f'[{i + 1}/{total}] save {output_file}')