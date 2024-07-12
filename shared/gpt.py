
"""This service creates messages and dispatches them to the discord bot.
"""

import os
import random
import shared.settings as settings

from shared.nano_gpt.trainer import setup_model,train_gpt_model
from shared.nano_gpt.generator import generate_text_from_gpt_model

def dir_is_not_empty(path): return os.path.exists(path) and len(os.listdir(path)) > 0

class DuckGPT:
    def __init__(self):
        print("...start loading", settings.model_path)
        self.update(setup_model(
            out_dir=settings.model_path,
            device='cuda',
            init_from="resume" if dir_is_not_empty(
                settings.model_path
            ) else "gpt2",
        ))
        print("...done loading", settings.model_path)

    def update(self,state):
        m,m_args,iter_num,best_val_loss,chkpt,scaler,optimizer=state
        self.model = m
        self.model_args = m_args
        self.iter_num = iter_num
        self.best_val_loss = best_val_loss
        self.checkpoint =chkpt
        self.scaler = scaler
        self.optimizer = optimizer
        return self

    def generate(self,priors):
        print("...... START MESSAGE GEN ......")
        print(".......context................")
        print(priors)

        generated_text=generate_text_from_gpt_model(
            model=self.model,
            seed=random.randint(1,1024),
            temperature=0.7,
            device='cuda',
            start=priors,
            max_new_tokens=2000,
        )[0]

        print("generated_text:")
        print(generated_text)

        return generated_text

    def train(self,input_data):
        print("......START TRAINING //////////////////////////////////")

        self.update(train_gpt_model(
            model=self.model,
            iter_num=self.iter_num,
            best_val_loss=self.best_val_loss,
            checkpoint=self.checkpoint,
            scaler=self.scaler,
            optimizer=self.optimizer,
            model_args=self.model_args,
            always_save_checkpoint=True,
            learning_rate=1e-9,
            min_lr=6e-12,
            out_dir=settings.model_path,
            input_data=input_data,
            warmup_iters=0,
            grad_clip=1,
            max_iters=1
        ))
        print("......END TRAINING ////////////////////////////////////")
