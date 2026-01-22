#pragma once
#include <string>
#include <iostream>
#include <random>

class TVMic {
public:
    TVMic(const std::string& name);

    void turn_on();
    void turn_off();
    bool is_on() const;

    // Симуляция уровня звука (0-100)
    int get_volume_level() const;

    void record_audio(const std::string& filename);

private:
    std::string name_;
    bool mic_on_;
};
