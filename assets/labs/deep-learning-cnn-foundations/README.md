# Deep learning CNN foundations lab

This lab explains the first convolutional neural network idea without depending on NumPy or PyTorch. It uses pure Python lists to show how 2D convolution, padding, stride, ReLU, max pooling, and global max features behave on tiny 8x8 images.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=4
TEST_SAMPLES=4
MAJORITY_BASELINE_ACC=0.500
RAW_TEMPLATE_ACC=0.000
CONV_FEATURE_ACC=1.000
SHIFT_GENERALIZATION_GAIN=1.000
VERTICAL_FILTER_RESPONSE_OK=yes
HORIZONTAL_FILTER_RESPONSE_OK=yes
RUN_STATUS=ok
deep_learning_cnn_lab_status=ok
```

## What the experiment does

The training images contain vertical and horizontal bars at positions 1 and 2. The test images contain the same shapes at held-out positions 5 and 6. A raw position-template baseline is tied to where pixels appeared during training, so it fails on this deliberately shifted test set. The convolution feature extractor applies the same vertical/horizontal filters everywhere and then uses max pooling/global max to keep the strongest response, so it recognizes the shifted bars in this toy setting.

Generated reports live under `reports/` after you run the lab:

- `cnn_probe.json`: machine-readable metrics and per-sample feature rows.
- `cnn_report.md`: human-readable explanation table.
- `feature_table.csv`: per-sample predictions and filter responses.

`reports/` is generated evidence and is not committed to the public package.

## Boundary

This is not a real image-recognition benchmark. It proves a mechanism: shared convolution filters plus pooling can detect the same local pattern at a new position. Real CNN training adds learned filters, many channels, losses, optimizers, regularization, and much larger datasets.
