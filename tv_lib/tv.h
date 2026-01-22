#pragma once
#include <string>

class TV {
public:
    TV(const std::string& name);
    void turn_on();
    void turn_off();
    std::string get_status() const;

private:
    std::string name_;
    bool is_on_;
};
