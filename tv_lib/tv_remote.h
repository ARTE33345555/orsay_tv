#pragma once
#include <string>
#include <iostream>
#include <stdexcept>

class TVRemote {
public:
    TVRemote(const std::string& name);

    // Включение/выключение (логика внутри программы)
    void power_on();
    void power_off();
    bool is_on() const;

    // Громкость
    void volume_up();
    void volume_down();
    int get_volume() const;

    // Каналы
    void change_channel(int channel);
    int get_channel() const;

    // Magic Remote функции
    void move(int x, int y);                     // движение пульта/курсора
    void scroll(int amount);                     // колёсико
    void press_button(const std::string& button); // кнопки, с ограничением

private:
    std::string name_;
    bool power_;
    int volume_;
    int channel_;
};
