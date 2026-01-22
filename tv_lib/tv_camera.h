#pragma once
#include <string>
#include <iostream>

class TVCamera {
public:
    TVCamera(const std::string& name);

    void turn_on();
    void turn_off();
    bool is_on() const;

    void take_photo(const std::string& filename);
    void record_video(const std::string& filename);

private:
    std::string name_;
    bool camera_on_;
};
