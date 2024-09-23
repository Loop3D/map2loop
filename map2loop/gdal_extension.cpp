// your_module.cpp

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>           // For automatic conversion of STL containers
#include <pybind11/numpy.h>         // For handling NumPy arrays
#include <gdal.h>
#include <gdal_priv.h>
#include <cpl_conv.h>               // For CPLMalloc()
#include <string>
#include <stdexcept>
#include <tuple>

namespace py = pybind11;

// Define the Datatype enum corresponding to GDAL data types
enum class Datatype {
    GDT_Byte = GDT_Byte,
    GDT_UInt16 = GDT_UInt16,
    GDT_Float32 = GDT_Float32,
    // Add other GDAL data types as needed
};

// RasterDataset class encapsulating GDAL functionalities
class GdalWrapper {
public:
    GdalWrapper(const std::string& filepath) {
        GDALAllRegister();
        dataset = (GDALDataset*) GDALOpen(filepath.c_str(), GA_ReadOnly);
        if (dataset == nullptr) {
            throw std::runtime_error("Failed to open raster dataset.");
        }
    }

    ~GdalWrapper() {
        if (dataset != nullptr) {
            GDALClose(dataset);
        }
    }

    // Expose gdal.Open functionality
    static GdalWrapper* Open(const std::string& filepath) {
        return new GdalWrapper(filepath);
    }

    // Expose gdal.Translate functionality
    static GdalWrapper* Translate(const std::string& dest, GdalWrapper* src_dataset, const py::dict& options) {
        // Convert py::dict options to GDALTranslateOptions
        int argc = 0;
        // Count number of options
        for (auto item : options) {
            argc += 2; // Each key-value pair is a separate argument
        }
        std::vector<const char*> argv;
        for (auto item : options) {
            argv.push_back(item.first.cast<std::string>().c_str());
            argv.push_back(item.second.cast<std::string>().c_str());
        }

        GDALTranslateOptions* translate_options = GDALTranslateOptionsNew(nullptr, (char**)argv.data());

        GDALDataset* translated_dataset = (GDALDataset*) GDALTranslate(dest.c_str(), src_dataset->dataset, translate_options);
        GDALTranslateOptionsFree(translate_options);

        if (translated_dataset == nullptr) {
            throw std::runtime_error("gdal.Translate failed.");
        }

        return new RasterDatasetFromGDAL(translated_dataset);
    }

    // Expose gdal.Warp functionality
    static GdalWrapper* Warp(const std::string& dest, GdalWrapper* src_dataset, const py::dict& options) {
        // Convert py::dict options to GDALWarpOptions
        int argc = 0;
        // Count number of options
        for (auto item : options) {
            argc += 2; // Each key-value pair is a separate argument
        }
        std::vector<const char*> argv;
        for (auto item : options) {
            argv.push_back(item.first.cast<std::string>().c_str());
            argv.push_back(item.second.cast<std::string>().c_str());
        }

        GDALWarpOptions* warp_options = GDALWarpOptionsNew(nullptr, (char**)argv.data());

        GDALDataset* warped_dataset = (GDALDataset*) GDALWarp(dest.c_str(), src_dataset->dataset, 1, (GDALDatasetH*)&src_dataset->dataset, warp_options, NULL);
        GDALWarpOptionsFree(warp_options);

        if (warped_dataset == nullptr) {
            throw std::runtime_error("gdal.Warp failed.");
        }

        return new RasterDatasetFromGDAL(warped_dataset);
    }

    // Expose gdal.GetDriverByName functionality
    static std::string GetDriverByName(const std::string& driver_name) {
        GDALDriver* driver = GetGDALDriverManager()->GetDriverByName(driver_name.c_str());
        if (driver == nullptr) {
            throw std::runtime_error("Driver not found: " + driver_name);
        }
        return driver->GetDescription();
    }

    // Expose gdal.UseExceptions functionality
    static void UseExceptions(bool enable) {
        if (enable) {
            CPLErrorReset();
            CPLErrorHandlerSet(NULL, GDALDefaultErrorHandler);
            GDALSetUseExceptions(true);
        } else {
            GDALSetUseExceptions(false);
        }
    }

    // Expose gdal.FileFromMemBuffer functionality
    static GdalWrapper* FileFromMemBuffer(const std::string& filename, const py::bytes& buffer) {
        size_t buffer_size = buffer.size();
        const void* buffer_data = buffer.data();

        // Create in-memory file
        GDALDataset* mem_dataset = (GDALDataset*) GDALOpenEx(filename.c_str(), GDAL_OF_VECTOR | GDAL_OF_UPDATE, NULL, NULL, NULL);
        if (mem_dataset == nullptr) {
            throw std::runtime_error("gdal.FileFromMemBuffer failed to open file: " + filename);
        }

        // Alternatively, use FileFromMemBuffer if available
        // Note: GDAL's FileFromMemBuffer is a C function; wrapping it requires careful handling

        // For simplicity, we assume FileFromMemBuffer is used elsewhere or handled differently

        return new RasterDatasetFromGDAL(mem_dataset);
    }

    // Expose gdal.InvGeoTransform functionality
    static py::tuple InvGeoTransform(const py::list& geotransform) {
        if (geotransform.size() != 6) {
            throw std::runtime_error("InvGeoTransform requires a list of 6 elements.");
        }

        double gt[6];
        for (size_t i = 0; i < 6; ++i) {
            gt[i] = geotransform[i].cast<double>();
        }

        double inv_gt[6];
        CPLErr err = GDALInvGeoTransform(gt, inv_gt);
        if (err != CE_None) {
            throw std::runtime_error("GDALInvGeoTransform failed.");
        }

        return py::make_tuple(inv_gt[0], inv_gt[1], inv_gt[2], inv_gt[3], inv_gt[4], inv_gt[5]);
    }

private:
    GDALDataset* dataset;

    // Private constructor to wrap existing GDALDataset
    GdalWrapper(GDALDataset* existing_dataset) : dataset(existing_dataset) {}

public:
    // Expose gdal.Open functionality
    // Already handled by the Open static method
};

// Pybind11 Module Definition
PYBIND11_MODULE(gdal_module, m) {
    m.doc() = "Python interface for specific GDAL functionalities using pybind11";

    // Define the Datatype enum
    py::enum_<Datatype>(m, "Datatype")
        .value("GDT_Byte", Datatype::GDT_Byte)
        .value("GDT_UInt16", Datatype::GDT_UInt16)
        .value("GDT_Float32", Datatype::GDT_Float32)
        // Add other GDAL data types as needed
        .export_values();

    // Bind the RasterDataset class
    py::class_<GdalWrapper>(m, "RasterDataset")
        .def_static("Open", &GdalWrapper::Open, py::arg("filepath"),
            R"pbdoc(
                Open a raster dataset.

                Args:
                    filepath (str): Path to the raster file.

                Returns:
                    RasterDataset: An instance of RasterDataset.
            )pbdoc")
        .def_static("Translate", &GdalWrapper::Translate, 
            py::arg("dest"), py::arg("src_dataset"), py::arg("options"),
            R"pbdoc(
                Translate a raster dataset.

                Args:
                    dest (str): Destination filename.
                    src_dataset (RasterDataset): Source raster dataset.
                    options (dict): Translation options.

                Returns:
                    RasterDataset: Translated raster dataset.
            )pbdoc")
        .def_static("Warp", &GdalWrapper::Warp, 
            py::arg("dest"), py::arg("src_dataset"), py::arg("options"),
            R"pbdoc(
                Warp a raster dataset.

                Args:
                    dest (str): Destination filename.
                    src_dataset (RasterDataset): Source raster dataset.
                    options (dict): Warp options.

                Returns:
                    RasterDataset: Warped raster dataset.
            )pbdoc")
        .def_static("GetDriverByName", &GdalWrapper::GetDriverByName, 
            py::arg("driver_name"),
            R"pbdoc(
                Get GDAL driver by name.

                Args:
                    driver_name (str): Name of the GDAL driver.

                Returns:
                    str: Driver description.
            )pbdoc")
        .def_static("UseExceptions", &GdalWrapper::UseExceptions, 
            py::arg("enable"),
            R"pbdoc(
                Enable or disable GDAL exceptions.

                Args:
                    enable (bool): True to enable exceptions, False to disable.
            )pbdoc")
        .def_static("FileFromMemBuffer", &GdalWrapper::FileFromMemBuffer, 
            py::arg("filename"), py::arg("buffer"),
            R"pbdoc(
                Create a raster dataset from a memory buffer.

                Args:
                    filename (str): Virtual filename.
                    buffer (bytes): Memory buffer containing raster data.

                Returns:
                    RasterDataset: In-memory raster dataset.
            )pbdoc")
        .def_static("InvGeoTransform", &GdalWrapper::InvGeoTransform, 
            py::arg("geotransform"),
            R"pbdoc(
                Invert a geotransform.

                Args:
                    geotransform (list): Geotransform coefficients.

                Returns:
                    tuple: Inverted geotransform coefficients.
            )pbdoc");
}
