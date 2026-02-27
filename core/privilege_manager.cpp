#include "privilege_manager.h"

void PrivilegeManager::registerSetting(const std::string& key, const std::string& value) {
    settings[key] = value;
}

void PrivilegeManager::updateSetting(const std::string& key, const std::string& value) {
    settings[key] = value;
}

std::string PrivilegeManager::getSetting(const std::string& key) {
    return settings[key];
}
