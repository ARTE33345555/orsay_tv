#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "iptv_engine.h"

namespace py = pybind11;

PYBIND11_MODULE(iptv_engine, m) {
    py::class_<Channel>(m, "Channel")
        .def_readonly("name", &Channel::name)
        .def_readonly("url", &Channel::url);

    py::class_<IPTVEngine>(m, "IPTVEngine")
        .def(py::init<>())
        .def("start", &IPTVEngine::start)
        .def("stop", &IPTVEngine::stop)
        .def("load_m3u", &IPTVEngine::loadM3U)
        .def("play_channel", &IPTVEngine::playChannel)
        .def("get_channels", &IPTVEngine::getChannels);
}
