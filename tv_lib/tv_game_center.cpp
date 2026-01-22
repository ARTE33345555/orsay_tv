#include "tv_game_center.h"

TVGameCenter::TVGameCenter(const std::string& name) : name_(name) {}

void TVGameCenter::add_game(const std::string& game_name) {
    games_.push_back(game_name);
    std::cout << "Game added: " << game_name << std::endl;
}

void TVGameCenter::list_games() const {
    std::cout << "Available games in " << name_ << ":" << std::endl;
    for(const auto& game : games_) {
        std::cout << "- " << game << std::endl;
    }
}

void TVGameCenter::play_game(const std::string& game_name, TVRemote* remote, TV3D* tv3d) {
    if(!remote->is_on()) {
        std::cout << "TV is OFF! Cannot play any game." << std::endl;
        return;
    }

    bool found = false;
    for(const auto& game : games_) {
        if(game == game_name) found = true;
    }
    if(!found) {
        std::cout << "Game not found: " << game_name << std::endl;
        return;
    }

    if(tv3d && tv3d->is_3d_enabled()) {
        std::cout << "Playing 3D game: " << game_name << " on " << name_ << std::endl;
    } else {
        std::cout << "Playing 2D game: " << game_name << " on " << name_ << std::endl;
    }
}
