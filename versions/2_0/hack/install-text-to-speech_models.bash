omz_downloader --name forward-tacotron-duration-prediction --output_dir ./models
omz_downloader --name forward-tacotron-regression --output_dir ./models
omz_downloader --name wavernn-upsampler --output_dir ./models
omz_downloader --name wavernn-rnn --output_dir ./models

omz_converter --name forward_tacotron_duration_prediction --output_dir ./models --precisions FP16
omz_converter --name forward_tacotron_regression --output_dir ./models --precisions FP16
omz_converter --name wavernn_upsampler --output_dir ./models --precisions FP16
omz_converter --name wavernn_rnn --output_dir ./models --precisions FP16
