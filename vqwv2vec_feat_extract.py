import torch
import fairseq
import torchaudio
import sys
import numpy as np
import librosa
from scipy.io import wavfile
if len(sys.argv) != 3:
    raise Exception("two arguments needed")
audio_dir=sys.argv[1]
out_dir=sys.argv[2]

import glob
import os
audio_paths = list(glob.glob(os.path.join(audio_dir,'*/*.wav')))
def load_wav(path):
    sr, x = wavfile.read(path)
    signed_int16_max = 2**15
    if x.dtype == np.int16:
        x = x.astype(np.float32) / signed_int16_max
    print(f'24khz wav {x.shape}')
    if sr != 16000:
        x = librosa.resample(x, sr, 16000)
    print(f'resample {x.shape}')
    x = np.clip(x, -1.0, 1.0)

    return x
def process(_audio_paths, out_dir):
    cp = 'vqw2v/vq-wav2vec_kmeans.pt'
    model, cfg, task = fairseq.checkpoint_utils.load_model_ensemble_and_task([cp])
    model = model[0]
    model.eval()
    for audio_path in _audio_paths:
        wav = load_wav(audio_path)
        #window_size=480
        
        #wav_input_16khz = wav
        #wav_input_16khz = np.pad(wav, pad_width = (window_size//2,window_size//2), mode='reflect')
        #print(f"after pad {wav_input_16khz.shape}")
        
        wav_tensor = torch.FloatTensor(wav).unsqueeze(0)
        z = model.feature_extractor(wav_tensor)
        print(f"z {z.size()}")
        dense, idxs = model.vector_quantizer.forward_idx(z)

        dense = dense[0].data.numpy()
        idxs = idxs[0].data.numpy()
        print(f" dense {dense.shape} idxs {idxs.shape}")
        file_id = os.path.basename(audio_path).split('.')[0]
        spk=os.path.basename(os.path.dirname(audio_path))
        os.makedirs(os.path.join(out_dir,spk), exist_ok = True)
        np.save(os.path.join(out_dir, spk, file_id+'_dense'), dense)
        #np.save(os.path.join(out_dir, spk, file_id+'_idxs'), idxs)

process(audio_paths, out_dir )
