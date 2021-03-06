from .pfsSimpleSpectrum import PfsSimpleSpectrum
from .utils import wraparoundNVisit, inheritDocstrings
from .fluxTable import FluxTable
from .observations import Observations


@inheritDocstrings
class PfsFiberArray(PfsSimpleSpectrum):
    """Spectrum arrays for a single object

    This base class is suitable for spectra which have been extracted from
    observations.

    Parameters
    ----------
    target : `pfs.datamodel.Target`
        Target information.
    observations : `pfs.datamodel.Observations`
        Observations of the target.
    wavelength : `numpy.ndarray` of `float`
        Array of wavelengths.
    flux : `numpy.ndarray` of `float`
        Array of fluxes.
    mask : `numpy.ndarray` of `int`
        Array of mask pixels.
    sky : `numpy.ndarray` of `float`
        Array of sky values.
    covar : `numpy.ndarray` of `float`
        Near-diagonal (diagonal and either side) part of the covariance matrix.
    covar2 : `numpy.ndarray` of `float`
        Low-resolution non-sparse covariance estimate.
    flags : `MaskHelper`
        Helper for dealing with symbolic names for mask values.
    metadata : `dict` (`str`: POD), optional
        Keyword-value pairs for the header.
    fluxTable : `pfs.datamodel.FluxTable`, optional
        Table of fluxes from contributing observations.
    """
    filenameFormat = None  # Subclasses should override

    def __init__(self, target, observations, wavelength, flux, mask, sky, covar, covar2, flags, metadata=None,
                 fluxTable=None):
        self.observations = observations
        self.sky = sky
        self.covar = covar
        self.covar2 = covar2
        self.nVisit = wraparoundNVisit(len(self.observations))
        self.fluxTable = fluxTable
        super().__init__(target, wavelength, flux, mask, flags, metadata=metadata)

    @property
    def variance(self):
        """Variance in the flux"""
        return self.covar[0]

    def getIdentity(self):
        """Return the identity of the spectrum

        Returns
        -------
        identity : `dict`
            Key-value pairs that identify this spectrum.
        """
        identity = super().getIdentity().copy()
        identity.update(self.observations.getIdentity())
        return identity

    def validate(self):
        """Validate that all the arrays are of the expected shape"""
        self.observations.validate()
        assert wraparoundNVisit(len(self.observations)) == self.nVisit
        assert self.sky.shape == (self.length,)
        assert self.covar.shape == (3, self.length)
        assert self.covar2.ndim == 2

    def __imul__(self, rhs):
        """Flux multiplication, in-place"""
        super().__imul__(rhs)
        for ii in range(3):
            self.covar[ii] *= rhs**2
        return self

    def __itruediv__(self, rhs):
        """Flux division, in-place"""
        super().__itruediv__(rhs)
        for ii in range(3):
            self.covar[ii] /= rhs**2
        return self

    @classmethod
    def _readImpl(cls, fits):
        """Implementation for reading from FITS file

        Parameters
        ----------
        fits : `astropy.io.fits.HDUList`
            Opened FITS file.

        Returns
        -------
        kwargs : ``dict``
            Keyword arguments for constructing spectrum.
        """
        data = super()._readImpl(fits)
        data["sky"] = fits["SKY"].data
        data["observations"] = Observations.fromFits(fits)
        data["covar"] = fits["COVAR"].data
        data["covar2"] = fits["COVAR2"].data
        try:
            fluxTable = FluxTable.fromFits(fits)
        except KeyError as exc:
            # Only want to catch "Extension XXX not found."
            if not exc.args[0].startswith("Extension"):
                raise
            fluxTable = None
        data["fluxTable"] = fluxTable
        return data

    def _writeImpl(self, fits):
        """Implementation for writing to FITS file

        Parameters
        ----------
        fits : `astropy.io.fits.HDUList`
            List of FITS HDUs. This has a Primary HDU already, the header of
            which may be supplemented with additional keywords.
        """
        from astropy.io.fits import ImageHDU
        header = super()._writeImpl(fits)
        fits.append(ImageHDU(self.sky, header=header, name="SKY"))
        fits.append(ImageHDU(self.covar, header=header, name="COVAR"))
        fits.append(ImageHDU(self.covar2, name="COVAR2"))
        self.observations.toFits(fits)
        if self.fluxTable is not None:
            self.fluxTable.toFits(fits)
