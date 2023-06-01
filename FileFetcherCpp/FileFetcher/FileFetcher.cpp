#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_set>
#include <boost/filesystem.hpp>
#include <mutex>
#include <atomic>
#include <future>

namespace fs = boost::filesystem;

std::mutex outputMutex;
std::atomic<int> logFileCounter(0);

void processFile(const std::string& filePath, const std::string& keyword) {
    std::ifstream inputFile(filePath);

    if (!inputFile) {
        std::cerr << "Error opening input file: " << filePath << '\n';
        return;
    }

    std::string logFileName = "log" + std::to_string(++logFileCounter) + ".txt";
    std::ofstream logFile(logFileName, std::ios_base::app);

    if (!logFile) {
        std::cerr << "Error opening log file: " << logFileName << '\n';
        inputFile.close();
        return;
    }

    std::string line;
    while (std::getline(inputFile, line)) {
        if (!line.empty() && line.find(keyword) != std::string::npos) {
            std::lock_guard<std::mutex> lock(outputMutex);
            logFile << line << '\n';
        }
    }

    inputFile.close();
    logFile.close();
}

void combineLogFiles(const std::string& keyword) {
    std::ofstream outputFile(keyword + ".txt", std::ios_base::app);

    for (int i = 1; i <= logFileCounter; ++i) {
        std::string logFileName = "log" + std::to_string(i) + ".txt";
        std::ifstream logFile(logFileName);

        if (!logFile) {
            std::cerr << "Error opening log file: " << logFileName << '\n';
            continue;
        }

        std::string line;
        while (std::getline(logFile, line)) {
            std::lock_guard<std::mutex> lock(outputMutex);
            outputFile << line << '\n';
        }

        logFile.close();
        fs::remove(logFileName);
    }

    outputFile.close();
}

void removeDuplicatesParallel(const std::string& filePath) {
    std::ifstream inputFile(filePath);

    if (!inputFile) {
        std::cerr << "Error opening input file: " << filePath << '\n';
        return;
    }

    const std::size_t numThreads = std::thread::hardware_concurrency();
    std::vector<std::unordered_set<std::string>> partialLines(numThreads);

    std::string line;
    int threadId = 0;
    while (std::getline(inputFile, line)) {
        if (!line.empty()) {
            partialLines[threadId].insert(line);
            threadId = (threadId + 1) % partialLines.size();
        }
    }

    inputFile.close();

    std::unordered_set<std::string> uniqueLines;
    for (const auto& partialSet : partialLines) {
        uniqueLines.insert(partialSet.begin(), partialSet.end());
    }

    std::ofstream outputFile(filePath, std::ofstream::trunc);
    if (!outputFile) {
        std::cerr << "Error opening output file: " << filePath << '\n';
        return;
    }

    for (const auto& uniqueLine : uniqueLines) {
        outputFile << uniqueLine << '\n';
    }

    outputFile.close();
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: program_name keyword\n";
        return 0;
    }

    std::string keyword = argv[1];
    std::string outputFileName = keyword + ".txt";

    std::vector<std::thread> threads;

    fs::directory_iterator end;
    for (fs::directory_iterator file(fs::current_path()); file != end; ++file) {
        if (fs::is_regular_file(file->status()) && file->path().extension() == ".txt") {
            threads.emplace_back(std::thread(processFile, file->path().string(), keyword));
        }
    }

    for (auto& thread : threads) {
        thread.join();
    }

    combineLogFiles(keyword);

    removeDuplicatesParallel(outputFileName);

    std::cout << "Processing complete. Files have been combined into " << keyword << ".txt\n";

    return 0;
}
