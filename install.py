import os
import shutil

volume = '/data'
model_file = '/whisper.cpp/base.en'
if os.path.exists(model_file):
    shutil.move(model_file, volume)