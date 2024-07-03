"""This service creates messages from the model and saves them in mongodb
"""

import os
import random
import datetime


from shared.nano_gpt.generator import generate_text_from_gpt_model
from shared.nano_gpt.trainer import setup_model

from shared.mongodb import discord_message_collection
import shared.settings as settings

from data import ChunkedCollection

def dir_is_not_empty(path): return os.path.exists(path) and len(os.listdir(path)) > 0
service_started=datetime.datetime.utcnow()


print("loading", settings.model_path)
model, model_args, iter_num, best_val_loss, checkpoint, scaler,optimizer=setup_model(
    out_dir=settings.model_path,
    device='cuda',
    init_from="resume" if dir_is_not_empty(settings.model_path) else "gpt2",
)
data = ChunkedCollection(discord_message_collection, 15)

temp=random.uniform(
    float(settings.MIN_TEMP),
    float(settings.MAX_TEMP)
)

print("...... START MESSAGE GEN ......")

message= generate_text_from_gpt_model(
    model=model,
    seed=random.randint(0,99999999),
    temperature=temp,
    device='cuda',
    start=data.last,
    max_new_tokens=2000,
)[0]
print(message)
print("...... END MESSAGE GEN ......")
