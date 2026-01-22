#include "tv.h"
#include <iostream>

TV::TV(const std::string& name) : name_(name), is_on_(false) {}

void TV::turn_on() {
    is_on_ = true;
    std::cout << name_ << " turned on!" << std::endl;
}

void TV::turn_off() {
    is_on_ = false;
    std::cout << name_ << " turned off!" << std::endl;
}

std::string TV::get_status() const {
    return is_on_ ? "ON" : "OFF";
}
