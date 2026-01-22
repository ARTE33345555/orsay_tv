#include <pybind11/pybind11.h>
#include "tv_remote.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_remote, m) {
    py::class_<TVRemote>(m, "TVRemote")
        .def(py::init<const std::string&>())
        .def("power_on", &TVRemote::power_on)
        .def("power_off", &TVRemote::power_off)
        .def("is_on", &TVRemote::is_on)
        .def("volume_up", &TVRemote::volume_up)
        .def("volume_down", &TVRemote::volume_down)
        .def("get_volume", &TVRemote::get_volume)
        .def("change_channel", &TVRemote::change_channel)
        .def("get_channel", &TVRemote::get_channel)
        .def("move", &TVRemote::move)
        .def("scroll", &TVRemote::scroll)
        .def("press_button", &TVRemote::press_button);
}
