#include <pybind11/pybind11.h>
#include "tv_3d.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_3d, m) {
    py::class_<TV3D>(m, "TV3D")
        .def(py::init<const std::string&>())
        .def("open_doors", &TV3D::open_doors)
        .def("close_doors", &TV3D::close_doors)
        .def("are_doors_open", &TV3D::are_doors_open)
        .def("enable_3d_effect", &TV3D::enable_3d_effect)
        .def("disable_3d_effect", &TV3D::disable_3d_effect)
        .def("is_3d_enabled", &TV3D::is_3d_enabled)
        .def("play_game", &TV3D::play_game);
}
