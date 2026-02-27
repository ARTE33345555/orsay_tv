#pragma once
#include <string>
#include <vector>

struct Channel {
    std::string name;
    std::string url;
};

class IPTVEngine {
public:
    IPTVEngine();

    void start();
    void stop();

    void loadM3U(const std::string& url);
    void playChannel(int index);

    std::vector<Channel> getChannels() const;

private:
    std::vector<Channel> channels;
    bool running;
};
