# AUTOGENERATED! DO NOT EDIT! File to edit: field_on_grid.ipynb (unless otherwise specified).

__all__ = ['Field_on_grid', 'NTHREAD', 'EPS']

# Cell
import multiprocessing
import numpy as np
import time
import pyfftw

NTHREAD = multiprocessing.cpu_count()
EPS = 1.E-20


class Field_on_grid(object):
    r"""
    A class to handle a field on a 3-dimensional grid.

    FFT convention relies on scipy.fftpack.fftn
    For the convention, see:
      https://docs.scipy.org/doc/scipy-0.19.0/reference/generated/scipy.fftpack.fft.html

    Attributes
    ----------------
    Lbox_sim: array_like(shape=(3,))
              The box size which an user specifies.

    Ngrid: integer
           Number of grids along the axis with maximum length.

    do_cube: logical
             If True, set a FFT box with a uniform length.

    Lmax: float
          The maximum value of Lbox_sim.

    Lgrid: float
           Length size of each grid. Set as Lmax/Ngrid, i.e., same for all directions.

    Vgrid: float
           Volume size of each grid.

    k_nyq: float
           Nyquist wavenumber = pi/Lgrid

    k_smp: float
           Sampling wavenumber = 2*pi/Lgrid

    Lbox_fft: array_like(shape=(3,))
              The FFT box size which an user specifies. If do_cube is True, Lbox_fft[:] = Lmax.

    k_f: array_like(shape=(3,))
         fundamental frequency = 2*pi/Lbox_fft

    Vbox_sim: float
              Volume size of the original box.

    Vbox_fft: float
              Volume size of the FFT box.

    nx, ny, nz: integer
                number of grid along each axis.

    ix_c, iy_c, iz_c: numpy mgrid[nx, ny, nz]
                      index of grid in configuration space

    c_grid: numpy mgrid[nx, ny, nz]
    index of grid in configuration space

    ix_k, iy_k, iz_k: numpy mgrid[nx, ny, nz]
                      index of grid in Fourier space

    Methods
    ----------------
    set_muk_grid: set mu_k at a fixed LOS direction.

    calc_iFFT: inverse FFT operation (configuration to Fourier space)

    calc_FFT: FFT operation (Fourier to configuration space)

    """

    def __init__(self, Lbox, Ngrid, do_cube=True):
        r"""

        """
        # input parameters
        self.Lbox_sim = np.array(Lbox)
        self.Ngrid = Ngrid
        self.do_cube = do_cube

        # derived parameters
        self.Lmax = max(Lbox)
        # overall volume
        self.Vmax = self.Lmax**3
        # grid size is the same for all direction
        self.Lgrid = self.Lmax / self.Ngrid
        self.Vgrid = self.Lgrid**3
        # Nyquist wavenumber
        self.k_nyq = np.pi / self.Lgrid
        # box for FFT grid
        self.Lbox_fft = np.zeros(shape=(3,))
        if do_cube:
            self.Lbox_fft[:] = self.Lmax
        else:
            self.Lbox_fft[:] = self.Lbox_sim

        # fundamental wavenumber along x, y, z
        self.k_f = 2. * np.pi / self.Lbox_fft

        # derived parameters for FFT
        self.Vbox_sim = Lbox[0] * Lbox[1] * Lbox[2]  # simulation volume
        # FFT-grid box volume
        self.Vbox_fft = self.Lbox_fft[0] * self.Lbox_fft[1] * self.Lbox_fft[2]
        self.k_smp = 2. * self.k_nyq  # sampling wavenumber
        self.nx = int(np.ceil(self.Lbox_fft[0] / self.Lgrid))
        self.ny = int(np.ceil(self.Lbox_fft[1] / self.Lgrid))
        self.nz = int(np.ceil(self.Lbox_fft[2] / self.Lgrid))
        # number of grid positions
        self.Npos = self.nx * self.ny * self.nz
        self.d3r = self.Vbox_fft      # iFFT normalization.
        self.d3k = 1 / self.Vbox_fft  # FFT normalization

        # define the grid point (NOT a center!)
        self.ix_c, self.iy_c, self.iz_c = np.mgrid[0:self.nx,
                                                   0:self.ny,
                                                   0:self.nz]

        self.ix_k, self.iy_k, self.iz_k = np.mgrid[0:self.nx,
                                                   0:self.ny,
                                                   0:self.nz]
        # FFT d.o.f. due to periodicity
        _xn2 = self.nx // 2
        _yn2 = self.ny // 2
        _zn2 = self.nz // 2
        self.ix_k[_xn2:, :, :] -= self.nx
        self.iy_k[:, _yn2:, :] -= self.ny
        self.iz_k[:, :, _zn2:] -= self.nz

        self.k_grid = np.sqrt((self.k_f[0] * self.ix_k)**2. +
                              (self.k_f[1] * self.iy_k)**2. +
                              (self.k_f[2] * self.iz_k)**2.) + EPS

        self.nk_grid = np.sqrt((self.ix_k)**2. +
                               (self.iy_k)**2. +
                               (self.iz_k)**2.) + EPS

        self.c_grid = np.sqrt((self.Lgrid * self.ix_k)**2. +
                              (self.Lgrid * self.iy_k)**2. +
                              (self.Lgrid * self.iz_k)**2.) + EPS

        return

    def set_muk_grid(self, nhat=np.array([0, 0, 1])):
        r"""
        assign the value of mu_k = cos(nhat cdot veck) on the grid,
        given the line-of-sight direction, nhat.

        Parameters
        ----------
        nhat: array_like(shape=(3,))
              A line-of-sight vector can be a non-unit vector.

        Attribute
        ---------
        muk_grid: value of muk on each grid point.

        kpara_grid: value of k_parallel on each grid point.
        """

        # normalize the direction vector
        norm = np.linalg.norm(nhat)

        # first calculate mu array
        self.nhat = nhat / norm

        self.kpara_grid = (self.k_f[0] * self.ix_k) * self.nhat[0] + (self.k_f[1] * self.iy_k) * self.nhat[1] + (self.k_f[2] * self.iz_k) * self.nhat[2]

        self.muk_grid = self.kpara_grid/np.abs(self.k_grid)

        self.absmuk_grid = np.abs(self.muk_grid)

        return

    def calc_iFFT(self, arr_grid_c, num_thread=NTHREAD):
        r"""
        compute the inverse FFT of a pre-computed field on the 3D grid
        to obtain a field on the 3D Fourier grid.

        Parameters
        ----------
        arr_grid_c: array_like
                    A precomputed field on the 3D grid in configuration space.

        num_thread: int (OPTIONAL)
                    Number of threads.

        Return
        ------
        arr_grid_k: array_like
                    A target field on the 3D grid in Fourier space.
        """
        _arr_tmp = arr_grid_c.copy()
        arr_grid_k = pyfftw.interfaces.scipy_fftpack.ifftn(_arr_tmp, overwrite_x=True,
                                                           threads=num_thread)*self.d3r
        return arr_grid_k

    def calc_FFT(self, arr_grid_k, num_thread=NTHREAD):
        r"""
        compute the FFT of a pre-computed field on the 3D Fourier grid
        to obtain a field on the 3D configuration grid.

        Parameters
        ----------
        arr_grid_k: array_like
                    A precomputed field on the 3D grid in Fourier space.

        num_thread: int (OPTIONAL)
                    Number of threads.

        Return
        ------
        arr_grid_c: array_like
                    A target field on the 3D grid in configuration space.
        """
        _arr_tmp = arr_grid_k.copy()
        arr_grid_c = pyfftw.interfaces.scipy_fftpack.fftn(_arr_tmp, overwrite_x=True,
                                                          threads=num_thread)*self.d3k
        return arr_grid_c