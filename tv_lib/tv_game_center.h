#pragma once
#include <string>
#include <vector>
#include <iostream>
#include "tv_remote.h"
#include "tv_3d.h"

class TVGameCenter {
public:
    TVGameCenter(const std::string& name);

    void add_game(const std::string& game_name);
    void list_games() const;
    void play_game(const std::string& game_name, TVRemote* remote, TV3D* tv3d = nullptr);

private:
    std::string name_;
    std::vector<std::string> games_;
};
