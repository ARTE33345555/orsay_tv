#include "tv_remote.h"

TVRemote::TVRemote(const std::string& name)
    : name_(name), power_(false), volume_(10), channel_(1) {}

void TVRemote::power_on() {
    power_ = true;
    std::cout << name_ << " TV powered ON!" << std::endl;
}

void TVRemote::power_off() {
    power_ = false;
    std::cout << name_ << " TV powered OFF!" << std::endl;
}

bool TVRemote::is_on() const {
    return power_;
}

void TVRemote::volume_up() {
    if(power_) {
        volume_++;
        std::cout << "Volume: " << volume_ << std::endl;
    }
}

void TVRemote::volume_down() {
    if(power_ && volume_ > 0) {
        volume_--;
        std::cout << "Volume: " << volume_ << std::endl;
    }
}

int TVRemote::get_volume() const {
    return volume_;
}

void TVRemote::change_channel(int channel) {
    if(power_) {
        channel_ = channel;
        std::cout << "Channel changed to: " << channel_ << std::endl;
    }
}

int TVRemote::get_channel() const {
    return channel_;
}

// --- Magic Remote функции ---
void TVRemote::move(int x, int y) {
    std::cout << name_ << " moved to (" << x << ", " << y << ")" << std::endl;
}

void TVRemote::scroll(int amount) {
    std::cout << name_ << " scrolled by " << amount << std::endl;
}

void TVRemote::press_button(const std::string& button) {
    if(button == "power" || button == "home") {
        throw std::runtime_error("Error: This button cannot be used!");
    } else {
        std::cout << name_ << " pressed button: " << button << std::endl;
    }
}
