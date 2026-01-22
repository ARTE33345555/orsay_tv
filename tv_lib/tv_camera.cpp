#include "tv_camera.h"

TVCamera::TVCamera(const std::string& name) : name_(name), camera_on_(false) {}

void TVCamera::turn_on() {
    camera_on_ = true;
    std::cout << name_ << " camera turned ON!" << std::endl;
}

void TVCamera::turn_off() {
    camera_on_ = false;
    std::cout << name_ << " camera turned OFF!" << std::endl;
}

bool TVCamera::is_on() const {
    return camera_on_;
}

void TVCamera::take_photo(const std::string& filename) {
    if(camera_on_) {
        std::cout << "Photo taken: " << filename << " by " << name_ << std::endl;
    } else {
        std::cout << "Camera is OFF! Cannot take photo." << std::endl;
    }
}

void TVCamera::record_video(const std::string& filename) {
    if(camera_on_) {
        std::cout << "Recording video: " << filename << " by " << name_ << std::endl;
    } else {
        std::cout << "Camera is OFF! Cannot record video." << std::endl;
    }
}
