#include "tv_mic.h"

TVMic::TVMic(const std::string& name) : name_(name), mic_on_(false) {}

void TVMic::turn_on() {
    mic_on_ = true;
    std::cout << name_ << " microphone turned ON!" << std::endl;
}

void TVMic::turn_off() {
    mic_on_ = false;
    std::cout << name_ << " microphone turned OFF!" << std::endl;
}

bool TVMic::is_on() const {
    return mic_on_;
}

int TVMic::get_volume_level() const {
    if(!mic_on_) return 0;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 100);
    return dis(gen);
}

void TVMic::record_audio(const std::string& filename) {
    if(mic_on_) {
        std::cout << "Recording audio to " << filename << " from " << name_ << std::endl;
    } else {
        std::cout << "Microphone is OFF! Cannot record audio." << std::endl;
    }
}
