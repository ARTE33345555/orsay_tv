#include <pybind11/pybind11.h>
#include "tv_camera.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_camera, m) {
    py::class_<TVCamera>(m, "TVCamera")
        .def(py::init<const std::string&>())
        .def("turn_on", &TVCamera::turn_on)
        .def("turn_off", &TVCamera::turn_off)
        .def("is_on", &TVCamera::is_on)
        .def("take_photo", &TVCamera::take_photo)
        .def("record_video", &TVCamera::record_video);
}
