#pragma once
#include <string>
#include <iostream>

class TV3D {
public:
    TV3D(const std::string& name);

    // Двери (open/close)
    void open_doors();
    void close_doors();
    bool are_doors_open() const;

    // 3D-эффект
    void enable_3d_effect();
    void disable_3d_effect();
    bool is_3d_enabled() const;

    // Игры
    void play_game(const std::string& game_name);

private:
    std::string name_;
    bool doors_open_;
    bool effect_3d_;
};
