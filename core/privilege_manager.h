#pragma once
#include <string>
#include <map>

class PrivilegeManager {
public:
    void registerSetting(const std::string& key, const std::string& value);
    void updateSetting(const std::string& key, const std::string& value);
    std::string getSetting(const std::string& key);

private:
    std::map<std::string, std::string> settings;
};
