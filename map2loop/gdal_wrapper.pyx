from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from cpython.bytes cimport PyBytes_AsString, PyBytes_Size

cdef extern from "gdal.h":
    ctypedef void* GDALDatasetH
    ctypedef void* GDALDriverH
    ctypedef void* CPLErr

    GDALDatasetH GDALOpen(const char *filename, int access)
    void GDALTranslate(const char *dest, GDALDatasetH srcDataset, void *options)
    GDALDatasetH GDALWarp(const char *dest, GDALDatasetH srcDataset, void *options)
    GDALDriverH GDALGetDriverByName(const char *name)
    void GDALUseExceptions()
    int GDALInvGeoTransform(double *gt_in, double *gt_out)
    void *GDALFileFromMemBuffer(const char *filename, void *buffer, int buffer_size)

# Python-friendly wrapper for GDAL Translate
def gdal_translate(str dest, srcDataset, options=None):
    """
    Wrapper around GDALTranslate function.
    Args:
        dest (str): Destination file path.
        srcDataset: Source dataset handle (GDALDatasetH).
        options: GDAL translation options (None by default).
    """
    cdef const char *c_dest
    temp_dest = dest.encode('utf-8')  # Store in a Python object first
    c_dest = temp_dest  # Assign the safe reference
    GDALTranslate(c_dest, <GDALDatasetH>srcDataset, <void*>options)

# Python-friendly wrapper for GDAL Warp
def gdal_warp(str dest, srcDataset, options=None):
    """
    Wrapper around GDALWarp function.
    Args:
        dest (str): Destination file path.
        srcDataset: Source dataset handle (GDALDatasetH).
        options: GDAL warp options (None by default).
    Returns:
        GDALDatasetH: Handle to the warped dataset.
    """
    cdef const char *c_dest
    temp_dest = dest.encode('utf-8')  # Store in a Python object first
    c_dest = temp_dest  # Assign the safe reference
    return <object>GDALWarp(c_dest, <GDALDatasetH>srcDataset, <void*>options)

# Wrapper for GDALGetDriverByName
def gdal_get_driver_by_name(str name):
    """
    Wrapper around GDALGetDriverByName function.
    Args:
        name (str): The driver name (e.g., 'GTiff').
    Returns:
        GDALDriverH: Handle to the GDAL driver.
    """
    cdef const char *c_name
    temp_name = name.encode('utf-8')  # Store in a Python object first
    c_name = temp_name  # Assign the safe reference
    return <object>GDALGetDriverByName(c_name)

# Wrapper for GDALUseExceptions
def gdal_use_exceptions():
    """
    Wrapper around GDALUseExceptions function.
    Enables the use of exceptions for GDAL errors.
    """
    GDALUseExceptions()

# Wrapper for GDALFileFromMemBuffer
def gdal_file_from_mem_buffer(str filename, bytes buffer):
    """
    Wrapper around GDALFileFromMemBuffer function.
    Args:
        filename (str): The name of the in-memory file.
        buffer (bytes): The in-memory buffer content.
    Returns:
        Pointer to the file in memory.
    """
    cdef const char *c_filename
    temp_filename = filename.encode('utf-8')  # Store in a Python object first
    c_filename = temp_filename  # Assign the safe reference

    cdef int buffer_size = PyBytes_Size(buffer)
    cdef void *c_buffer = malloc(buffer_size)
    
    if not c_buffer:
        raise MemoryError("Failed to allocate memory for the buffer")

    # Copy the content from the Python bytes object to the allocated C buffer
    memcpy(c_buffer, PyBytes_AsString(buffer), buffer_size)
    
    cdef void *mem_file = GDALFileFromMemBuffer(c_filename, c_buffer, buffer_size)
    
    # Free the allocated C buffer
    free(c_buffer)

    # Return the memory file handle as an object (adjust if you need a specific object type)
    return <object>mem_file

# Wrapper for GDALInvGeoTransform
def gdal_inv_geo_transform(gt_in):
    """
    Wrapper around GDALInvGeoTransform function.
    Args:
        gt_in (list): Input geotransform (list of 6 elements).
    Returns:
        list: Inverted geotransform (list of 6 elements).
    """
    cdef double gt_out[6]
    cdef double gt_in_c[6]

    # Copy the input list into the C array
    for i in range(6):
        gt_in_c[i] = gt_in[i]

    # Call the GDALInvGeoTransform function
    if GDALInvGeoTransform(gt_in_c, gt_out):
        raise RuntimeError("Geotransform inversion failed")

    # Return the inverted geotransform as a Python list
    return [gt_out[i] for i in range(6)]
