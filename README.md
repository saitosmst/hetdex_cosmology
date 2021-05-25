# HETDEX Cosmology SWG: LAE clsuering analysis
> Summary description here.


This file will become your README and also the index of your documentation.

## Install

`pip install your_project_name`

## How to use

Fill me in please! Don't forget code examples:

```python
import numpy as np

print('running test...')
fg = Field_on_grid(Lbox=[1000., 1000., 1000.], Ngrid=128)
print('  Nyquist wavenumber k_ny = {0}'.format(fg.k_nyq))
arr_const_c = np.zeros(shape=(fg.nx, fg.ny, fg.nz), dtype=np.float)
arr_const_c[:, :, :] = 1
arr_const_k = fg.calc_iFFT(arr_const_c)
print('  Compare (iFFT of unity)={0} vs (Lgrid*Ngrid)^3={1}'.format(arr_const_k[0, 0, 0], fg.Lgrid**3*fg.Ngrid**3))
```

    running test...
      Nyquist wavenumber k_ny = 0.40212385965949354
      Compare (iFFT of unity)=(1000000000+0j) vs (Lgrid*Ngrid)^3=1000000000.0

