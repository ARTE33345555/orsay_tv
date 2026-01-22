#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "tv_game_center.h"
#include "tv_remote.h"
#include "tv_3d.h"

namespace py = pybind11;

PYBIND11_MODULE(tv_game_center, m) {
    py::class_<TVGameCenter>(m, "TVGameCenter")
        .def(py::init<const std::string&>())
        .def("add_game", &TVGameCenter::add_game)
        .def("list_games", &TVGameCenter::list_games)
        .def("play_game", &TVGameCenter::play_game, py::arg("game_name"), py::arg("remote"), py::arg("tv3d") = nullptr);
}
