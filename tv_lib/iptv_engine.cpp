#include "iptv_engine.h"
#include <iostream>
#include <sstream>
#include <curl/curl.h>

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* s) {
    size_t newLength = size * nmemb;
    s->append((char*)contents, newLength);
    return newLength;
}

IPTVEngine::IPTVEngine() : running(false) {}

void IPTVEngine::start() {
    running = true;
    std::cout << "[IPTV] Engine started\n";
}

void IPTVEngine::stop() {
    running = false;
    std::cout << "[IPTV] Engine stopped\n";
}

void IPTVEngine::loadM3U(const std::string& url) {
    CURL* curl = curl_easy_init();
    std::string buffer;

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
    curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    std::stringstream ss(buffer);
    std::string line;

    while (std::getline(ss, line)) {
        if (line.find("#EXTINF") != std::string::npos) {
            std::string name = line.substr(line.find(",") + 1);
            std::string streamUrl;
            std::getline(ss, streamUrl);
            channels.push_back({name, streamUrl});
        }
    }

    std::cout << "[IPTV] Loaded " << channels.size() << " channels\n";
}

void IPTVEngine::playChannel(int index) {
    if (!running || index >= channels.size()) return;

    std::cout << "[IPTV] Playing: " << channels[index].name << "\n";
    std::cout << "[IPTV] Stream URL: " << channels[index].url << "\n";
}

std::vector<Channel> IPTVEngine::getChannels() const {
    return channels;
}
