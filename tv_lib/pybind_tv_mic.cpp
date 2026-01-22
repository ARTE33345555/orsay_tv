#include <pybind11/pybind11.h>
#include "tv_mic.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_mic, m) {
    py::class_<TVMic>(m, "TVMic")
        .def(py::init<const std::string&>())
        .def("turn_on", &TVMic::turn_on)
        .def("turn_off", &TVMic::turn_off)
        .def("is_on", &TVMic::is_on)
        .def("get_volume_level", &TVMic::get_volume_level)
        .def("record_audio", &TVMic::record_audio);
}
