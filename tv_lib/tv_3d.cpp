#include "tv_3d.h"

TV3D::TV3D(const std::string& name) : name_(name), doors_open_(false), effect_3d_(false) {}

void TV3D::open_doors() {
    doors_open_ = true;
    std::cout << name_ << " doors opened!" << std::endl;
}

void TV3D::close_doors() {
    doors_open_ = false;
    std::cout << name_ << " doors closed!" << std::endl;
}

bool TV3D::are_doors_open() const {
    return doors_open_;
}

void TV3D::enable_3d_effect() {
    effect_3d_ = true;
    std::cout << name_ << " 3D effect enabled!" << std::endl;
}

void TV3D::disable_3d_effect() {
    effect_3d_ = false;
    std::cout << name_ << " 3D effect disabled!" << std::endl;
}

bool TV3D::is_3d_enabled() const {
    return effect_3d_;
}

void TV3D::play_game(const std::string& game_name) {
    if(effect_3d_) {
        std::cout << "Playing 3D game: " << game_name << " on " << name_ << std::endl;
    } else {
        std::cout << "Enable 3D effect first to play 3D games!" << std::endl;
    }
}
