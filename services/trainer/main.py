"""This service creates messages from the model and saves them in mongodb
"""

import os
import datetime

from shared.nano_gpt.trainer import setup_model,train_gpt_model

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

print("......START TRAINING ///////////////////////////////////////////////////////////////////")
model, model_args, iter_num, best_val_loss, checkpoint, scaler,optimizer=train_gpt_model(
    model, iter_num, best_val_loss, checkpoint, scaler,optimizer,model_args,
    always_save_checkpoint=True,
    learning_rate=1e-9,
    min_lr=6e-12,
    out_dir=settings.model_path,
    input_data=data.chunks[10:],
    warmup_iters=2,
    grad_clip=1,
    max_iters=5
)
print("......END TRAINING ///////////////////////////////////////////////////////////////////")
