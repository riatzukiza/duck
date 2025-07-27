 python original_demo.py \
        --input ./input.txt \
        --device CPU \
        -o ./audio.wav \
        --model_duration ./models/public/forward-tacotron/forward-tacotron-duration-prediction/FP16/forward-tacotron-duration-prediction.xml \
        --model_forward ./models/public/forward-tacotron/forward-tacotron-regression/FP16/forward-tacotron-regression.xml \
        --model_upsample ./models/public/wavernn/wavernn-upsampler/FP16/wavernn-upsampler.xml \
        --model_rnn ./models/public/wavernn/wavernn-rnn/FP16/wavernn-rnn.xml
