# TDMS Scaler Reader

A fast reader for scaler channels for TDMS files.

## Installation

    pip install -r requirements.txt

## Usage

    python3 tdms_scaler_reader.py -c 5 -o . -n example ./PATH/TO/SCALER/DATA/*.tdms

Options:

* `-o`: output file path, default is PWD
* `-n`: output file name, default is "results"
* `-c`: which channel, default is 5

## Accessing data

The resulting file will be a compressed numpy file (`npz`) containing two arrays: frequency and time. You can access them like this:

    import numpy as np
    import matplotlib.pyplot as plt
    d = np.load('example.npz')
    plt.plot(d['t'], d['f'])


## Explanation of the method

Creating difference between adjacent elements are done using `np.diff`. But, how about non adjacent elements?
Imagine you have the array and the indexs of it:

| Index | Array Values |
|:-----:|:-----------:|
|   0   |      2      |
|   1   |      1      |
|   2   |      2      |
|   3   |      3      |
|   4   |      4      |
|   5   |      7      |
|   6   |      8      |
|   7   |      8      |
|   8   |      6      |
|   9   |      5      |
|   10  |      4      |
|   11  |      1      |


These are 12 values, i.e. indexes from 0 to 11. You are interested in getting a `diff` of every 4 elements, so from 12 values, you will have only 12/4 (three) values left by subtracting:

- index 3 minus index 0 --> 3-2 = 1
- index 7 minus index 4 --> 8-4 = 4
- index 11 minus index 8 --> 1-6 = -5

so you shift the original array by -3, subtract from itself:


| Index | Shifted Array Values | Array Values |  Diference  |
|:-----:|:--------------------:|:------------:|:-----------:|
|   0   |           3          |       2      |      1      |
|   1   |           4          |       1      |      3      |
|   2   |           7          |       2      |      5      |
|   3   |           8          |       3      |      5      |
|   4   |           8          |       4      |      4      |
|   5   |           6          |       7      |     -1      |
|   6   |           5          |       8      |     -3      |
|   7   |           4          |       8      |     -4      |
|   8   |           1          |       6      |     -5      |
|   9   |           2          |       5      |     -3      |
|   10  |           1          |       4      |     -3      |
|   11  |           2          |       1      |      1      |


you see this is exactly what you want, only it contains more points than needed. You only need every 4th element using usual slicing `[start:stop:step]`system, like `[::4]`, resulting in the first, middle and the last one which is what we want.

```
(a[3:]-a[:-3])[::4]
--> array([ 1,  4, -5])
```
Visually:
```
   |----------| (shifted array)
|----------|    (original array)
   |-------|    (difference)
   x   x   x    (values taken at indexes: 0,4,8)
```   
In the case of TDMS scaler files we do the same. Since we have a time stamp and 1024 count points follow. So in case of 256 time stamps. `delta_t` is calculated using `np.diff` directly, since `TimeDelta64` elements are adjacent. In between those time stamps, the counter counts up, every time there is a pulse on the scaler. So to determine the number of counts in each section, the count difference between the value directly on top of the time stamp, and the last value just before the next time stamp. e.g.: value at index 1023 - value at index 0, value at index 2047 - value at index 1024 and so on. This is achieved by the method above for `delta_cnt` and results again in 256 values. Then `delta_cnt / delta_t` gives us a value in frequency `[Hz]`. The time stamp values are aligned to the left of 1024 data points, so the last bin must be left out.
