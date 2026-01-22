#include <pybind11/pybind11.h>
#include "tv.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_lib, m) {
    py::class_<TV>(m, "TV")
        .def(py::init<const std::string&>())
        .def("turn_on", &TV::turn_on)
        .def("turn_off", &TV::turn_off)
        .def("get_status", &TV::get_status);
}
